import os
from atproto import Client
from dotenv import load_dotenv
import json

load_dotenv()

def main():
    # Initialize client and login
    client = Client()
    client.login(
        os.getenv("BLUESKY_IDENTIFIER"),
        os.getenv("BLUESKY_PWD")
    )
    
    print(f"Logged in as: {client.me.handle}")
    
    disaster_keywords = ["earthquake", "flood", "wildfire", "hurricane", "tornado"]
    total_posts = 0
    # batch of max posts of 500
    MAX_POSTS = 500
    
    # Open file for writing
    with open("bluesky_tweets.jsonl", "w") as f:
        for keyword in disaster_keywords:
            if total_posts >= MAX_POSTS:
                print("Reached maximum post limit of 500")
                break
            
            print(f"Searching for posts with keyword: {keyword}")
            posts_needed = MAX_POSTS - total_posts
            limit = min(posts_needed, 100)  # API max is 100
            
            # Search for posts
            results = client.app.bsky.feed.search_posts(
                params={
                    'q': keyword,
                    'limit': limit
                }
            )
            
            for post in results.posts:
                if total_posts >= MAX_POSTS:
                    break
                
                if hasattr(post.record, 'text') and post.record.text:
                    print(f"Disaster-related post: {post.record.text}")
                    
                    # Convert post to dict for JSON serialization
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

if __name__ == "__main__":
    main()