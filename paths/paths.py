import features as feats
import geometry as geo

from ua_parser import user_agent_parser

import pprint
from log_config.log_config import logger

##############################################################################
#
# Utility Classes for path objects
#
##############################################################################


class Survey(object):

    def __init__(self, identifier, start):  # ,end):

        self.id = identifier
        self.start = start
        # self.end = float(end)
        # self.duration = self.end - self.start

    def __str__(self):

        out = (
            "== SURVEY ==\n"
            + "ID: "
            + str(self.id)
            + "\n"
            + "Started at: "
            + str(self.start)
        )
        # "Duration: " + str(self.duration/1000) + " seconds." )

        return out

    def __repr__(self):
        return str(self)


class Question(object):

    def __init__(self, identifier, start, end, qtype, stimulus, options, midpoints):

        self.id = stimulus  # identifier
        self.start = float(start)
        self.end = float(end)
        self.duration = self.end - self.start
        self.type = qtype
        self.stimulus = stimulus  # Starting point of mouse
        self.options = {}

        num = 0
        for i in options:
            self.options[i] = "option" + str(num)
            num += 1

        # Midpoints need to be normalized in the same
        # way as the path, or they will make no sense.
        self.midpoints = None

        for i, j in enumerate(midpoints):
            self.midpoints = {"option" + str(i): (j[0], j[1])}

    def __str__(self):

        out = (
            "== QUESTION ==\n"
            + "ID: "
            + str(self.id)
            + "\n"
            + "Duration: "
            + str(self.duration / 1000)
            + " seconds.\n"
            + "Type: "
            + self.type
            + "\n"
            + "Stimulus: "
            + self.stimulus
            + "\n"
            + "Options: "
            + pprint.pformat(self.options)
        )

        return out

    def __repr__(self):
        return str(self)


class Browser(object):

    def __init__(self, useragent, mq, language, width, height):

        self.useragent = user_agent_parser.Parse(useragent)
        self.screen = mq
        self.language = language
        self.width = float(width)
        self.height = float(height)

    def __str__(self):

        out = (
            "== BROWSER ==\n"
            + "Screen: "
            + self.screen
            + "("
            + str(self.width)
            + "x"
            + str(self.height)
            + ")\n"
            + "Language: "
            + self.language
            + "\n"
            + "User Agent:\n"
            + pprint.pformat(self.useragent)
        )

        return out

    def __repr__(self):
        return str(self)


##############################################################################
#
# Path is a class to describe a single survey question
# from the perspective of participant behaviour.
#
# A path is a mouse trajectory, along with metadata
# describing the context, outcome, participant, etc.
#
##############################################################################


