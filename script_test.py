from typing import List

import requests
import random
import time
from faker import Faker
import uuid
fake = Faker()

BASE_URL = "http://localhost:5003"


def get_data() -> List:
    with open('id_survey_session_chunk.csv', 'r') as f:
        return f.read().split('\n')


def post_to_ffml_preprocess(survey_session_chunk_id: str):
    payload = {
        "survey_session_chunk_id": survey_session_chunk_id
    }

    response = requests.post(f"{BASE_URL}/", json=payload)
    print("\n🔹 POST / to ffml-preprocess-main")
    print(f"Payload: {payload}")
    print("Status code:", response.status_code)
    try:
        print("Response:", response.json())
    except Exception:
        print("Response:", response.text)

if __name__ == "__main__":
    print("🚀 Отправляем тест в ffml-preprocess-main...") # 4451
    #with open('iddddd.csv', 'r') as f:
    #    data = f.read().split('\n')
    #print(data)
    #example_chunk_ids = get_data()
    example_chunk_ids = ['sawdda6uxr2fxbfs', '4k8zcresy0kauf57']

   # example_chunk_ids = [
        #1642,
        #1643,\
        #1644,
        #1645,
        #1646,
        #1647,
        #1648,
        #1649,
        #1650,
        ##1651,
        #2248,
        #2249,
        #2260,
        #2261,
        #2262,
        #2263,
        #2269,
        #2590,
        #2591,
        #2595,

    #]

    for ind, chunk_id in enumerate(example_chunk_ids):
        print(f'[{ind}/{len(example_chunk_ids)}] Was processed')
        #if ind <=26461:
        #    continue
        #    print('skip')

        print(chunk_id)
        post_to_ffml_preprocess(chunk_id)
