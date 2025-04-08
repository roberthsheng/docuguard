import unittest
import os
from unittest.mock import patch, mock_open

# Adjust import path based on how tests are run
# If running pytest from root, this should work:
from docuguard.document.document_parser import DocumentParser, segment_document, parse_text_file, extract_metadata
from docuguard.document.document_representation import Document, DocumentElement

# Define paths to test files (relative to project root)
SAMPLE_TXT_PATH = "data/sample_report.txt"
# SAMPLE_PDF_PATH = "data/sample_report.pdf" # PDF path commented out
ENRON_SAMPLE_PATH = "data/enron/williams-w3/sent_items/1."

class TestDocumentParser(unittest.TestCase):

    def test_segment_document_simple(self):
        text = "This is the first paragraph.\n\nThis is the second."
        elements = segment_document(text)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0].text, "This is the first paragraph.")
        self.assertEqual(elements[0].type, "paragraph")
        self.assertEqual(elements[0].id, "elem_0")
        self.assertEqual(elements[1].text, "This is the second.")
        self.assertEqual(elements[1].type, "paragraph")
        self.assertEqual(elements[1].id, "elem_1")

    def test_segment_document_extra_newlines(self):
        text = "\n\nFirst.\n\n\n\nSecond.\n\n"
        elements = segment_document(text)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0].text, "First.")
        self.assertEqual(elements[1].text, "Second.")

    def test_segment_document_empty(self):
        text = ""
        elements = segment_document(text)
        self.assertEqual(len(elements), 0)

    @patch('os.path.getsize')
    @patch('os.path.basename')
    def test_extract_metadata(self, mock_basename, mock_getsize):
        mock_basename.return_value = "test.txt"
        mock_getsize.return_value = 123
        metadata = extract_metadata("/fake/path/test.txt")
        self.assertEqual(metadata['filename'], "test.txt")
        self.assertEqual(metadata['filesize_bytes'], 123)
        mock_basename.assert_called_once_with("/fake/path/test.txt")
        mock_getsize.assert_called_once_with("/fake/path/test.txt")

    @patch('builtins.open', new_callable=mock_open, read_data="Hello\n\nWorld")
    @patch('os.path.getsize', return_value=11)
    @patch('os.path.basename', return_value='mock_file.txt')
    @patch('uuid.uuid4', return_value='mock-uuid')
    def test_parse_text_file_mocked(self, mock_uuid, mock_basename, mock_getsize, mock_file):
        # Renamed to avoid clash with actual file test
        doc = parse_text_file("mock_file.txt")
        self.assertIsInstance(doc, Document)
        self.assertEqual(doc.id, 'mock-uuid')
        self.assertEqual(doc.metadata['filename'], 'mock_file.txt')
        self.assertEqual(doc.metadata['filesize_bytes'], 11)
        self.assertEqual(doc.metadata['source_format'], 'text')
        self.assertEqual(len(doc.elements), 2)
        self.assertEqual(doc.elements[0].text, "Hello")
        self.assertEqual(doc.elements[1].text, "World")
        mock_file.assert_called_once_with("mock_file.txt", 'r', encoding='utf-8')

    @patch('docuguard.document.document_parser.parse_text_file')
    def test_document_parser_txt_mocked(self, mock_parse_text):
        mock_doc = Document(id="test-doc", elements=[], metadata={'filename': 'test.txt'})
        mock_parse_text.return_value = mock_doc
        parser = DocumentParser()
        result = parser.parse("some/path/test.txt")
        self.assertEqual(result, mock_doc)
        mock_parse_text.assert_called_once_with("some/path/test.txt")

    def test_document_parser_unsupported(self):
        parser = DocumentParser()
        with self.assertRaises(ValueError) as cm:
            parser.parse("document.docx")
        self.assertIn("Unsupported file format: .docx", str(cm.exception))

    # --- PDF Test Commented Out --- 
    # def test_parse_real_pdf_layout_aware(self):
    #     """Tests layout-aware parsing of the actual sample_report.pdf file."""
    #     self.assertTrue(os.path.exists(SAMPLE_PDF_PATH), f"Test file not found: {SAMPLE_PDF_PATH}")
    #     parser = DocumentParser()
    #     try:
    #         document = parser.parse(SAMPLE_PDF_PATH)
    #         # ... (rest of PDF test commented out) ...
    #     except Exception as e:
    #         import traceback
    #         self.fail(f"PDF layout parsing failed with error: {e}\n{traceback.format_exc()}")

    # --- Tests for Text Files --- 
    def test_parse_real_enron_email(self):
        """Tests parsing an actual Enron email file (.txt format)."""
        self.assertTrue(os.path.exists(ENRON_SAMPLE_PATH), f"Test file not found: {ENRON_SAMPLE_PATH}")
        parser = DocumentParser()
        try:
            document = parser.parse(ENRON_SAMPLE_PATH)
            self.assertIsInstance(document, Document)
            self.assertEqual(document.metadata['filename'], os.path.basename(ENRON_SAMPLE_PATH))
            self.assertEqual(document.metadata['source_format'], 'text')
            self.assertGreater(len(document.elements), 0, "Enron email parsing resulted in zero elements.")
            first_element_text = document.elements[0].text.lower()
            self.assertTrue(
                first_element_text.startswith("message-id:") or \
                first_element_text.startswith("date:"),
                f"First element doesn't seem to start with expected email headers: {first_element_text[:50]}..."
            )
        except Exception as e:
            self.fail(f"Enron email parsing failed with error: {e}")

    def test_parse_non_existent_file(self):
        """Tests parsing a non-existent file."""
        parser = DocumentParser()
        with self.assertRaises(FileNotFoundError):
            parser.parse("non_existent_file.txt")
        # Test PDF error handling (should now raise ValueError as it's unsupported)
        with self.assertRaises(ValueError) as cm:
             parser.parse("non_existent_file.pdf")
        self.assertIn("Unsupported file format: .pdf", str(cm.exception))


if __name__ == '__main__':
    unittest.main() 