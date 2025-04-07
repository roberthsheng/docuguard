# DocuGuard Project Specification

## Project Overview

DocuGuard is a privacy-aware document scoring and redaction system that quantifies privacy risk in documents and adaptively anonymizes sensitive content while preserving document utility. The system uses a graph-based approach to model information flow and context-sensitive risk propagation.

## Core Components

The system is divided into the following major components:

1. Document Processing Module
2. Entity Recognition Engine
3. Risk Scoring System
4. Graph-Based Risk Propagation
5. Anonymization Engine
6. User Interface
7. Evaluation Framework

## Task Assignments

### Robert: Document Processing & Entity Recognition

#### 1. Document Processing Module

**Description:** This module handles document parsing, text extraction, and structural analysis to prepare documents for privacy assessment.

**Requirements:**
- Support for text files (.txt) and PDFs if time permits
- Extract and preserve document structure (paragraphs, sections)
- Basic metadata extraction capabilities
- Segmentation of documents into elements for analysis

**Functions/Classes:**
- `DocumentParser`: Main class for document parsing
- `parse_text_file(file_path)`: Parse plain text files
- `parse_pdf(file_path)`: Parse PDF files (if time permits)
- `segment_document(text)`: Divide document into logical elements
- `extract_metadata(file_path)`: Extract available document metadata

**Deliverables:**
- `document_parser.py`: Module for document parsing
- `document_representation.py`: Data structures for document representation

#### 2. Entity Recognition Engine

**Description:** This module identifies and classifies potentially sensitive information within document elements.

**Requirements:**
- Detect common PII types using pattern matching (emails, phone numbers, SSNs, etc.)
- Leverage pre-trained NER models for entity detection
- Classify entities into sensitivity categories (explicit identifiers, quasi-identifiers)
- Assign base risk scores to different entity types

**Functions/Classes:**
- `EntityRecognizer`: Main class for entity detection
- `detect_entities(text)`: Identify entities in text using NER and patterns
- `classify_entity(entity, context)`: Determine entity sensitivity type
- `assign_base_risk(entity_type)`: Assign initial risk score to entity

**Deliverables:**
- `entity_recognizer.py`: Entity detection and classification module
- `patterns.py`: Regular expressions and rules for identifying PII
- `entity_risk.py`: Base risk score assignment logic

### Reed: Risk Scoring & Anonymization

#### 3. Risk Scoring System

**Description:** This module assesses the local risk of document elements based on their content and immediate context.

**Requirements:**
- Compute local risk scores for elements based on contained entities
- Analyze contextual windows around elements
- Establish semantic relationships between elements
- Generate initial element-level risk scores

**Functions/Classes:**
- `RiskScorer`: Main class for element risk assessment
- `compute_local_risk(element, entities)`: Calculate risk based on contained entities
- `analyze_context(element, document)`: Assess element's contextual risk
- `compute_semantic_relationship(element1, element2)`: Measure semantic similarity

**Deliverables:**
- `risk_scorer.py`: Local risk assessment module
- `context_analyzer.py`: Context window analysis functions

#### 4. Graph-Based Risk Propagation

**Description:** This module constructs and processes the information flow graph to propagate risk between connected elements.

**Requirements:**
- Build graph representation from document elements
- Weight edges based on semantic and structural relationships
- Implement iterative risk propagation algorithm
- Calculate overall document risk score

**Functions/Classes:**
- `GraphBuilder`: Class for constructing the information flow graph
- `build_graph(document)`: Create graph from document elements
- `calculate_edge_weights(element1, element2)`: Determine connection strength
- `propagate_risk(graph, iterations=3)`: Run risk propagation algorithm
- `calculate_document_risk(graph)`: Compute overall document risk score

**Deliverables:**
- `graph_builder.py`: Graph construction module
- `risk_propagation.py`: Risk propagation algorithm
- `document_risk.py`: Document-level risk scoring

#### 5. Anonymization Engine

**Description:** This module transforms documents to reduce privacy risk while preserving utility.

**Requirements:**
- Implement various anonymization operations (removal, masking, generalization)
- Select appropriate operations based on element type and context
- Iteratively anonymize elements until target risk threshold is met
- Maintain document coherence during transformation

**Functions/Classes:**
- `AnonymizationEngine`: Main class for document anonymization
- `anonymize_document(document, threshold)`: Top-level anonymization function
- `select_anonymization_strategy(element, risk)`: Choose appropriate operation
- `apply_anonymization(element, strategy)`: Execute anonymization operation
- `reevaluate_risk(document)`: Recalculate risk after anonymization steps

**Operations:**
- `remove_element(element)`: Complete removal of element
- `mask_entity(entity, mask_char='*')`: Replace entity with mask characters
- `generalize_entity(entity, level)`: Replace with more general category
- `pseudonymize_entity(entity, type)`: Replace with consistent substitute

**Deliverables:**
- `anonymization_ops.py`: Implementation of anonymization operations
- `anonymization_engine.py`: Main anonymization logic

### Shared Responsibilities

#### 6. User Interface

**Description:** This component provides a command-line interface for interacting with the system.

**Requirements:**
- Simple CLI for document input and configuration
- Display risk scores with highlighting of sensitive elements
- Show before/after comparisons of anonymized documents
- Configuration options for risk thresholds and anonymization preferences

**Functions:**
- `process_arguments()`: Parse command-line arguments
- `display_risk_scores(document)`: Show element risk scores
- `highlight_sensitive_elements(document)`: Visualize sensitive content
- `display_anonymized_document(original, anonymized)`: Show comparison

