import json

with open("rag/knowledge_base.json", "r") as file:
    knowledge = json.load(file)

print(f"Loaded {len(knowledge)} knowledge entries.")

for item in knowledge:
    print(f"{item['id']}: {item['title']}")