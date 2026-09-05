import os

import chromadb
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")


# PostgreSQL connection
engine = create_engine(DATABASE_URL)


# Local ChromaDB storage
chroma_client = chromadb.PersistentClient(
    path="rag/chroma_db"
)


# Collection for risk knowledge
collection = chroma_client.get_or_create_collection(
    name="risk_knowledge"
)


# Embedding model
embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def load_risk_rules_into_vector_db():
    """
    Read enabled risk rules from PostgreSQL,
    generate embeddings, and store them in ChromaDB.
    """

    query = text("""
        SELECT
            rule_code,
            title,
            category,
            description,
            severity,
            conditions,
            recommended_action
        FROM risk_rules
        WHERE enabled = TRUE
        ORDER BY id
    """)

    with engine.connect() as connection:
        rules = connection.execute(query).mappings().all()

    if not rules:
        print("No risk rules found in PostgreSQL.")
        return

    documents = []
    ids = []
    metadatas = []

    for rule in rules:

        document = (
            f"Rule: {rule['title']}. "
            f"Category: {rule['category']}. "
            f"Severity: {rule['severity']}. "
            f"Description: {rule['description']}. "
            f"Recommended action: {rule['recommended_action']}."
        )

        documents.append(document)

        ids.append(rule["rule_code"])

        metadatas.append({
            "rule_code": rule["rule_code"],
            "title": rule["title"],
            "category": rule["category"],
            "severity": rule["severity"],
            "recommended_action": rule["recommended_action"]
        })

    embeddings = embedding_model.encode(
        documents
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print(f"Loaded {len(rules)} risk rules into ChromaDB.")


def search_vector_store(query: str, top_k: int = 3):
    """
    Perform semantic similarity search in ChromaDB.
    """

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return results


if __name__ == "__main__":

    print("\nLoading PostgreSQL risk rules into ChromaDB...")

    load_risk_rules_into_vector_db()

    print("\nTesting semantic search...")

    test_queries = [
        "large payment",
        "many failed attempts",
        "too many transactions quickly",
        "brand new account making unusual payment",
        "payment from unusual country"
    ]

    for query in test_queries:

        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("=" * 60)

        results = search_vector_store(query)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            print(
                f"{metadata['rule_code']} | "
                f"{metadata['title']} | "
                f"distance={distance:.4f}"
            )