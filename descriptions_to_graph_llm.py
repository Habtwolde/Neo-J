# descriptions_to_graph_llm.py
#
# Excel (one description column) -> Neo4j graph using LLM extraction.
#
# - Uses llama3.1:8b via Ollama (http://localhost:11434)
# - Asks the model to output strict JSON: entities + relationships
# - Upserts nodes and relationships into Neo4j

from neo4j import GraphDatabase
from pathlib import Path
import pandas as pd
import yaml
import requests
import json
from typing import Optional, Dict, Any, List

# === BASIC CONFIG ============================================================

NEO4J_URI  = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "neo4j123"

EXCEL_PATH  = Path("descriptions_only.xlsx")
RULES_PATH  = Path("relation_rules.yml")
SOURCE_NAME = EXCEL_PATH.name

# Ollama config
OLLAMA_URL   = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.1:8b"

# === HELPERS =================================================================

def clean_str(v) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    s = str(v).strip()
    return s if s else None


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing rules/config file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


CONFIG = load_config(RULES_PATH)
RECORD_CFG = CONFIG.get("record", {})
RECORD_LABEL = RECORD_CFG.get("label", "Record")
RECORD_ID_PREFIX = RECORD_CFG.get("id_prefix", "DESC_")

ENTITY_CONFIG = CONFIG.get("entities", {})
REL_CONFIG    = CONFIG.get("relationships", {})

# Make sure there is a DEFAULT block
ENTITY_CONFIG.setdefault("DEFAULT", {"labels": ["Entity"]})
REL_CONFIG.setdefault("DEFAULT", {"type": "RELATED_TO"})

# === NEO4J DRIVER ============================================================

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def write(cypher: str, params: Optional[dict] = None):
    with driver.session() as s:
        s.run(cypher, **(params or {}))


def read(cypher: str, params: Optional[dict] = None):
    with driver.session() as s:
        return s.run(cypher, **(params or {})).data()


# === SCHEMA ==================================================================

def ensure_schema():
    # Record uniqueness
    write(f"""
    CREATE CONSTRAINT IF NOT EXISTS
    FOR (r:{RECORD_LABEL})
    REQUIRE r.record_id IS UNIQUE
    """)

    # Entity uniqueness by (entity_type, canonical_text)
    write("""
    CREATE CONSTRAINT IF NOT EXISTS
    FOR (e:Entity)
    REQUIRE (e.entity_type, e.canonical_text) IS UNIQUE
    """)


# === EXCEL LOADER ============================================================

def load_descriptions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    df = pd.read_excel(path)

    # accept either 'description' or 'Description'
    cols_lower = {c.lower(): c for c in df.columns}
    if "description" not in cols_lower:
        raise ValueError("Excel must contain a column named 'description' (any case).")
    desc_col = cols_lower["description"]

    df = df.dropna(subset=[desc_col]).copy()
    df.rename(columns={desc_col: "description"}, inplace=True)
    print(f"Loaded {len(df)} descriptions from {path}")
    return df


# === LLM EXTRACTION LAYER ====================================================

SYSTEM_PROMPT = """
You are an information extraction engine that converts free-text descriptions
about people, organizations, locations, travel, and documents into a structured
graph representation.

For EACH input description, you MUST output ONLY a single valid JSON object,
with this exact structure:

{
  "entities": [
    {
      "id": "p1",
      "type": "PERSON",
      "name": "Full name here",
      "properties": {
        "dob": "YYYY-MM-DD or text if unknown",
        "citizenship": "country",
        "place_of_birth": "city or place",
        "residence_location": "current residence city or place",
        "phone_number": "string",
        "passport_number": "string",
        "flight_number": "string",
        "departure_location": "place",
        "arrival_location": "place",
        "arrest_location": "place",
        "arrival_date": "date string",
        "departure_date": "date string",
        "date_generic": "any other relevant date",
        "money": "amount + currency if present",
        "license_plate": "string",
        "drivers_license": "string",
        "role": "job title or role",
        "notes": "any extra useful notes"
      }
    },
    {
      "id": "o1",
      "type": "ORG",
      "name": "Organization name",
      "properties": {
        "address": "address or location",
        "sector": "type of organization",
        "notes": "optional"
      }
    },
    {
      "id": "l1",
      "type": "LOCATION",
      "name": "Location name",
      "properties": {
        "country": "if you can infer",
        "notes": "optional"
      }
    }
  ],
  "relationships": [
    {
      "type": "WORKS_FOR",
      "source": "p1",
      "target": "o1",
      "properties": {
        "role": "job title if known",
        "confidence": 0.95
      }
    },
    {
      "type": "DEPARTED_FROM",
      "source": "p1",
      "target": "l1",
      "properties": {
        "date": "departure_date if known",
        "flight_number": "if known",
        "confidence": 0.9
      }
    }
  ]
}

Rules:
- You can omit any fields that are not present in the text.
- "type" should be one of: PERSON, ORG, ORGANIZATION, GPE, LOCATION, MONEY, DATE, DOCUMENT, OTHER.
  (Prefer PERSON / ORG / LOCATION / GPE when possible.)
- "id" must be unique within the JSON (p1, p2, o1, l1, etc.).
- Use "properties" as a flat key-value map.
- If nothing can be extracted, output {"entities": [], "relationships": []}.
- DO NOT include explanations, comments, or markdown. Only raw JSON.
""".strip()


