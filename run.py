import psycopg2
import json
from paths import Path, evil
from features.question_features import QuestionFeatures
import os

from log_config.log_config import logger
from flask import Flask, jsonify, request

from pool import POOL

app = Flask(__name__)

def send_to_database(

    cur, conn, res: Path, survey_version_id: str, survey_session_chunk_id: str, question_features: QuestionFeatures#, first_movement_delay
):
    # Combine question features and path features
    features = question_features.question_features
    features.update(res.features)
    #features['question_features']['first_movement_delay'] = first_movement_delay
    features_string = json.dumps(features)

    res.question.stimulus = res.question.stimulus.replace("'", "''")
    res.response = res.response.replace("'", "''")

    values = f"({survey_version_id}, {survey_session_chunk_id}, '{res.participant}', '{res.question.type}', '{res.question.stimulus}', '{res.response}', '{features_string}')"
    #cur.execute(
    #    f"""
    #    INSERT INTO results (survey_version_id, survey_session_chunk_id, participant, question_type, question_stimulus, response, features)
    #    VALUES
    #    {values}
    #    ON CONFLICT (survey_session_chunk_id)
    #    DO UPDATE
    #    SET features=EXCLUDED.features
    #    """
    #)
    cur.execute(
        """
        INSERT INTO results (
            survey_version_id,
            survey_session_chunk_id,
            participant,
            question_type,
            question_stimulus,
            response,
            features,
            qlabel
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            survey_version_id,
            survey_session_chunk_id,
            res.participant,
            res.question.type,
            res.question.stimulus,
            res.response,
            features_string,
            res.qlabel
        )
    )
    #ON
    #CONFLICT(survey_session_chunk_id)
    #DO
    #UPDATE
    #SET
    #features = EXCLUDED.features
    conn.commit()
    print(f'survey version id = {survey_version_id}')

    #REQUEST_PROCESS_URL = f'http://127.0.0.1:8000/{survey_version_id}'
    #import requests
    #print(f'request send for {survey_version_id}')

    #requests.get(
    #    REQUEST_PROCESS_URL,
    #)

    print('ever')
    return values

GET_FIRST_MOVEMENT_DELAY_SQL = """
SELECT
    MIN(a.time) AS first_movement_delay
FROM survey_session_chunk ssc
JOIN activity a ON a.survey_session_chunk_id = ssc.id
JOIN element_of_interest eoi ON eoi.survey_session_chunk_id = ssc.id
WHERE a.name = 'mousemove' and ssc.id = {chunk_id}  and eoi.label = '{qlabel}'
GROUP BY ssc.id, ssc.client_load_complete, eoi.label
ORDER BY first_movement_delay ASC
LIMIT 10;
"""

def read_from_database(cur, per, survey_session_chunk_id):

    # # Get the set of questions they completed.
    cur.execute(
        f"""select id, client_load_start, client_submit, window_size_desc, 
        window_width, window_height, container_left, container_top, was_resized, survey_session_id
        from survey_session_chunk 
        where id = '{survey_session_chunk_id}' order by client_load_start"""
    )
    survey_version_id = None
    survey_sess_chunk = cur.fetchone()

    try:
        cur.execute(
            "select survey_version_id, time_started, language, user_agent from survey_session where id = '"
            + survey_sess_chunk[9]
            + "'"
        )

    except TypeError as e:
        logger.error(f"Error in read from survey_session DB: {e}", exc_info=True)
        logger.debug(f"Session Chunk Diagnostics \t {survey_sess_chunk[9]} \t {survey_sess_chunk}")

    survey_sess = cur.fetchone()

    survey_version_id = survey_sess[0]
    # Get the answers to the questions.
    per.execute(
        "select qlabel, question_text, answer_text, answer_value "
        + "from answer where survey_session_chunk_id = "
        + str(survey_sess_chunk[0])
    )

    #ans = per.fetchone()
    answers = per.fetchall()

    if not answers:
        return None, survey_version_id
    rec_list = []
    for ans in answers:

        qtype = "bipartite_choice"
        if "bipartite" not in ans[0]:
            if "tripartite" in ans[0]:
                qtype = "tripartite_choice"
            else:
                qtype = "non_instrumented"

        rec = {
            "id": survey_sess_chunk[9],
            "questionStartTime": survey_sess_chunk[1],
            "questionEndTime": survey_sess_chunk[2],
            "deviceMQ": survey_sess_chunk[3],
            "innerWidth": survey_sess_chunk[4],
            "innerHeight": survey_sess_chunk[5],
            "containerLeft": survey_sess_chunk[6],
            "containerTop": survey_sess_chunk[7],
            "mqChanged": survey_sess_chunk[8],
            "questionID": survey_sess_chunk[0],
            "questionType": qtype,
            'qlabel': ans[0],
            "stimulus": ans[1],
            "response": ans[2],
            "surveyStartTime": survey_sess[1],
            "browserLanguage": survey_sess[2],
            "browserUserAgent": survey_sess[3],
            "surveyID": survey_sess[0],
        }

        rec["options"] = []
        rec["midpoints"] = []
        rec["mousePath"] = []
        rec["mousePaths"] = [] # Note - mousePath, but nested for multiple movements

    # Get the positions of elements on the screen
        if qtype in ["bipartite_choice", "tripartite_choice"]:

        # Get the behavioural data we need for analysis
            per.execute(
                "select title, center_x, center_y, width, height "
                + "from element_of_interest "
                + "where survey_session_chunk_id = "
                + str(survey_sess_chunk[0])
                + " "
                + "and element_type = 'option' and visible = true "
                + "order by center_x ASC, center_y ASC"
            )

            for i in per.fetchall():
                rec["options"].append(i[0])
                rec["midpoints"].append((i[1], i[2], i[3], i[4]))

        # Get the mouse path coordinates
            per.execute(
                "select name, time, x, y from activity "
                + "where survey_session_chunk_id = '"
                + str(survey_sess_chunk[0])
                + "'"
                + "order by time"
            )
            tmp = []
            up = 0
            for i in per.fetchall():
                if i[0] in ["mouseup", "touchend"]:
                    up += 1
                tmp.append((i[0], i[1], i[2], i[3]))

            rec["changedMind"] = up - 1

        # Note: I keep separate movements in separate sub-arrays
        # incase we want to process them separately in future developments
            movement = []
            for action in tmp:
                rec["mousePath"].append((action[1], action[2], action[3]))

            # Keep multiple movements separate in "mousePaths" -> currently unused
                movement.append((action[1], action[2], action[3]))
                if action[0] in ["mouseup", "touchend"]:
                    rec["mousePaths"].append(movement)
                    movement = []


        # Sanity check that the last mouse coordinate is inside the
        # coordinates of the option with the text that matches the
        # response submitted.

        ## TODO Needs more explaination of utlity
        #"Если пользователь ответил "Very satisfied" и у этой опции был center_x = 0.5, width = 0.2, height = 0.1, то последняя мышиная координата должна быть внутри этой области. Иначе — что-то пошло не так (возможно, bot/spam/fake)."

        ##count = 0
        ##box = (0, 0, 0, 0)
        ##for i in rec["options"]:
        ##    if i == rec["response"]:
         ##       box = rec["midpoints"][count]
        ##        break
        ##    count += 1
        ##if count == len(rec["options"]):
        ##    logger.debug(f"Sanity Check Failed \t {survey_session_chunk_id} \t {rec['response']} \t {rec['options']}")
        ##    return None, None
        rec_list.append(rec)


    #return rec, survey_version_id
    return rec_list, survey_version_id


def get_first_movement_delay(cur, survey_session_chunk_id, qlabel):
    cur.execute(
        GET_FIRST_MOVEMENT_DELAY_SQL.format(chunk_id=survey_session_chunk_id, qlabel=qlabel)
    )
    return cur.fetchone()[0]



@app.route('/', methods=['POST'])
def lambda_handler():
    # get from request survey_session_chunk_id
    body = request.data 
    survey_session_chunk_id = json.loads(body).get(  # survey_session_chunk_id=chunk.id
        "survey_session_chunk_id"
    )
    if not survey_session_chunk_id:
        return jsonify({"statusCode": 200, "body": json.dumps("No chunk id found!")})
    try:

        conn = POOL.getconn()

    #conn = psycopg2.connect(
    #    host=os.environ.get("POSTGRES_HOST"),
    #    #dbname="postgres",
    #    dbname='decipher',
    #    user=os.environ.get("POSTGRES_USERNAME"),
    ##    password=os.environ.get("POSTGRES_PASSWORD"),
    #)
        with conn:

            with conn.cursor() as cur, conn.cursor() as per:
                questions, survey_version_id = read_from_database(cur, per, survey_session_chunk_id)
    #cur.close()
    #per.close()
            print(questions)

            for question in questions:
                if question:
                    result = Path(question)
                    question_feats = QuestionFeatures(question["stimulus"])
                    if not evil.is_evil(result):
                #other_cur = conn.cursor()
                #first_movement_delay = get_first_movement_delay(cur=other_cur,
                                                                #survey_session_chunk_id=survey_session_chunk_id,
                                                                #qlabel=question['qlabel'])
                        with conn.cursor() as cur:
                            send_to_database(
                        cur, conn, result, survey_version_id, survey_session_chunk_id, question_feats#, first_movement_delay
                            )
            #cur.close()
       
        #else:
        #    logger.debug(f'Send to DB skipped, due to failed sanity check\t{question}\t{survey_version_id}')

    #cur.close()
        return jsonify({"statusCode": 200, "body": "ok"}), 200
    except Exception as err:
        print(err)
        return jsonify({'status': 500, 'body': str(err)})
    finally:
        if conn:
            print('opa')
            POOL.putconn(conn)



if __name__ == '__main__':
    app.run(debug=True, port=5003)
