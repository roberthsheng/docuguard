import csv
import ast
from typing import List, Dict, Any, Tuple

def load_kaggle_pii_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Loads the Kaggle PII dataset CSV.

    Parses string representations of lists into actual Python lists.
    """
    dataset = []
    print(f"Loading Kaggle PII dataset from: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['tokens'] = ast.literal_eval(row['tokens'])
                    row['trailing_whitespace'] = ast.literal_eval(row['trailing_whitespace'])
                    row['labels'] = ast.literal_eval(row['labels'])
                    if len(row['tokens']) == len(row['labels']) == len(row['trailing_whitespace']):
                        dataset.append(row)
                    else:
                        print(f"Warning: Skipping row for document {row.get('document', 'N/A')} due to mismatched list lengths.")
                except (ValueError, SyntaxError, TypeError) as e:
                    print(f"Warning: Skipping row for document {row.get('document', 'N/A')} due to parsing error: {e}")
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {file_path}")
        raise
    except Exception as e:
        print(f"Error loading dataset: {e}")
        raise
    print(f"Loaded {len(dataset)} entries from dataset.")
    return dataset

def convert_bio_to_offset_entities(tokens: List[str], labels: List[str], trailing_whitespace: List[bool], full_text: str) -> List[Dict[str, Any]]:
    """Converts BIO labeled tokens to character offset-based entity annotations.

    More robust offset calculation by iterating through full_text.
    """
    entities = []
    current_entity_tokens = []
    current_entity_label = None
    current_entity_start_char = -1
    current_char_idx = 0
    previous_token_end_char = 0 # Initialize to 0

    for i, (token, label, ws) in enumerate(zip(tokens, labels, trailing_whitespace)):
        start_char = -1
        search_start = current_char_idx
        while search_start < len(full_text) and full_text[search_start].isspace():
            search_start += 1

        try:
            start_char = full_text.index(token, search_start)
            current_char_idx = start_char + len(token)
        except ValueError:
            print(f"CRITICAL WARNING: Token '{token}' not found in full_text after offset {search_start}. Aborting entity conversion for this document.")
            return []

        end_char = current_char_idx
        bio_label = label
        entity_type = bio_label[2:] if len(bio_label) > 1 else None

        if bio_label.startswith('B-'):
            if current_entity_tokens:
                entity_text = full_text[current_entity_start_char : previous_token_end_char]
                entities.append({
                    'text': entity_text,
                    'label': current_entity_label,
                    'start_char': current_entity_start_char,
                    'end_char': previous_token_end_char
                })
            current_entity_tokens = [token]
            current_entity_label = entity_type
            current_entity_start_char = start_char

        elif bio_label.startswith('I-'):
            if current_entity_tokens and entity_type == current_entity_label:
                current_entity_tokens.append(token)
            else:
                if current_entity_tokens:
                    entity_text = full_text[current_entity_start_char : previous_token_end_char]
                    entities.append({
                        'text': entity_text,
                        'label': current_entity_label,
                        'start_char': current_entity_start_char,
                        'end_char': previous_token_end_char
                    })
                current_entity_tokens = []
                current_entity_label = None
                current_entity_start_char = -1

        else: # Outside tag (O)
            if current_entity_tokens:
                entity_text = full_text[current_entity_start_char : previous_token_end_char]
                entities.append({
                    'text': entity_text,
                    'label': current_entity_label,
                    'start_char': current_entity_start_char,
                    'end_char': previous_token_end_char
                })
            current_entity_tokens = []
            current_entity_label = None
            current_entity_start_char = -1

        previous_token_end_char = end_char

    if current_entity_tokens:
        entity_text = full_text[current_entity_start_char : previous_token_end_char]
        entities.append({
            'text': entity_text,
            'label': current_entity_label,
            'start_char': current_entity_start_char,
            'end_char': previous_token_end_char
        })

    return entities 