import spacy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re # Import re for Luhn check preprocessing

from .patterns import PII_PATTERNS
from .entity_risk import assign_base_risk
from ..document.document_representation import Document, DocumentElement

# --- Luhn Algorithm Implementation --- #
def is_luhn_valid(card_number: str) -> bool:
    """Checks if a credit card number passes the Luhn algorithm."""
    try:
        num = [int(d) for d in str(card_number) if d.isdigit()]
        # Reverse digits and double every second digit
        checksum = sum(sum(divmod(2 * d, 10)) if i % 2 else d for i, d in enumerate(num[::-1]))
        return checksum % 10 == 0
    except (ValueError, TypeError):
        return False

# Define the Entity data structure
@dataclass
class Entity:
    """Represents a detected entity within a document element."""
    text: str                   # The actual text of the entity (e.g., "John Doe", "555-1234")
    label: str                  # The type or category (e.g., "PERSON", "PHONE", "EMAIL")
    start_char: int             # Start character offset within the element's text
    end_char: int               # End character offset within the element's text
    base_risk_score: float      # Initial risk score based on type
    sensitivity_type: str = 'quasi-identifier' # 'explicit-identifier' or 'quasi-identifier'
    metadata: Dict = field(default_factory=dict) # Additional info (e.g., source='ner' or 'pattern')
    # metadata can now store: {'source': 'ner'/'pattern', 'element_type': 'heading'/'paragraph'/...}

class EntityRecognizer:
    """Identifies and classifies entities in documents using NER and pattern matching."""

    def __init__(self, spacy_model_name="en_core_web_md"):
        """Initializes the EntityRecognizer, loading the specified spaCy model."""
        try:
            print(f"Attempting to load spaCy model '{spacy_model_name}'...")
            self.nlp = spacy.load(spacy_model_name)
            print(f"spaCy model '{spacy_model_name}' loaded successfully.")
        except OSError:
            print(f"Error: spaCy model '{spacy_model_name}' not found.")
            print(f"Please download it using: python -m spacy download {spacy_model_name}")
            raise

    def _detect_pii_patterns(self, text: str) -> List[Tuple[str, int, int, str]]:
        """Detects entities using predefined regex patterns."""
        found_entities = []
        for label, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                # Add potential matches directly, validation happens later if needed
                found_entities.append((match.group(0), match.start(), match.end(), label))
        return found_entities

    def _detect_ner_entities(self, text: str) -> List[Tuple[str, int, int, str]]:
        """Detects entities using the loaded spaCy NER model."""
        doc = self.nlp(text)
        found_entities = []
        for ent in doc.ents:
            found_entities.append((ent.text, ent.start_char, ent.end_char, ent.label_))
        return found_entities

    def classify_entity_sensitivity(self, label: str, context: Optional[DocumentElement] = None) -> str:
        """Classifies an entity label as explicit or quasi-identifier, potentially using context."""
        explicit_types = {'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD'}
        if label in explicit_types:
            return 'explicit-identifier'
        # Example context use: elevate PERSON in heading
        if label == 'PERSON' and context and context.type == 'heading':
             print(f"  -> Elevated sensitivity for PERSON '{context.text[:20]}...' in heading.")
             # Decide: treat as explicit or just higher risk quasi? For now, stick to definition.
             # return 'explicit-identifier' # Option
             pass # Keep as quasi for now, risk score reflects base + context later

        return 'quasi-identifier'

    def detect_entities_in_element(self, element: DocumentElement) -> List[Entity]:
        """Detects entities, validates CREDIT_CARD with Luhn, adds context."""
        text = element.text
        pattern_entities = self._detect_pii_patterns(text)
        ner_entities = self._detect_ner_entities(text)

        combined_entities = []
        covered_spans = set()

        # Add pattern entities first, validating where necessary
        for text_val, start, end, label in pattern_entities:
            # --- Luhn Check for Credit Cards --- #
            if label == 'CREDIT_CARD':
                # Remove potential separators before Luhn check
                cleaned_num = re.sub(r'[- ]', '', text_val)
                if not is_luhn_valid(cleaned_num):
                    print(f"  -> Discarded potential CREDIT_CARD (failed Luhn check): {text_val}")
                    continue # Skip this match if Luhn check fails
            # ----------------------------------- #

            # Check for overlap before adding
            current_span = set(range(start, end))
            if not current_span.intersection(covered_spans):
                base_risk = assign_base_risk(label)
                sensitivity = self.classify_entity_sensitivity(label, element)
                entity_metadata = {'source': 'pattern', 'element_type': element.type}
                entity = Entity(text=text_val, label=label, start_char=start, end_char=end,
                                base_risk_score=base_risk, sensitivity_type=sensitivity,
                                metadata=entity_metadata)
                combined_entities.append(entity)
                covered_spans.update(current_span)
            else:
                print(f"  -> Discarded overlapping pattern entity: {text_val} ({label})")

        # Add NER entities if they don't overlap
        for text_val, start, end, label in ner_entities:
            current_span = set(range(start, end))
            if not current_span.intersection(covered_spans):
                base_risk = assign_base_risk(label)
                sensitivity = self.classify_entity_sensitivity(label, element)
                entity_metadata = {'source': 'ner', 'element_type': element.type}
                entity = Entity(text=text_val, label=label, start_char=start, end_char=end,
                                base_risk_score=base_risk, sensitivity_type=sensitivity,
                                metadata=entity_metadata)
                combined_entities.append(entity)
                covered_spans.update(current_span)
            else:
                # Simple overlap rule: pattern entities added first take precedence
                 print(f"  -> Discarded overlapping NER entity: {text_val} ({label})")

        combined_entities.sort(key=lambda e: e.start_char)
        return combined_entities

    def detect_entities(self, document: Document) -> None:
        """Detects entities for all elements in a Document and updates them in place."""
        print(f"Starting entity detection for document {document.id}...")
        total_entities = 0
        for element in document.elements:
            entities = self.detect_entities_in_element(element)
            element.entities = entities # Assign detected entities back to the element
            total_entities += len(entities)
        print(f"Finished entity detection. Found {total_entities} entities in {len(document.elements)} elements.") 