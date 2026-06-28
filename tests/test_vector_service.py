from collections import Counter
import unittest

from app.services.vector_service import VectorService


class VectorServiceTests(unittest.TestCase):

    def test_tokens_remove_common_question_words(self):
        tokens = VectorService._tokens(
            "What topics are covered in Spring Boot 3 and ReactJS?"
        )

        self.assertEqual(
            tokens,
            ["topic", "spring", "boot", "reactjs"]
        )

    def test_rare_terms_receive_more_weight(self):
        frequencies = Counter({"module": 100, "sonarqube": 2})

        self.assertGreater(
            VectorService._idf("sonarqube", frequencies, 100),
            VectorService._idf("module", frequencies, 100)
        )


if __name__ == "__main__":
    unittest.main()
