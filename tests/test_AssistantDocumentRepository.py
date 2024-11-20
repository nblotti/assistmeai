# File: test_AssistantDocumentRepository.py

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from assistants.AssistantDocumentRepository import AssistantDocumentRepository
from assistants.AssistantsDocument import AssistantsDocument, AssistantDocumentType, AssistantsDocumentCreate
from document.Document import DocumentCreate


class TestAssistantDocumentRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()
        AssistantsDocument.metadata.create_all(cls.engine)
        cls.repository = AssistantDocumentRepository(cls.session)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        cls.engine.dispose()

    def setUp(self):
        self.session.rollback()
        self.session.query(AssistantsDocument).delete()
        self.session.commit()
        self.add_sample_data()

    def test_convert_to_int_with_non_none_string(self):
        self.assertEqual(AssistantDocumentRepository.convert_to_int("123"), 123)

    def test_convert_to_int_with_none(self):
        self.assertIsNone(AssistantDocumentRepository.convert_to_int(None))

    def test_convert_to_int_with_empty_string(self):
        with self.assertRaises(ValueError):
            AssistantDocumentRepository.convert_to_int("")

    def test_convert_to_int_with_negative_string(self):
        self.assertEqual(AssistantDocumentRepository.convert_to_int("-123"), -123)

    def test_convert_to_int_with_non_numeric_string(self):
        with self.assertRaises(ValueError):
            AssistantDocumentRepository.convert_to_int("abc")

    def test_convert_to_int_with_float_string(self):
        with self.assertRaises(ValueError):
            AssistantDocumentRepository.convert_to_int("123.45")

    def test_convert_to_str_with_none(self):
        result = AssistantDocumentRepository.convert_to_str(None)
        self.assertIsNone(result)

    def test_convert_to_str_with_zero(self):
        result = AssistantDocumentRepository.convert_to_str(0)
        self.assertEqual(result, '0')

    def test_convert_to_str_with_positive_integer(self):
        result = AssistantDocumentRepository.convert_to_str(123)
        self.assertEqual(result, '123')

    def test_convert_to_str_with_negative_integer(self):
        result = AssistantDocumentRepository.convert_to_str(-456)
        self.assertEqual(result, '-456')

    def test_convert_to_str_with_large_integer(self):
        result = AssistantDocumentRepository.convert_to_str(9876543210)
        self.assertEqual(result, '9876543210')

    def add_sample_data(self):
        sample_data = [
            AssistantsDocument(
                assistant_id=1,
                document_id=1,
                document_name="test document 1",
                assistant_document_type=AssistantDocumentType.MY_DOCUMENTS,
                shared_group_id=1),
            AssistantsDocument(
                assistant_id=1,
                document_id=2,
                document_name="test document 2",
                assistant_document_type=AssistantDocumentType.MY_DOCUMENTS,
                shared_group_id=1),
            AssistantsDocument(
                assistant_id=2,
                document_id=3,
                document_name="test document 4",
                assistant_document_type=AssistantDocumentType.MY_DOCUMENTS,
                shared_group_id=5)
        ]
        self.session.add_all(sample_data)
        self.session.commit()

    def test_delete_existing_assistant(self):
        affected_rows = self.repository.delete(1)
        self.assertEqual(affected_rows, 1)
        result = self.session.query(AssistantsDocument).filter_by(id=1).first()
        self.assertIsNone(result)

    def test_delete_non_existing_assistant(self):
        affected_rows = self.repository.delete(999)
        self.assertEqual(affected_rows, 0)

    def test_delete_with_multiple_records(self):
        affected_rows = self.repository.delete(1)
        self.assertEqual(affected_rows, 1)
        affected_rows = self.repository.delete(2)
        self.assertEqual(affected_rows, 1)
        result_1 = self.session.query(AssistantsDocument).filter_by(id=1).first()
        result_2 = self.session.query(AssistantsDocument).filter_by(id=2).first()
        self.assertIsNone(result_1)
        self.assertIsNone(result_2)

    def test_list_by_assistant_id_with_existing_id(self):

        # Test
        result = self.repository.list_by_assistant_id(1)
        self.assertGreater(len(result), 0)
        for doc in result:
            self.assertEqual(doc.assistant_id, "1")

    def test_list_by_assistant_id_with_non_existing_id(self):
        result = self.repository.list_by_assistant_id(999)
        self.assertEqual(result, [])

    def test_list_by_assistant_id_with_multiple_documents(self):

        result = self.repository.list_by_assistant_id(1)
        self.assertEqual(len(result), 2)
        for doc in result:
            self.assertEqual(doc.assistant_id, "1")

    def test_create_assistant_document(self):
        new_document = AssistantsDocumentCreate(
            assistant_id="10",
            document_id= "10",
            document_name= "test document 10",
            assistant_document_type= AssistantDocumentType.MY_DOCUMENTS,
            shared_group_id= "10"
        )

        created_document = self.repository.create(new_document)

        self.assertIsNotNone(created_document)
        self.assertEqual(created_document.assistant_id, "10")
        self.assertEqual(created_document.document_id, "10")
        self.assertEqual(created_document.document_name, "test document 10")
        self.assertEqual(created_document.assistant_document_type, AssistantDocumentType.MY_DOCUMENTS)
        self.assertEqual(created_document.shared_group_id, "10")
        self.assertEqual(self.session.query(AssistantsDocument).filter_by(document_id=10).one().document_name,
                         "test document 10")

if __name__ == "__main__":
    unittest.main()
