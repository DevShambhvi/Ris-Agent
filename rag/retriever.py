import json


with open("rag/knowledge_base.json", "r") as file:
    knowledge = json.load(file)


def search_knowledge(query, top_k=3):
    query_words = set(query.lower().split())

    results = []

    for item in knowledge:
        text = (
            item["title"] + " " +
            item["category"] + " " +
            item["content"]
        ).lower()

        score = 0

        for word in query_words:
            if word in item["title"].lower():
                score += 3
            elif word in item["category"].lower():
                score += 2
            elif word in text:
                score += 1

        if score > 0:
            results.append((score, item))

    results.sort(key=lambda x: x[0], reverse=True)

    return [item for score, item in results[:top_k]]


if __name__ == "__main__":
    results = search_knowledge(
        "many failed payment attempts"
    )

    for result in results:
        print(f"{result['id']}: {result['title']}")