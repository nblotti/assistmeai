import unittest

from dotenv import load_dotenv

from assistants.AssistantsController import build_response_content


class TestAssistantsController(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Setting necessary environment variables
        load_dotenv()

    def test_build_response_content_with_output_only(self):
        result = {"output": "Test Output"}
        expected_response = {"result": "Test Output"}
        self.assertEqual(build_response_content(result), expected_response)

    def test_build_response_content_with_output_and_sources(self):
        result = {"output": "Test Output", "sources": ["Source1", "Source2"]}
        expected_response = {"result": "Test Output", "sources": ["Source1", "Source2"]}
        self.assertEqual(build_response_content(result), expected_response)

    def test_build_response_content_with_empty_output(self):
        result = {"output": ""}
        expected_response = {"result": ""}
        self.assertEqual(build_response_content(result), expected_response)

    def test_build_response_content_with_missing_output(self):
        result = {}
        with self.assertRaises(KeyError):
            build_response_content(result)

    def test_build_response_content_with_extra_keys(self):
        result = {"output": "Test Output", "extra_key": "Extra Value"}
        expected_response = {"result": "Test Output"}
        self.assertEqual(build_response_content(result), expected_response)


if __name__ == "__main__":
    unittest.main()
