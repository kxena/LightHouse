import json
from typing import List, Dict

def extract_important_fields(post: dict) -> dict:
    """
    Extract important fields from Python atproto client post format
    
    Args:
        post: Raw post dictionary from Bluesky API
    
    Returns:
        dict: Cleaned post with only essential fields
    """
    return {
        "author": {
            "handle": post.get("author", {}).get("handle"),
            "displayName": post.get("author", {}).get("display_name"),
        },
        "createdAt": post.get("created_at"),
        "text": post.get("text")
    }


def clean_tweets(input_file: str = "../fetch_tweets/bluesky_tweets.jsonl", output_file: str = "../fetch_tweets/clean_tweets.jsonl") -> List[Dict]:
    """
    Clean tweets from input JSONL file
    
    Args:
        input_file: Input filename (default: "bluesky_tweets.jsonl")
        output_file: Output filename (default: "clean_tweets.jsonl")
    
    Returns:
        List[Dict]: List of cleaned tweet dictionaries
    
    Raises:
        FileNotFoundError: If input file doesn't exist
    """
    cleaned_tweets = []
    
    with open(input_file, "r", encoding="utf-8") as infile, \
         open(output_file, "w", encoding="utf-8") as outfile:
        
        for line in infile:
            try:
                post = json.loads(line)
                cleaned = extract_important_fields(post)
                outfile.write(json.dumps(cleaned) + "\n")
                cleaned_tweets.append(cleaned)
            except json.JSONDecodeError:
                print(f"ERROR WITH: {line}")
                continue
    
    print(f"Cleaned {len(cleaned_tweets)} tweets to {output_file}")
    return cleaned_tweets


# For standalone testing
if __name__ == "__main__":
    cleaned = clean_tweets()
    print(f"Cleaning complete: {len(cleaned)} tweets processed")