import json
import re
import hashlib

# disaster keywords to match against
DISASTER_KEYWORDS = ["earthquake", "flood", "wildfire", "hurricane", "tornado", "blaze"]

# loop through text content and try finding a keyword; if none, mark as null
def extract_keyword(text: str, keywords: list) -> str:
    if not text:
        return None
    
    text_lower = text.lower()

    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
            return keyword
        
    return None

# create a unique ID for post based on author and timestamp
def generate_id(post: dict) -> str:
   
    author_handle = post.get("author", {}).get("handle", "unknown")
    created_at = post.get("createdAt", "")
    
    # hash based ID for randomness/security
    id_string = f"{author_handle}_{created_at}"
    return hashlib.md5(id_string.encode()).hexdigest()[:10]


# convert cleaned Bluesky data to Kaggle format
def clean_post_to_kaggle_format(post: dict) -> dict:
    
    text = post.get("text", "")
    
    return {
        "id": generate_id(post),
        "keyword": extract_keyword(text, DISASTER_KEYWORDS),
        "location": None,  # will try to do later
        "text": text,
        "target": 1  # assuming all collected posts are disaster-related (target=1)
    }


def main():
    cleaned_posts = []
    
    with open("clean_posts_api.jsonl", "r", encoding="utf-8") as infile:
        for line in infile:
            try:
                post = json.loads(line)
                cleaned = clean_post_to_kaggle_format(post)
                cleaned_posts.append(cleaned)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue
    
    # write as JSONL
    with open("kaggle_format_posts.jsonl", "w", encoding="utf-8") as outfile:
        for post in cleaned_posts:
            outfile.write(json.dumps(post) + "\n")
    
    # write as CSV
    if cleaned_posts:
        import csv
        
        with open("kaggle_format_posts.csv", "w", encoding="utf-8", newline="") as csvfile:
            fieldnames = ["id", "keyword", "location", "text", "target"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(cleaned_posts)
        
        print(f"Processed {len(cleaned_posts)} posts")
        print(f"Output: kaggle_format_posts.jsonl and kaggle_format_posts.csv")
        
        # print some stats
        keywords_found = sum(1 for p in cleaned_posts if p["keyword"])
        print(f"Keywords extracted: {keywords_found}/{len(cleaned_posts)}")
    else:
        print("No posts processed")


if __name__ == "__main__":
    main()