def call_ollama(description: str) -> Dict[str, Any]:
    """
    Call llama3.1:8b via Ollama /api/chat and return parsed JSON
    with keys: entities, relationships.
    """
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()

    content = data.get("message", {}).get("content", "").strip()

    # Clean possible ```json ... ``` wrappers
    if content.startswith("```"):
        # strip first and last fences
        content = content.strip("`")
        # remove language identifier if present
        if content.lower().startswith("json"):
            content = content[4:].strip()

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try to find JSON object substring
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(content[start : end + 1])
        else:
            raise

    # Normalize
    entities = parsed.get("entities", []) or []
    relationships = parsed.get("relationships", []) or []
    return {"entities": entities, "relationships": relationships}


# === GRAPH UPSERTS ===========================================================

def upsert_record(record_id: str, row_index: int, description: str):
    params = {
        "record_id": record_id,
        "row_index": row_index,
        "description": description,
        "source_file": SOURCE_NAME,
    }
    cypher = f"""
    MERGE (r:{RECORD_LABEL} {{record_id: $record_id}})
    ON CREATE SET
      r.description = $description,
      r.row_index   = $row_index,
      r.source_file = $source_file,
      r.created_at  = datetime(),
      r.updated_at  = datetime()
    ON MATCH SET
      r.description = $description,
      r.updated_at  = datetime()
    """
    write(cypher, params)


def get_entity_labels(entity_type: str) -> List[str]:
    et = (entity_type or "DEFAULT").upper()
    cfg = ENTITY_CONFIG.get(et, ENTITY_CONFIG["DEFAULT"])
    labels = cfg.get("labels", ["Entity"])
    # Guarantee "Entity" always present
    if "Entity" not in labels:
        labels = ["Entity"] + [l for l in labels if l != "Entity"]
    return labels


def upsert_entity(entity: Dict[str, Any]) -> Dict[str, str]:
    """
    Upsert an entity node and return its key:
      {"entity_type": <str>, "canonical_text": <str>}
    """
    e_type = clean_str(entity.get("type", "OTHER")) or "OTHER"
    name = clean_str(entity.get("name")) or clean_str(entity.get("canonical_text"))
    if not name:
        # Fallback if LLM did not give a name
        name = f"{e_type}_{entity.get('id', 'UNKNOWN')}"

    canonical_text = name
    props = entity.get("properties") or {}
    if not isinstance(props, dict):
        props = {}

    # Ensure "name" is present as a property
    props = dict(props)
    if "name" not in props:
        props["name"] = name

    labels = get_entity_labels(e_type)
    label_str = ":".join(labels)

    params = {
        "entity_type": e_type.upper(),
        "canonical_text": canonical_text,
        "props": props,
    }

    cypher = f"""
    MERGE (e:{label_str} {{entity_type: $entity_type, canonical_text: $canonical_text}})
    ON CREATE SET
      e.created_at = datetime(),
      e.updated_at = datetime()
    SET e += $props,
        e.updated_at = datetime()
    """
    write(cypher, params)

    return {"entity_type": params["entity_type"], "canonical_text": canonical_text}


