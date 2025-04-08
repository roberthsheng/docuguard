from typing import Dict

# Base risk scores assigned to different entity types
# Adjusted to reflect slightly more realistic relative risk
# Still requires proper validation for actual use.

BASE_RISK_SCORES: Dict[str, float] = {
    # Pattern-based PII
    'EMAIL': 0.8,
    'PHONE': 0.7,
    'SSN': 1.0, # Highest explicit risk
    'DATE_PATTERN': 0.5,
    'CREDIT_CARD': 1.0, # Highest explicit risk
    'ZIP_CODE': 0.4,
    'ADDRESS': 0.7, # Addresses are strong quasi-identifiers

    # NER-based Entities (adjusting relative risk slightly)
    'PERSON': 0.6,
    'ORG': 0.3, # Reduced risk unless context proves otherwise
    'GPE': 0.2, # Generally lower risk
    'LOC': 0.3,
    'DATE': 0.5,
    'TIME': 0.1,
    'MONEY': 0.6,
    'PERCENT': 0.05,
    'FAC': 0.2,
    'PRODUCT': 0.05,
    'EVENT': 0.2,
    'WORK_OF_ART': 0.05,
    'LAW': 0.1,
    'LANGUAGE': 0.0,
    'NORP': 0.4, # Can be sensitive depending on group
    'QUANTITY': 0.05,
    'ORDINAL': 0.05,
    'CARDINAL': 0.05,

    'UNKNOWN': 0.0 # Assume unknown is safe unless context proves otherwise
}

def assign_base_risk(entity_type: str) -> float:
    """Assigns a base risk score to an entity based on its type."""
    normalized_type = entity_type.upper()
    return BASE_RISK_SCORES.get(normalized_type, BASE_RISK_SCORES['UNKNOWN']) 