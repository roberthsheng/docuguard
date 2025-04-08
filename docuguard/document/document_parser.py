import os
import uuid
import re # Needed for list pattern matching
from typing import List, Dict, Tuple, Optional

# Updated pdfminer imports for layout analysis
# from pdfminer.high_level import extract_pages # Use extract_pages for layout
# Import more layout elements for detailed analysis
# from pdfminer.layout import LTTextLineHorizontal, LAParams, LTChar # Removed LTTextBoxHorizontal, added others
# from pdfminer.pdfdocument import PDFPasswordIncorrect, PDFSyntaxError

from .document_representation import Document, DocumentElement

# Helper function for simple title case check
def is_title_case(line: str) -> bool:
    return line.istitle() and not line.isupper()

def is_likely_heading(text: str, max_heading_len: int = 150, max_lines: int = 2) -> bool:
    """Heuristic for headings: few lines, title/all caps, not too long."""
    lines = text.split('\n')
    if not 0 < len(lines) <= max_lines:
        return False
    # Check combined length
    if len(text) > max_heading_len:
        return False
    # Require alpha characters
    if not any(c.isalpha() for c in text):
        return False
    # Check case (allow title case or all caps for the first line)
    first_line = lines[0]
    if first_line.isupper() or is_title_case(first_line):
        # Could add checks: no ending punctuation? Specific font attributes if available?
        return True
    return False

# Simple regex for common list markers
LIST_MARKER_PATTERN = re.compile(r'^\s*([\*\-\•\▪]|(?:\d+\.|[a-zA-Z][\.\)]))\s+')

def is_likely_list_item(text_line: str, prev_line_indent: Optional[float], current_indent: float, indent_tolerance: float = 1.0) -> bool:
    """Heuristic for list items: starts with marker, potentially indented."""
    if LIST_MARKER_PATTERN.match(text_line):
        return True
    # Check for simple indentation continuation (often seen in multi-line list items)
    if prev_line_indent is not None and abs(current_indent - prev_line_indent) < indent_tolerance and current_indent > indent_tolerance:
         # If indented similarly to previous line and not at margin
         # This is very basic and might misclassify indented paragraphs
         pass # Let's not classify based on pure indentation for now to avoid false positives
    return False

def segment_document(text: str) -> List[DocumentElement]:
    """Segments document text into elements (paragraphs, potential headings)."""
    elements = []
    raw_paragraphs = text.strip().split('\n\n')
    current_id = 0
    for para_text in raw_paragraphs:
        # Clean up individual lines within the paragraph block
        lines = [line.strip() for line in para_text.split('\n') if line.strip()]
        cleaned_para = '\n'.join(lines)

        if cleaned_para:
            elem_type = 'paragraph' # Default
            # Apply heading heuristic
            if is_likely_heading(cleaned_para):
                elem_type = 'heading'

            # TODO: Add list detection heuristics?

            element = DocumentElement(
                id=f"elem_{current_id}",
                text=cleaned_para,
                type=elem_type,
                bbox=None # Ensure bbox is None for text elements
            )
            elements.append(element)
            current_id += 1
    return elements

def extract_metadata(file_path: str) -> Dict:
    """Extracts basic metadata from the file."""
    metadata = {}
    try:
        metadata['filename'] = os.path.basename(file_path)
        metadata['filesize_bytes'] = os.path.getsize(file_path)
        # Add more metadata extraction if needed (e.g., creation/modification time)
    except Exception as e:
        print(f"Warning: Could not extract metadata for {file_path}: {e}")
    return metadata

def parse_text_file(file_path: str) -> Document:
    """Parses a plain text file into a Document object."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        doc_id = str(uuid.uuid4())
        elements = segment_document(text)
        metadata = extract_metadata(file_path)
        metadata['source_format'] = 'text'

        document = Document(
            id=doc_id,
            elements=elements,
            metadata=metadata
        )
        return document

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        raise
    except Exception as e:
        print(f"Error parsing text file {file_path}: {e}")
        raise

# def group_lines_into_elements(lines: List[LTTextLineHorizontal], max_vertical_gap_factor: float = 0.5) -> List[DocumentElement]:
#     """Groups lines into elements based mainly on vertical proximity."""
#     print(f"  [group_lines_into_elements] Received {len(lines)} lines.") # DEBUG
#     if not lines: return []
#     # ... (rest of the function commented out) ...
#     return [] # Return empty list if called

# def parse_pdf(file_path: str) -> Document:
#     """Parses a PDF using layout analysis, grouping lines into elements."""
#     # ... (function body commented out) ...
#     print(f"PDF Parsing is currently disabled.")
#     # Return an empty document or raise an error if PDF parsing is attempted
#     raise NotImplementedError("PDF parsing is currently disabled.")

class DocumentParser:
    """Wraps document parsing functions (TEXT ONLY)."""
    def __init__(self):
        pass

    def parse(self, file_path: str) -> Document:
        """Determines file type and calls the appropriate parser.

        Treats files with unknown extensions or no extension (like Enron emails)
        as plain text. PDF is currently unsupported.
        """
        _, ext = os.path.splitext(file_path.lower())

        # if ext == '.pdf':
            # PDF parsing disabled
            # raise ValueError("PDF parsing is currently disabled.")
            # # return parse_pdf(file_path)
        if ext == '.txt' or not ext or ext == '.': # Handle text-like files
            return parse_text_file(file_path)
        else:
            # Keep the explicit error for other known-but-unsupported types
            raise ValueError(f"Unsupported file format: {ext}. Only text files (.txt, no ext, .) are currently supported.") 