def create_relationship(rel: Dict[str, Any], entity_key_by_id: Dict[str, Dict[str, str]]):
    src_id = rel.get("source")
    tgt_id = rel.get("target")
    if not src_id or not tgt_id:
        return
    if src_id not in entity_key_by_id or tgt_id not in entity_key_by_id:
        return

    src_key = entity_key_by_id[src_id]
    tgt_key = entity_key_by_id[tgt_id]

    r_type = clean_str(rel.get("type", "RELATED_TO")) or "RELATED_TO"
    r_type_upper = r_type.upper()
    cfg = REL_CONFIG.get(r_type_upper, REL_CONFIG["DEFAULT"])
    neo4j_type = cfg.get("type", r_type_upper)

    props = rel.get("properties") or {}
    if not isinstance(props, dict):
        props = {}
    params = {
        "src_entity_type": src_key["entity_type"],
        "src_canonical": src_key["canonical_text"],
        "tgt_entity_type": tgt_key["entity_type"],
        "tgt_canonical": tgt_key["canonical_text"],
        "props": props,
    }

    cypher = f"""
    MATCH (s:Entity {{entity_type: $src_entity_type, canonical_text: $src_canonical}})
    MATCH (t:Entity {{entity_type: $tgt_entity_type, canonical_text: $tgt_canonical}})
    MERGE (s)-[r:{neo4j_type}]->(t)
    ON CREATE SET
      r.created_at = datetime(),
      r.updated_at = datetime()
    SET r += $props,
        r.updated_at = datetime()
    """
    write(cypher, params)


def connect_record_to_persons(record_id: str, entity_key_by_id: Dict[str, Dict[str, str]]):
    """
    Simple heuristic: connect the record to all PERSON entities with DESCRIBES.
    """
    for key in entity_key_by_id.values():
        if key["entity_type"].upper() != "PERSON":
            continue
        params = {
            "record_id": record_id,
            "entity_type": key["entity_type"],
            "canonical_text": key["canonical_text"],
        }
        cypher = f"""
        MATCH (r:{RECORD_LABEL} {{record_id: $record_id}})
        MATCH (p:Entity {{entity_type: $entity_type, canonical_text: $canonical_text}})
        MERGE (r)-[:DESCRIBES]->(p)
        """
        write(cypher, params)


# === MAIN PIPELINE ===========================================================

def process_row(idx: int, description: str):
    record_id = f"{RECORD_ID_PREFIX}{idx + 1}"
    print(f"\n=== Row {idx + 1} -> {record_id} ===")
    print("Description:", description[:200].replace("\n", " "), "..." if len(description) > 200 else "")

    upsert_record(record_id, idx + 1, description)

    try:
        llm_graph = call_ollama(description)
    except Exception as e:
        print(f"  [LLM ERROR] {e}")
        return

    entities = llm_graph.get("entities", []) or []
    relationships = llm_graph.get("relationships", []) or []

    print(f"  Entities extracted: {len(entities)}")
    print(f"  Relationships extracted: {len(relationships)}")

    # Upsert entities
    entity_key_by_id: Dict[str, Dict[str, str]] = {}
    for ent in entities:
        ent_id = ent.get("id")
        if not ent_id:
            continue
        key = upsert_entity(ent)
        entity_key_by_id[ent_id] = key

    # Connect record -> person(s)
    connect_record_to_persons(record_id, entity_key_by_id)

    # Create relationships
    for rel in relationships:
        create_relationship(rel, entity_key_by_id)


def main():
    print("=== Ensuring schema ===")
    ensure_schema()

    print("=== Loading Excel ===")
    df = load_descriptions(EXCEL_PATH)

    print("=== Processing rows with LLM extraction ===")
    for idx, row in df.iterrows():
        description = clean_str(row["description"])
        if not description:
            continue
        process_row(idx, description)

    print("\n=== Sample graph view ===")
    rows = read("""
    MATCH (p:Entity:Person)-[r]->(x)
    RETURN p.name AS person,
           type(r) AS rel,
           labels(x) AS target_labels,
           x.name AS target
    LIMIT 50
    """)
    for r in rows:
        print(r)


if __name__ == "__main__":
    try:
        main()
    finally:
        driver.close()
