import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL)


def search_risk_rules(query: str, top_k: int = 3):
    """
    Dynamically retrieves relevant enabled risk rules from PostgreSQL.
    """

    search_query = text("""
        SELECT
            id,
            rule_code,
            title,
            category,
            description,
            severity,
            conditions,
            recommended_action
        FROM risk_rules
        WHERE enabled = TRUE
          AND (
              LOWER(title) LIKE LOWER(:query)
              OR LOWER(category) LIKE LOWER(:query)
              OR LOWER(description) LIKE LOWER(:query)
          )
        ORDER BY
            CASE
                WHEN LOWER(title) LIKE LOWER(:query) THEN 1
                WHEN LOWER(category) LIKE LOWER(:query) THEN 2
                ELSE 3
            END,
            severity DESC
        LIMIT :top_k
    """)

    search_pattern = f"%{query}%"

    with engine.connect() as connection:
        results = connection.execute(
            search_query,
            {
                "query": search_pattern,
                "top_k": top_k
            }
        ).mappings().all()

    return [dict(row) for row in results]


if __name__ == "__main__":

    queries = [
        "velocity",
        "payment failure",
        "amount",
        "account",
        "location"
    ]

    for query in queries:

        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("=" * 60)

        results = search_risk_rules(query)

        for rule in results:
            print(
                f"{rule['rule_code']} | "
                f"{rule['title']} | "
                f"{rule['severity']}"
            )