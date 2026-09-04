from rag.retriever import search_knowledge


def get_relevant_knowledge(query):
    results = search_knowledge(query)

    return [
        {
            "id": item["id"],
            "title": item["title"],
            "category": item["category"],
            "content": item["content"]
        }
        for item in results
    ]


if __name__ == "__main__":

    queries = [
        "multiple transactions in one hour",
        "many failed payment attempts",
        "unusually large transaction"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        print("-" * 50)

        results = get_relevant_knowledge(query)

        for item in results:
            print(f"{item['id']}: {item['title']}")