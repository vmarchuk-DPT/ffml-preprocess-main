import re
import math


class QuestionFeatures(object):
    def __init__(self, question):
        self.question_features = self.extract(question)

    # Run all the extractors on the path
    # to return a feature set describing
    # the given path.
    def extract(self, question):
        length = len(self.get_question_words(question))
        gunning_fog = self.gunning_fog_index(question)
        smog_index = self.smog_index(question)
        return {'question_features':
                    {'length': [length, "series"],
                     'gunning_fog': [gunning_fog, "series"],
                     'smog_index': [smog_index, "series"]}}

    def count_syllables(self, word):
        word = word.lower()
        vowels = "aeiou"
        syllables = 0
        prev_char_was_vowel = False
        for char in word:
            if char in vowels:
                if not prev_char_was_vowel:
                    syllables += 1
                prev_char_was_vowel = True
            else:
                prev_char_was_vowel = False
        if word.endswith("e"):
            syllables -= 1
        return max(syllables, 1)


    def is_complex(self, word):
        return self.count_syllables(word) >= 3 and word.isalpha()

    # Simple regex tokeniser
    def get_question_words(self, text):
        words = re.findall(r'\b\w+\b', text)
        return words


    def gunning_fog_index(self, text):
        """
        Calculate the Gunning Fog Index for a given text.

        Parameters:
            text (str): The text to analyze.

        Returns:
            float: The Gunning Fog Index of the text.
        """
        # Split the text into sentences using '.', '!', or '?' as delimiters
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        num_sentences = len(sentences)

        words = self.get_question_words(text)
        num_words = len(words)

        complex_words = [word for word in words if self.is_complex(word)]
        num_complex_words = len(complex_words)

        # Avoid division by zero
        if num_sentences == 0 or num_words == 0:
            return 0

        # Calculate Gunning Fog Index
        avg_sentence_length = num_words / num_sentences
        perc_complex_words = (num_complex_words / num_words) * 100
        fog_index = 0.4 * (avg_sentence_length + perc_complex_words)

        return round(fog_index, 2)

    def smog_index(self, text):
        """
        Calculate the SMOG Index for a given text.

        Parameters:
            text (str): The text to analyze.

        Returns:
            float: The SMOG Index of the text.
        """
        # Split the text into sentences using '.', '!', or '?' as delimiters
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        num_sentences = len(sentences)

        words = self.get_question_words(text)

        complex_words = [word for word in words if self.is_complex(word)]
        num_complex_words = len(complex_words)

        # Avoid division by zero
        if num_sentences == 0:
            return 0

        # Calculate SMOG Index
        smog = 1.043 * math.sqrt(num_complex_words * (30 / num_sentences)) + 3.1291

        return round(smog, 2)

