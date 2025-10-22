import json

def extract_important_fields(post: dict) -> dict:
    return {
        "author": {
            "handle": post.get("author", {}).get("handle"),
            "displayName": post.get("author", {}).get("displayName"),
        },
        "createdAt": post.get("record", {}).get("createdAt"),
        "text": post.get("record", {}).get("text")
    }


def main():
    with open("backend/disaster_posts_api.jsonl", "r", encoding="utf-8") as infile, open("backend/clean_posts_api.jsonl", "w", encoding="utf-8") as outfile:
        for line in infile:
            try:
                post = json.loads(line)
                cleaned = extract_important_fields(post)
                outfile.write(json.dumps(cleaned) + "\n")
            except json.JSONDecodeError:
                outfile.write("ERROR WITH " + line + "\n")

    print(f"Cleaned results to backend/clean_posts_api.jsonl")

if __name__ == "__main__":
    main()