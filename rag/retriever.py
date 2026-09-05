from rag.db_retriever import search_risk_rules


def search_knowledge(query: str, top_k: int = 3):
    """
    Retrieve relevant risk knowledge from PostgreSQL.
    """

    rules = search_risk_rules(
        query=query,
        top_k=top_k
    )

    return [
        {
            "id": rule["rule_code"],
            "title": rule["title"],
            "category": rule["category"],
            "content": rule["description"],
            "severity": rule["severity"],
            "conditions": rule["conditions"],
            "recommended_action": rule["recommended_action"]
        }
        for rule in rules
    ]


if __name__ == "__main__":

    queries = [
        "velocity",
        "payment failure",
        "large transaction",
        "new account",
        "geographic anomaly"
    ]

    for query in queries:

        print("\n" + "=" * 60)
        print(f"Query: {query}")
        print("=" * 60)

        results = search_knowledge(query)

        for result in results:
            print(
                f"{result['id']} | "
                f"{result['title']} | "
                f"{result['severity']}"
            )