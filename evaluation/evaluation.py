# Evaluation functions and metrics

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

# Add sentence-transformers import for utility measure
try:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim
    sbert_model = SentenceTransformer('all-MiniLM-L6-v2') # Load a default SBERT model
    print("Sentence Transformer model loaded for utility measurement.")
except ImportError:
    print("Warning: sentence-transformers library not found. Semantic similarity utility measure disabled.")
    print("Install it using: pip install sentence-transformers")
    sbert_model = None
except Exception as e:
    print(f"Warning: Could not load Sentence Transformer model: {e}")
    sbert_model = None

# Import project types if defined, otherwise use Any
try:
    from docuguard.document.document_representation import Document, DocumentElement
    from docuguard.entity.entity_recognizer import Entity
except ImportError:
    DocumentElement = Any
    Document = Any
    Entity = Any

# Ground truth format assumption:
# A dictionary where keys are element IDs (e.g., "elem_0")
# and values are lists of ground truth entity dictionaries:
# {"text": "John Doe", "label": "PERSON", "start_char": 10, "end_char": 18}
# Character offsets are relative to the element's text.
GroundTruth = Dict[str, List[Dict[str, Any]]]

def _calculate_overlap(pred_start, pred_end, gt_start, gt_end):
    """Calculate the overlap length between two spans."""
    return max(0, min(pred_end, gt_end) - max(pred_start, gt_start))

def evaluate_entity_detection(
    doc_elements: List[DocumentElement],
    ground_truth: GroundTruth,
    label_map: Optional[Dict] = None,
    match_strategy: str = 'exact', # 'exact' or 'overlap'
    overlap_threshold: float = 0.5 # Used if match_strategy is 'overlap'
) -> Dict:
    """Calculates precision, recall, F1 for detected entities against ground truth.

    Args:
        doc_elements: List of DocumentElement objects with detected entities.
        ground_truth: Dictionary mapping element IDs to lists of ground truth entities.
        label_map: Optional mapping for ground truth labels.
        match_strategy: 'exact' (text, label, span must match) or 'overlap'
                        (label must match, span overlap must meet threshold).
        overlap_threshold: Minimum overlap fraction (IOU or similar) for partial match.

    Returns:
        Dictionary containing overall and per-class precision, recall, F1 scores.
    """
    true_positives = defaultdict(int)
    false_positives = defaultdict(int)
    false_negatives = defaultdict(int)
    unique_labels = set()
    pred_matches = defaultdict(set) # Keep track of matched predictions
    gt_matches = defaultdict(set) # Keep track of matched ground truths

    if label_map is None: label_map = {}

    for element in doc_elements:
        elem_id = element.id
        gt_entities_in_elem = ground_truth.get(elem_id, [])
        pred_entities_in_elem = element.entities

        # Add labels to unique set
        unique_labels.update(p.label for p in pred_entities_in_elem)
        unique_labels.update(label_map.get(gt['label'], gt['label']) for gt in gt_entities_in_elem)

        # Match predictions to ground truth
        for p_idx, pred in enumerate(pred_entities_in_elem):
            pred_id = (elem_id, p_idx)
            best_match_gt_idx = -1
            max_overlap = -1

            for gt_idx, gt in enumerate(gt_entities_in_elem):
                gt_id = (elem_id, gt_idx)
                if gt_id in gt_matches.get(pred.label, set()): continue # Skip already matched GT

                gt_label = label_map.get(gt['label'], gt['label'])
                if pred.label == gt_label:
                    if match_strategy == 'exact':
                        if pred.text == gt['text'] and pred.start_char == gt['start_char'] and pred.end_char == gt['end_char']:
                            best_match_gt_idx = gt_idx
                            break # Exact match found
                    elif match_strategy == 'overlap':
                        overlap = _calculate_overlap(pred.start_char, pred.end_char, gt['start_char'], gt['end_char'])
                        pred_len = pred.end_char - pred.start_char
                        gt_len = gt['end_char'] - gt['start_char']
                        # Simple overlap fraction (of prediction or gt span)
                        # Could use IOU: overlap / (pred_len + gt_len - overlap)
                        if pred_len > 0 and overlap / pred_len >= overlap_threshold and gt_len > 0 and overlap / gt_len >= overlap_threshold:
                             if overlap > max_overlap: # Take best overlapping match
                                 max_overlap = overlap
                                 best_match_gt_idx = gt_idx
            # Assign match if found
            if best_match_gt_idx != -1:
                gt_id_matched = (elem_id, best_match_gt_idx)
                if gt_id_matched not in gt_matches.get(pred.label, set()):
                    true_positives[pred.label] += 1
                    pred_matches.setdefault(pred.label, set()).add(pred_id)
                    gt_matches.setdefault(pred.label, set()).add(gt_id_matched)
                else:
                    # GT already matched by another prediction, this is an FP
                    false_positives[pred.label] += 1
            else:
                 false_positives[pred.label] += 1 # No match found for prediction

        # Calculate FN by finding unmatched ground truths
        for gt_idx, gt in enumerate(gt_entities_in_elem):
            gt_label = label_map.get(gt['label'], gt['label'])
            gt_id = (elem_id, gt_idx)
            if gt_id not in gt_matches.get(gt_label, set()):
                false_negatives[gt_label] += 1

    # Calculate metrics per class and overall
    results = {'per_class': {}}
    all_tp, all_fp, all_fn = 0, 0, 0
    for label in unique_labels:
        tp = true_positives[label]
        fp = false_positives[label]
        fn = false_negatives[label]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        results['per_class'][label] = {'precision': precision, 'recall': recall, 'f1': f1, 'support': tp + fn}
        all_tp += tp; all_fp += fp; all_fn += fn

    overall_precision = all_tp / (all_tp + all_fp) if (all_tp + all_fp) > 0 else 0.0
    overall_recall = all_tp / (all_tp + all_fn) if (all_tp + all_fn) > 0 else 0.0
    overall_f1 = 2 * (overall_precision * overall_recall) / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0.0
    results['overall'] = {'precision': overall_precision, 'recall': overall_recall, 'f1': overall_f1, 'support': all_tp + all_fn}

    print(f"Entity Detection Evaluation Complete (Strategy: {match_strategy}): Overall F1 = {overall_f1:.4f}")
    return results

