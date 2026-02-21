<<<<<<< HEAD
# 🧠 Excel → Neo4j Knowledge Graph Builder (LLM‑Powered)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)]()
[![Neo4j](https://img.shields.io/badge/Database-Neo4j-green.svg)]()
[![LLM](https://img.shields.io/badge/LLM-Ollama%20Local-orange.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)]()
[![Status](https://img.shields.io/badge/Project-Active-success.svg)]()

Convert messy, real‑world textual descriptions into a structured
knowledge graph using a **local Large Language Model** and **Neo4j graph
database**.

------------------------------------------------------------------------

## 🚀 What This Project Does

This project reads free‑text descriptions from Excel and automatically
builds a connected knowledge graph:

    Unstructured Text → LLM Understanding → Entities → Relationships → Graph Database

You get structured, queryable intelligence from raw human language.

------------------------------------------------------------------------

## 🏗️ Architecture

    ┌──────────────────┐
    │  Excel Dataset   │
    │ descriptions.xlsx│
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │   Python Engine  │
    │  Data Pipeline   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │   Local LLM      │
    │   Ollama Model   │
    │  JSON Extraction │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Validation Layer │
    │ Deduplication    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │     Neo4j DB     │
    │ Knowledge Graph  │
    └──────────────────┘

------------------------------------------------------------------------

## 📸 Screenshots (Placeholders)

> Replace these with real screenshots later --- GitHub ranking improves
> heavily with visuals.

### Graph Visualization

![Graph Preview](docs/images/graph_preview.png)

### Data Extraction Logs

![Logs](docs/images/logs.png)

### Neo4j Browser Query Result

![Query](docs/images/query.png)

------------------------------------------------------------------------

## ✨ Features

-   Fully automated entity & relationship extraction
-   Works offline (local LLM --- privacy safe)
-   Configurable ontology via YAML
-   Deduplicated graph nodes
-   Idempotent upserts
-   Handles noisy real‑world data
-   Extendable schema mapping
-   Production‑pipeline friendly

------------------------------------------------------------------------

## 📂 Project Structure

    .
    ├── descriptions_to_graph_llm.py
    ├── relation_rules.yml
    ├── descriptions_only.xlsx
    ├── requirements.txt
    ├── docs/
    │   └── images/
    │       ├── graph_preview.png
    │       ├── logs.png
    │       └── query.png
    └── README.md

------------------------------------------------------------------------

## ⚙️ Installation

### 1) Clone

    git clone <repo-url>
    cd graph-builder

### 2) Environment

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

### 3) Install LLM

    ollama pull llama3.1:8b

------------------------------------------------------------------------

## 🔧 Configuration

Create `.env`

    NEO4J_URI=neo4j://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASS=password
    OLLAMA_URL=http://localhost:11434/api/chat
    OLLAMA_MODEL=llama3.1:8b
    EXCEL_PATH=descriptions_only.xlsx
    RULES_PATH=relation_rules.yml

------------------------------------------------------------------------

## ▶️ Run

    python descriptions_to_graph_llm.py

Output: - Graph nodes created - Relationships linked - Records traceable
to source text

------------------------------------------------------------------------

## 🔍 Example Cypher Queries

Find all people:

    MATCH (p:Person) RETURN p LIMIT 25;

Find relationships:

    MATCH (a)-[r]->(b) RETURN a,r,b LIMIT 50;

Trace source text:

    MATCH (r:Record)-[:DESCRIBES]->(p:Person)
    RETURN r.description, p.name

------------------------------------------------------------------------

## 🧠 SEO Keywords

knowledge graph generation, LLM extraction pipeline, Neo4j NLP, entity
relationship extraction, graph database automation, AI data structuring,
local LLM processing, semantic graph builder, unstructured text mining,
Python graph ETL, Ollama AI projects

------------------------------------------------------------------------

## 📈 Ideal Use Cases

-   Investigation systems
-   Compliance monitoring
-   Research intelligence
-   CRM enrichment
-   Document mining
-   Case management
-   Data lineage mapping

------------------------------------------------------------------------

## 🛣️ Roadmap

-   [ ] Parallel processing
-   [ ] Docker deployment
-   [ ] UI visualization
-   [ ] Incremental ingestion
-   [ ] Confidence scoring
-   [ ] Embedding similarity linking

------------------------------------------------------------------------

## 🤝 Contributing

PRs welcome --- focus on:

-   extraction accuracy
-   ontology mapping
-   graph performance
-   validation robustness

------------------------------------------------------------------------

## 📜 License

MIT
=======
# Excel → Neo4j Graph (LLM extraction)
**Convert free-text descriptions in an Excel file into a Neo4j graph using an LLM.**

This project reads descriptions from `descriptions_only.xlsx`, extracts entities & relationships using a local Ollama LLM (prompted to return strict JSON), and upserts those entities/relationships into Neo4j.

> Primary script: `descriptions_to_graph_llm.py`. (Inspected for this README.) :contentReference[oaicite:2]{index=2}

---

## Features
- Per-row LLM extraction → entities + relationships.
- Upserts entities and relationships to Neo4j with configurable label/type mappings via `relation_rules.yml`.
- Ensures basic Neo4j schema constraints (unique record id, unique `(entity_type, canonical_text)`).
- Simple heuristic to link `Record` → `Person` nodes.

---

## Quick start (development)

### 1) Prerequisites
- Python 3.10+ (use pyenv / venv)
- Neo4j (desktop or server) accessible from the machine
- Ollama running locally with the `llama3.1:8b` model (or change model/url in env)
- The repository files:
  - `descriptions_to_graph_llm.py` (main script). :contentReference[oaicite:3]{index=3}
  - `descriptions_only.xlsx` (input)
  - `relation_rules.yml` (label/type mapping)

### 2) Install dependencies
Create a virtual environment and install dependencies; add a `requirements.txt` file (example below).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
>>>>>>> f2ebdb7b52c7487228cab5382a5339e364d2a1a0
