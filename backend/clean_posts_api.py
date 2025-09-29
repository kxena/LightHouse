import json

def extract_important_fields(post: dict) -> dict:
    return {
        "author": {
            "handle": post.get("author", {}).get("handle"),
            "displayName": post.get("author", {}).get("displayName"),
        },
        "createdAt": post.get("record", {}).get("createdAt"),
        "text": post.get("record", {}).get("text"),
        '''the following fields could possibly be extracted for credibility'''
        "stats": {
            "likeCount": post.get("likeCount", 0),
            "repostCount": post.get("repostCount", 0),
            "replyCount": post.get("replyCount", 0),
            "quoteCount": post.get("quoteCount", 0),
            "bookmarkCount": post.get("bookmarkCount", 0),
        }
    }


def main():
    with open("disaster_posts_api.jsonl", "r", encoding="utf-8") as infile, open("clean_posts_api.jsonl", "w", encoding="utf-8") as outfile:
        for line in infile:
            try:
                post = json.loads(line)
                cleaned = extract_important_fields(post)
                outfile.write(json.dumps(cleaned) + "\n")
            except json.JSONDecodeError:
                outfile.write("ERROR WITH " + line + "\n")

    print(f"Cleaned results to clean_posts_api.jsonl")

if __name__ == "__main__":
    main()