def evaluate_risk_scoring(document: Document, ground_truth_risk: Dict) -> Dict:
    """Assesses risk score accuracy (placeholder)."""
    print("Placeholder: Evaluating risk scoring...")
    # TODO: Implement risk scoring evaluation (correlation, MAE, etc.)
    # Requires calculated risk scores on document and ground truth risk
    return {
        'element_local_risk_correlation': 0.0,
        'document_overall_risk_mae': 0.0
    }

def measure_utility(original_text: str, anonymized_text: str) -> Dict:
    """Quantifies utility using word count ratio and semantic similarity (if available)."""
    original_words = len(original_text.split())
    anonymized_words = len(anonymized_text.split())
    ratio = anonymized_words / original_words if original_words > 0 else (1.0 if anonymized_words == 0 else 0.0)

    results = {'word_count_ratio': ratio}

    if sbert_model:
        try:
            # Encode texts - ensure they are not empty
            if original_text.strip() and anonymized_text.strip():
                emb1 = sbert_model.encode(original_text, convert_to_tensor=True)
                emb2 = sbert_model.encode(anonymized_text, convert_to_tensor=True)
                similarity = cos_sim(emb1, emb2).item()
                results['semantic_similarity'] = similarity
                print(f"Utility Measurement: Word Ratio={ratio:.4f}, Semantic Sim={similarity:.4f}")
            else:
                 results['semantic_similarity'] = 0.0 # Handle empty strings
                 print(f"Utility Measurement: Word Ratio={ratio:.4f}, Semantic Sim=N/A (empty text)")

        except Exception as e:
            print(f"Error calculating semantic similarity: {e}")
            results['semantic_similarity'] = None # Indicate error
    else:
        print(f"Utility Measurement (Word Count Ratio only): {ratio:.4f}")

    return results 