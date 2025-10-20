import json

def extract_important_fields(post: dict) -> dict:
    """
    Extract important fields from Python atproto client post format
    """
    return {
        "author": {
            "handle": post.get("author", {}).get("handle"),
            "displayName": post.get("author", {}).get("display_name"),
        },
        "createdAt": post.get("created_at"),
        "text": post.get("text")
    }


def main():
    with open("bluesky_tweets.jsonl", "r", encoding="utf-8") as infile, open("clean_tweets.jsonl", "w", encoding="utf-8") as outfile:
        for line in infile:
            try:
                post = json.loads(line)
                cleaned = extract_important_fields(post)
                outfile.write(json.dumps(cleaned) + "\n")
            except json.JSONDecodeError:
                outfile.write("ERROR WITH " + line + "\n")

    print(f"Cleaned results to clean_tweets.jsonl")

if __name__ == "__main__":
    main()