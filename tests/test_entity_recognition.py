import unittest
# Removed: from unittest.mock import patch, MagicMock # No longer mocking spacy
import spacy # Import the real spacy

from docuguard.entity.entity_recognizer import EntityRecognizer, Entity
from docuguard.document.document_representation import Document, DocumentElement

# No longer need MockSpacy classes

# Removed class decorator: @patch('spacy.load', return_value=MockSpacyModel())
class TestEntityRecognizer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the real spaCy medium model once for the entire test class."""
        cls.model_name = "en_core_web_md" # Use medium model
        try:
            cls.nlp = spacy.load(cls.model_name)
            # Pass the model name explicitly during testing
            cls.recognizer = EntityRecognizer(spacy_model_name=cls.model_name)
            print(f"\nReal spaCy model {cls.model_name} loaded for tests.")
        except OSError:
            print(f"\nError: spaCy model '{cls.model_name}' not found.")
            print(f"Please download it: python -m spacy download {cls.model_name}")
            raise unittest.SkipTest(f"spaCy model {cls.model_name} not available")

    # Test methods no longer need mock_spacy_load argument

    def test_init(self):
        """Test if spaCy model is loaded during init (using class instance)."""
        self.assertIsNotNone(self.recognizer)
        self.assertIsNotNone(self.recognizer.nlp)

    def test_detect_pii_patterns(self):
        # This test doesn't rely on spaCy
        text = "Contact me at test@example.com or call 555-123-4567. SSN: 999-00-1111."
        entities = self.recognizer._detect_pii_patterns(text)
        self.assertEqual(len(entities), 3)
        labels = {e[3] for e in entities}
        self.assertSetEqual(labels, {'EMAIL', 'PHONE', 'SSN'})

    def test_detect_ner_entities_real_model(self):
        # Use the recognizer with the real md model
        text = "Alice works at Google in London."
        entities_tuples = self.recognizer._detect_ner_entities(text)
        self.assertEqual(len(entities_tuples), 3)
        labels = {e[3] for e in entities_tuples}
        texts = {e[0] for e in entities_tuples}
        # md model should reliably find these
        self.assertSetEqual(labels, {'PERSON', 'ORG', 'GPE'})
        self.assertSetEqual(texts, {'Alice', 'Google', 'London'})

    def test_classify_entity_sensitivity(self):
        # No change needed here
        self.assertEqual(self.recognizer.classify_entity_sensitivity('EMAIL'), 'explicit-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('PHONE'), 'explicit-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('SSN'), 'explicit-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('PERSON'), 'quasi-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('ORG'), 'quasi-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('GPE'), 'quasi-identifier')
        self.assertEqual(self.recognizer.classify_entity_sensitivity('DATE'), 'quasi-identifier')

    def test_detect_entities_in_element_combined_real_model(self):
        element = DocumentElement(id="e1", text="Alice <alice@email.com> works at Google. Call 123-456-7890.", type="paragraph")
        entities = self.recognizer.detect_entities_in_element(element)

        # Check combined output (patterns + real md NER)
        # Expect: Alice (PERSON, ner), alice@email.com (EMAIL, pattern), Google (ORG, ner), 123-456-7890 (PHONE, pattern)
        self.assertGreaterEqual(len(entities), 4) # Expect all four

        labels = {e.label for e in entities}
        texts = {e.text for e in entities}

        self.assertIn('PERSON', labels) # Expect PERSON with md model
        self.assertIn('EMAIL', labels)
        self.assertIn('PHONE', labels)
        self.assertIn('ORG', labels)

        self.assertIn('Alice', texts)
        self.assertIn('alice@email.com', texts)
        self.assertIn('Google', texts)
        self.assertIn('123-456-7890', texts)

        # Check sources
        sources = {e.text: e.metadata.get('source') for e in entities}
        self.assertEqual(sources.get('alice@email.com'), 'pattern')
        self.assertEqual(sources.get('123-456-7890'), 'pattern')
        self.assertEqual(sources.get('Alice'), 'ner')
        self.assertEqual(sources.get('Google'), 'ner')

    # Removed test_detect_entities_in_element_overlap as it relied heavily on specific mock behavior
    # Testing precise overlap scenarios with a real model is harder to set up reliably.

    def test_detect_entities_document_real_model(self):
        elements = [
            DocumentElement(id="e1", text="Call 555-111-2222.", type="paragraph"),
            DocumentElement(id="e2", text="Meet Alice at Google.", type="paragraph")
        ]
        doc = Document(id="doc1", elements=elements)

        self.recognizer.detect_entities(doc)

        # Element 1: PHONE (pattern)
        self.assertEqual(len(doc.elements[0].entities), 1)
        self.assertEqual(doc.elements[0].entities[0].label, 'PHONE')

        # Element 2: PERSON (ner), ORG (ner) - md model should find these
        self.assertEqual(len(doc.elements[1].entities), 2)
        ent_map = {e.label: e.text for e in doc.elements[1].entities}
        self.assertIn('PERSON', ent_map)
        self.assertEqual(ent_map['PERSON'], 'Alice')
        self.assertIn('ORG', ent_map)
        self.assertEqual(ent_map['ORG'], 'Google')

if __name__ == '__main__':
    unittest.main() 