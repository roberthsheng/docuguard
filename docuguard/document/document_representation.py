from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

@dataclass
class DocumentElement:
    """Represents a basic element of a document (e.g., paragraph, section title, textbox)."""
    id: str
    text: str
    type: str  # e.g., 'paragraph', 'heading', 'textbox'
    metadata: Dict = field(default_factory=dict) # e.g., {'page_number': 1, 'font_size': 12}
    bbox: Optional[Tuple[float, float, float, float]] = None # Added: (x0, y0, x1, y1)
    entities: List['Entity'] = field(default_factory=list) # Populated later by EntityRecognizer
    local_risk_score: Optional[float] = None # Calculated by RiskScorer
    propagated_risk_score: Optional[float] = None # Calculated by RiskPropagation

@dataclass
class Document:
    """Represents a full document."""
    id: str
    elements: List[DocumentElement]
    metadata: Dict = field(default_factory=dict) # e.g., {'filename': 'report.txt', 'author': 'AI'}
    overall_risk_score: Optional[float] = None # Calculated by DocumentRisk

# Forward reference for type hinting
Entity = 'Entity' # Actual Entity class will be defined in entity_recognizer.py or similar 