**Deliverables:**
- `docuguard_cli.py`: Command-line interface

#### 7. Evaluation Framework

**Description:** This module enables assessment of the system's performance across different datasets.

**Requirements:**
- Scripts for evaluating on selected datasets
- Metrics calculation for entity detection and risk assessment
- Measurement of utility preservation
- Visualization of privacy-utility tradeoffs

**Functions:**
- `evaluate_entity_detection(predictions, ground_truth)`: Calculate precision, recall, F1
- `evaluate_risk_scoring(document, ground_truth)`: Assess risk score accuracy
- `measure_utility(original, anonymized)`: Quantify document utility preservation
- `plot_privacy_utility_tradeoff(results)`: Generate visualization

**Deliverables:**
- `evaluation.py`: Evaluation functions and metrics
- `visualize.py`: Visualization utilities

## Technical Specifications

### Environment Setup

```
# Create virtual environment
python -m venv docuguard-env
source docuguard-env/bin/activate  # On Windows: docuguard-env\Scripts\activate

# Install dependencies
pip install spacy scikit-learn sentence-transformers numpy pandas matplotlib pdfminer.six
python -m spacy download en_core_web_sm
```

### Project Structure

```
docuguard/
│
├── data/                          # Sample datasets
│   ├── enron/                     # Enron email samples
│   └── i2b2/                      # i2b2 samples (if available)
│
├── docuguard/                     # Main package
│   ├── __init__.py
│   ├── document/                  # Document processing
│   │   ├── __init__.py
│   │   ├── document_parser.py
│   │   └── document_representation.py
│   │
│   ├── entity/                    # Entity recognition
│   │   ├── __init__.py
│   │   ├── entity_recognizer.py
│   │   ├── patterns.py
│   │   └── entity_risk.py
│   │
│   ├── risk/                      # Risk scoring
│   │   ├── __init__.py
│   │   ├── risk_scorer.py
│   │   ├── context_analyzer.py
│   │   ├── graph_builder.py
│   │   ├── risk_propagation.py
│   │   └── document_risk.py
│   │
│   ├── anonymization/             # Anonymization
│   │   ├── __init__.py
│   │   ├── anonymization_ops.py
│   │   └── anonymization_engine.py
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       └── helpers.py
│
├── evaluation/                    # Evaluation framework
│   ├── __init__.py
│   ├── evaluation.py
│   └── visualize.py
│
├── scripts/                       # CLI and scripts
│   ├── docuguard_cli.py
│   └── run_evaluation.py
│
├── tests/                         # Unit tests
│   ├── test_document_parser.py
│   ├── test_entity_recognition.py
│   └── ...
│
├── README.md
├── requirements.txt
└── setup.py
```

### Data Flow

1. **Input**: Document file (.txt, .pdf)
2. **Document Processing**: Parse and segment document
3. **Entity Recognition**: Identify and classify sensitive information
4. **Risk Scoring**: Calculate local risk scores
5. **Graph Construction**: Build information flow graph
6. **Risk Propagation**: Propagate risk through the graph
7. **Document Risk Calculation**: Compute overall risk score
8. **Anonymization**: Apply transformations to meet target threshold
9. **Output**: Anonymized document and risk assessment report

## Implementation Guidelines

### Performance Considerations

- Use multiprocessing for parallel entity detection when possible
- Implement caching for expensive operations (e.g., semantic similarity)
- Limit graph propagation to 2-3 iterations for reasonable performance
- Use efficient data structures (numpy arrays for numerical operations)

### Testing Strategy

- Unit tests for individual components
- Integration tests for component interactions
- Sample documents with known sensitive information for validation
- Comparison against baseline approaches (rule-based detection)

## Timeline and Milestones

### Day 1-2: Core Components
- Set up project structure and repositories
- Implement document processing and entity recognition
- Build basic risk scoring functionality

### Day 3-4: Advanced Features
- Implement graph construction and risk propagation
- Develop anonymization operations and strategy
- Create basic CLI interface

### Day 5-6: Integration & Testing
- Integrate all components
- Test on sample datasets
- Fix bugs and optimize performance

### Day 7: Evaluation & Documentation
- Evaluate system performance
- Generate visualizations of results
- Complete documentation and prepare demonstration

## Minimum Viable Product (MVP)

The MVP should include:
1. Basic document parsing (text files)
2. Pattern-based and NER-based entity recognition
3. Simple risk scoring based on entity types
4. Basic graph construction and risk propagation
5. Key anonymization operations (removal, masking)
6. Command-line interface
7. Evaluation on a small subset of email data

## Future Enhancements (Post-Week)

1. Support for additional document formats (Word, HTML)
2. More sophisticated semantic analysis
3. Advanced anonymization techniques (synthetic data generation)
4. GUI for interactive document analysis
5. Expanded evaluation on multiple datasets
6. Performance optimizations for larger documents

## Resources

### Datasets
- Enron Email Dataset (sample): https://www.cs.cmu.edu/~enron/
- i2b2 de-identification dataset (if available): https://portal.dbmi.hms.harvard.edu/projects/n2c2-nlp/

### Libraries
- spaCy: https://spacy.io/
- Sentence Transformers: https://www.sbert.net/
- scikit-learn: https://scikit-learn.org/
- PDFMiner: https://github.com/pdfminer/pdfminer.six

## Contact Information

- Person A: [Your Email]
- Person B: [Partner's Email]
- Repository: [GitHub Repository URL]