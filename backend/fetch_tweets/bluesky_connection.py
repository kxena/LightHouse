import os
from atproto import Client
from dotenv import load_dotenv
import json

load_dotenv()

def scrape_bluesky_tweets(max_posts: int = 500, output_file: str = "../fetch_tweets/bluesky_tweets.jsonl") -> int:
    """
    Scrapes disaster-related posts from Bluesky
    
    Args:
        max_posts: Maximum number of posts to collect (default: 500)
        output_file: Output filename (default: "bluesky_tweets.jsonl")
    
    Returns:
        int: Number of posts collected
    
    Raises:
        Exception: If login fails or scraping encounters errors
    """
    client = Client()
    client.login(
        os.getenv("BLUESKY_USER"),
        os.getenv("BLUESKY_PWD")
    )
    
    print(f"Logged in as: {client.me.handle}")
    
    disaster_keywords = ["earthquake", "flood", "wildfire", "hurricane", "tornado"]
    total_posts = 0
    
    with open(output_file, "w") as f:
        for keyword in disaster_keywords:
            if total_posts >= max_posts:
                print(f"Reached maximum post limit of {max_posts}")
                break
            
            print(f"Searching for posts with keyword: {keyword}")
            posts_needed = max_posts - total_posts
            limit = min(posts_needed, 100)  # API max is 100
            
            results = client.app.bsky.feed.search_posts(
                params={
                    'q': keyword,
                    'limit': limit
                }
            )
            
            for post in results.posts:
                if total_posts >= max_posts:
                    break
                
                if hasattr(post.record, 'text') and post.record.text:
                    post_dict = {
                        'text': post.record.text,
                        'uri': post.uri,
                        'cid': post.cid,
                        'author': {
                            'handle': post.author.handle,
                            'display_name': post.author.display_name
                        },
                        'created_at': post.record.created_at,
                        'like_count': post.like_count if hasattr(post, 'like_count') else 0,
                        'reply_count': post.reply_count if hasattr(post, 'reply_count') else 0,
                        'repost_count': post.repost_count if hasattr(post, 'repost_count') else 0
                    }
                    
                    f.write(json.dumps(post_dict) + "\n")
                    total_posts += 1
    
    print(f"\nTotal posts collected: {total_posts}")
    return total_posts


# For standalone testing
if __name__ == "__main__":
    total = scrape_bluesky_tweets()
    print(f"Scraping complete: {total} posts collected")