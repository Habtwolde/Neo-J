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