# A parser for mouse tracking data collection.
# Expects a list of fields with appropriate
# header information.
#
# Key Fields are:
#
# 	= Identification =
# 	completeCode		# The completion validation code.
# 						# Uniquely identifies a user, since users cannot
# 						# take part in data collection more than once.
# 	surveyID			# Unique identifier for the survey.
#
# 	= Boilerplate =
# 	termsAccepted		# Must be True to have collected any data.
#
# 	= Timing =
# 	surveyStartTime		# Wall time of survey start.
# 	surveyEndTime		# Wall time of survey end.
# 	surveyDuration		# surveyEndTime - surveyStartTime
# 	questionStartTime	# Wall time of question start.
# 	questionEndTime		# Wall time of question end.
# 	questionDuration	# questionEndTime - questionStartTime
#
# 	= Tech Context =
# 	browserUserAgent	# Information about the browser and version
# 	deviceMQ			# Screen size: [XLarge,Large,Medium,Small,XSmall]
# 	mqChanged			# Was the browser resized mid-session? Disqualifies.
# 	browserLanguage		# The ISO language code of the browser settings.
# 	innerWidth			# Actual width of the browser screen in pixels.
# 	innerHeight			# Actual height of the browser screen in pixels.
# 	containerTop		# Coordinates of container top relative to screen.
# 	containerLeft		# Coordinates of container left relative to screen.
#
# 	= Survey Context =
# 	nextQ				# questionID of the next question the user will see.
# 	previousQ			# questionID of the previous question the user saw.
# 	sequenceNum			# Position of this question relative to the survey.
#
# 	= Question =
# 	questionID			# The unique identifier of this question.
# 	questionType		# The type of question. Can be list_choice,
# 						# bipartite_choice, single_field
# 	stimulus			# The question/stimulus the participant sees.
# 	options				# A list of target options for the participant
# 						# to choose from, depending on the question type
# 						# Listed in the same order as midpoints.
# 	midpoints			# The coordinates of the middle of each point of
# 						# interest on the screen--the stimulus, and each
# 						# of the options. Formatted as:
# 						#	"(stimulus x y|option0 x y|option1 x y)"
# 	response			# The selection that was made by the participant.
# 						# Referenced by the same identifier as in options.
# 	mousePath			# The x, y, time coordinates for the mouse path.
# 						# Mouse coordinates are space and pipe separated:
# 						#   "(x|y|t) (x|y|t) (x|y|t)"
#
class Path(object):

    def __init__(self, data):

        self.pf = feats.PathFeatures()

        self.participant = data["id"]

        self.survey = Survey(
            data["surveyID"],
            data["surveyStartTime"],
            # data[header['surveyEndTime']]
        )

        self.question = Question(
            data["questionID"],
            data["questionStartTime"],
            data["questionEndTime"],
            data["questionType"],
            data["stimulus"],
            data["options"],
            data["midpoints"],
        )

        self.browser = Browser(
            data["browserUserAgent"],
            data["deviceMQ"],
            data["browserLanguage"],
            data["innerWidth"],
            data["innerHeight"],
        )

        self.response = data["response"]
        self.qlabel = data['qlabel']

        # Get the mouse coordinates
        self.mouse_path = data["mousePath"]
        logger.debug(f'Original Path: {self.mouse_path}')
        self.clean_trailing_duplicates()
        self.clean_move_duplicates()
        logger.debug(f'Cleaned Path: {self.mouse_path}')

        # Decode each coordinate/timestamp entry
        self.path = []

        try:
            # Right now we only have a feature extraction
            # routine for bipartite choice reaching questions.
            if self.question.type == "bipartite_choice":
                self.path = geo.bipartiteNormPath(
                    self.mouse_path,
                    self.question.midpoints,
                    self.question.options,
                    self.response,
                    self.question.start,
                    self.question.end,
                )

            if self.question.type == "tripartite_choice":
                self.path = geo.tripartiteNormPath(
                    self.mouse_path,
                    self.question.midpoints,
                    self.question.options,
                    self.response,
                    self.question.start,
                    self.question.end,
                )
        except ValueError as e:
            logger.error(f"Error in path: {e}", exc_info=True)
            logger.debug(f"ValueError in path: {self.mouse_path}, {self.participant}, {e}, {self.question.id}, "
                          f"{self.question.stimulus}")

        if not self.path and self.question.type == 'bipartite_choice':
            logger.error(f"Error in path: empty feature set")
            logger.debug(f"Error in path: empty feature set, {self.mouse_path}, "
                          f"{self.participant}, {self.question.id}, {self.question.stimulus}")


        # The un-normalized features
        self.features = self.pf.extract(self.path, 10, self.question.duration)
        # The normalized features
        self.norm_features = {}
        self.relative_uncertainty = 0

    def clean_trailing_duplicates(self):
        """Function to clean out late duplicates from a given mousepath"""
        duplicates = []
        x_end, y_end = 0, 0
        for i, row in enumerate(reversed(self.mouse_path)):

            # Take the second to last row (to avoid the different coordinates from the)
            # touchend/mouseup, which happen due to redirecting in the app.
            # This row represents the finishing point of the movement
            if i:
                if not x_end and not y_end:
                    x_end = row[1]
                    y_end = row[2]

                else:
                    if row[1] == x_end and row[2] == y_end:
                        duplicates.append(len(self.mouse_path) - 1 - i)

        for duplicate in duplicates:
            self.mouse_path.pop(duplicate)

    def clean_move_duplicates(self):
        """Function to clean out successive "move" event duplicates
         from a given path"""
        duplicates = []
        prev_row = []
        for i, row in enumerate(self.mouse_path):
            if i:
                if row[1] == prev_row[1] and row[2] == prev_row[2]:
                    duplicates.append(i)
            prev_row = row

        # Reverse through the list, so the order of earlier elements is unchanged
        for duplicate in reversed(duplicates):
            self.mouse_path.pop(duplicate)

    def __str__(self):

        out = (
            "===== PATH =====\n"
            + "Participant: "
            + self.participant
            + "\n\n"
            + str(self.survey)
            + "\n\n"
            + str(self.question)
            + "\n\n"
            + str(self.browser)
            + "\n\n"
            + "== FEATURES ==\n"
            + pprint.pformat(self.features)
            + "\n\n"
            + "== NORMALIZED FEATURES ==\n"
            + pprint.pformat(self.norm_features)
        )

        return out

    def __repr__(self):
        return str(self)
