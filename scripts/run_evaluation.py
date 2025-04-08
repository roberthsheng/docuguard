import argparse
import sys
import os
import pprint
from collections import defaultdict
from typing import Optional

# Ensure the docuguard package is discoverable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Document processing and entity recognition components
    from docuguard.document.document_parser import segment_document # Use basic segmenter for text
    from docuguard.document.document_representation import Document, DocumentElement
    from docuguard.entity.entity_recognizer import EntityRecognizer
    # Evaluation components
    from evaluation.evaluation import evaluate_entity_detection
    from docuguard.utils.data_loader import load_kaggle_pii_dataset, convert_bio_to_offset_entities
except ImportError as e:
    print(f"Error importing DocuGuard modules: {e}")
    print("Please ensure the script is run from the project root or that the project root is in PYTHONPATH.")
    sys.exit(1)

# --- Label Mapping (Example) --- #
# Map Kaggle labels (e.g., NAME_STUDENT) to potentially broader categories if desired,
# or align with spaCy labels where appropriate.
# For now, use a direct mapping or simplified categories.
KAGGLE_TO_DOCUGUARD_LABEL_MAP = {
    # Direct Maps (Examples - verify against dataset)
    "USERNAME": "USERNAME",
    "ID_NUM": "ID_NUM",
    "EMAIL": "EMAIL",
    "URL_PERSONAL": "URL",
    "PHONE_NUM": "PHONE",
    "STREET_ADDRESS": "ADDRESS", # Map to our pattern
    # Grouped Maps (Examples)
    "NAME_STUDENT": "PERSON",
    "NAME_TEACHER": "PERSON",
    "LOCATION": "LOC", # Or GPE depending on usage
    "DATE_OB": "DATE",
    # Add other labels from the dataset as needed
}

def run_kaggle_evaluation(dataset_path: str, num_entries: Optional[int] = None):
    """Loads Kaggle data, runs detection, and evaluates entity recognition."""
    dataset = load_kaggle_pii_dataset(dataset_path)
    if num_entries:
        print(f"Limiting evaluation to first {num_entries} entries.")
        dataset = dataset[:num_entries]

    if not dataset:
        print("No data loaded, skipping evaluation.")
        return

    recognizer = EntityRecognizer()

    agg_tp = defaultdict(int)
    agg_fp = defaultdict(int)
    agg_fn = defaultdict(int)
    all_labels = set()

    for i, entry in enumerate(dataset):
        print(f"\n--- Processing Document {i+1}/{len(dataset)} (ID: {entry['document']}) ---")
        # Use the correct column name 'text' from the CSV header
        document_text = entry['text']

        # 1. Simulate Parsing
        elements = segment_document(document_text)
        doc = Document(id=entry['document'], elements=elements, metadata={'source_format': 'text'})

        # 2. Run Entity Detection
        recognizer.detect_entities(doc)

        # 3. Convert BIO Ground Truth to Offset Format for the *entire* document text
        ground_truth_entities_doc_level = convert_bio_to_offset_entities(
            entry['tokens'], entry['labels'], entry['trailing_whitespace'], document_text # Pass correct text
        )

        # 4. Map document-level GT entities to elements and adjust offsets
        ground_truth_for_eval = defaultdict(list)
        for element in doc.elements:
            try:
                # Use the original document_text for finding element spans
                elem_start = document_text.index(element.text)
            except ValueError:
                 print(f"Warning: Element text for {element.id} not found precisely in full text. GT mapping for this element might be incomplete.")
                 continue
            elem_end = elem_start + len(element.text)

            for gt_entity in ground_truth_entities_doc_level:
                if elem_start <= gt_entity['start_char'] < elem_end and gt_entity['end_char'] <= elem_end:
                    relative_start = gt_entity['start_char'] - elem_start
                    relative_end = gt_entity['end_char'] - elem_start
                    if element.text[relative_start:relative_end] == gt_entity['text']:
                        ground_truth_for_eval[element.id].append({
                            'text': gt_entity['text'],
                            'label': gt_entity['label'],
                            'start_char': relative_start,
                            'end_char': relative_end
                        })

        # 5. Evaluate predictions vs mapped GT for this document
        eval_results = evaluate_entity_detection(
            doc.elements,
            ground_truth_for_eval,
            label_map=KAGGLE_TO_DOCUGUARD_LABEL_MAP,
            match_strategy='overlap'
        )

        # 6. Aggregate counts
        for label, metrics in eval_results['per_class'].items():
            all_labels.add(label)
            tp = metrics['support'] * metrics['recall']
            fp = (tp / metrics['precision']) - tp if metrics['precision'] > 0 else (metrics['support'] * (1-metrics['recall']))
            fn = metrics['support'] - tp
            agg_tp[label] += tp
            agg_fp[label] += fp
            agg_fn[label] += fn

    # --- Calculate Final Aggregated Metrics --- #
    final_metrics = {'per_class': {}}
    total_tp = sum(agg_tp.values())
    total_fp = sum(agg_fp.values())
    total_fn = sum(agg_fn.values())
    overall_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    overall_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    overall_f1 = 2 * (overall_p * overall_r) / (overall_p + overall_r) if (overall_p + overall_r) > 0 else 0
    final_metrics['overall'] = {'precision': overall_p, 'recall': overall_r, 'f1': overall_f1, 'support': total_tp + total_fn}
    for label in sorted(list(all_labels)):
        tp = agg_tp[label]
        fp = agg_fp[label]
        fn = agg_fn[label]
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
        final_metrics['per_class'][label] = {'precision': p, 'recall': r, 'f1': f1, 'support': tp + fn}

    print("\n--- Aggregated Evaluation Results --- ")
    pprint.pprint(final_metrics)

def main():
    parser = argparse.ArgumentParser(description="Run DocuGuard evaluation on a dataset.")
    parser.add_argument("dataset_path", help="Path to the dataset file (e.g., data/pii_dataset.csv).")
    parser.add_argument("-n", "--num-entries", type=int, default=None, help="Limit evaluation to the first N entries.")
    args = parser.parse_args()

    run_kaggle_evaluation(args.dataset_path, args.num_entries)

if __name__ == "__main__":
    main() 