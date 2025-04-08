import argparse
import sys
import os

# Ensure the docuguard package is discoverable
# Add the project root to the Python path if the script is run directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from docuguard.document.document_parser import DocumentParser
    from docuguard.entity.entity_recognizer import EntityRecognizer
except ImportError as e:
    print(f"Error importing DocuGuard modules: {e}")
    print("Please ensure the script is run from the project root using 'python -m scripts.process_document' or that the project root is in PYTHONPATH.")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Parse a TEXT document and detect entities using DocuGuard.")
    parser.add_argument("file_path", help="Path to the TEXT document file (.txt, no extension, .) to process.")
    args = parser.parse_args()

    if not os.path.exists(args.file_path):
        print(f"Error: File not found at {args.file_path}")
        sys.exit(1)

    # Check for PDF extension explicitly
    _, ext = os.path.splitext(args.file_path.lower())
    if ext == '.pdf':
        print(f"Error: PDF file processing is currently disabled ('{args.file_path}').")
        print("Please provide a text-based file.")
        sys.exit(1)

    print("---")
    print(f"Processing document: {args.file_path}")
    print("---")

    try:
        # 1. Initialize components
        # EntityRecognizer will load the default spaCy model (en_core_web_md)
        parser_component = DocumentParser()
        recognizer_component = EntityRecognizer()

        # 2. Parse the document
        document = parser_component.parse(args.file_path)
        print(f"Parsed document ID: {document.id}")
        print(f"Source Format: {document.metadata.get('source_format', 'N/A')}")
        print(f"Number of elements found: {len(document.elements)}")
        print("---")

        # 3. Detect entities
        recognizer_component.detect_entities(document)
        print("---")

        # 4. Display results (elements with entities)
        print("Elements containing detected entities:")
        found_any = False
        for i, element in enumerate(document.elements):
            if element.entities:
                found_any = True
                print(f"\nElement {i} (ID: {element.id}, Type: {element.type}, Page: {element.metadata.get('page_number', 'N/A')}):")
                print(f"  Text: '{element.text[:100]}...'" if len(element.text) > 100 else f"  Text: '{element.text}'")
                print("  Entities Found:")
                for entity in element.entities:
                    print(f"    - '{entity.text}' ({entity.label}, Score: {entity.base_risk_score:.2f}, Source: {entity.metadata.get('source', 'N/A')})")

        if not found_any:
            print("(No entities detected in any element)")

    except ValueError as e:
        print(f"Error processing document: {e}")
        sys.exit(1)
    except Exception as e:
        # Catch potential errors during parsing or entity recognition
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 