from rag.vector_store import (
    load_risk_rules_into_vector_db,
    search_vector_store
)

from rag.transaction_retriever import (
    get_transaction_context
)


def get_relevant_knowledge(
    query: str,
    transaction_id: str = None,
    top_k: int = 3
):
    """
    Retrieve relevant risk rules from ChromaDB
    and live transaction context from PostgreSQL.
    """

    # --------------------------------------------------
    # 1. Semantic retrieval from ChromaDB
    # --------------------------------------------------

    vector_results = search_vector_store(
        query=query,
        top_k=top_k
    )

    documents = vector_results.get(
        "documents",
        [[]]
    )[0]

    metadatas = vector_results.get(
        "metadatas",
        [[]]
    )[0]

    distances = vector_results.get(
        "distances",
        [[]]
    )[0]

    risk_rules = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        risk_rules.append({
            "id": metadata["rule_code"],
            "title": metadata["title"],
            "category": metadata["category"],
            "content": document,
            "severity": metadata["severity"],
            "recommended_action": metadata[
                "recommended_action"
            ],
            "similarity_distance": round(
                float(distance),
                4
            )
        })

    # --------------------------------------------------
    # 2. Retrieve live transaction context
    # --------------------------------------------------

    transaction_context = None

    if transaction_id:

        transaction_context = (
            get_transaction_context(
                transaction_id
            )
        )

    # --------------------------------------------------
    # 3. Return combined RAG context
    # --------------------------------------------------

    return {
        "risk_rules": risk_rules,
        "transaction_context": transaction_context
    }


if __name__ == "__main__":

    # Make sure PostgreSQL rules are synchronized
    # with ChromaDB.

    print("\nSyncing risk rules...")

    load_risk_rules_into_vector_db()

    print("\nTesting complete RAG retrieval...")

    result = get_relevant_knowledge(
        query=(
            "large payment with many failed "
            "attempts and unusual transaction activity"
        ),
        transaction_id="TXN00504"
    )

    print("\n" + "=" * 60)
    print("RETRIEVED RISK RULES")
    print("=" * 60)

    for rule in result["risk_rules"]:

        print(
            f"{rule['id']} | "
            f"{rule['title']} | "
            f"severity={rule['severity']} | "
            f"distance={rule['similarity_distance']}"
        )

    print("\n" + "=" * 60)
    print("LIVE TRANSACTION CONTEXT")
    print("=" * 60)

    context = result["transaction_context"]

    if context:

        print("\nCurrent Transaction:")
        print(context["transaction"])

        print("\nRecent History:")

        for transaction in context[
            "transaction_history"
        ]:
            print(transaction)

        print("\nPrevious Cases:")

        for case in context[
            "previous_cases"
        ]:
            print(case)