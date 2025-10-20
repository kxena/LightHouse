import { AtpAgent } from "@atproto/api";
import fs from "fs";

 // Load environment variables from .env file
require('dotenv').config();
const identifier = process.env.BLUESKY_IDENTIFIER;
const password = process.env.BLUESKY_PWD;

// main function to collect posts
async function main() {
  const agent = new AtpAgent({ service: "https://bsky.social" });

  await agent.login({
    identifier: identifier,
    password: password,
  });

  console.log("Logged in as:", agent.session.handle);

  const disasterKeywords = ["earthquake", "flood", "wildfire", "hurricane", "tornado"];
  let totalPosts = 0;
  const MAX_POSTS = 500;  // Maximum number of posts to collect overall

  // Use the new searchPosts API instead of getAuthorFeed
  for (const keyword of disasterKeywords) {
    if (totalPosts >= MAX_POSTS) {
      console.log("Reached maximum post limit of 500");
      break;
    }
     // Search for posts containing the disaster keyword
    console.log(`Searching for posts with keyword: ${keyword}`);
    const postsNeeded = MAX_POSTS - totalPosts;
    const limit = Math.min(postsNeeded, 100); // Fetch up to 100 posts at a time

    const results = await agent.api.app.bsky.feed.searchPosts({
      q: keyword,
      limit: limit,
    });

    // Process and save the posts
    for (const post of results.data.posts) {
      if (totalPosts >= MAX_POSTS) break;
      
      if (post.record?.text) {
        console.log("Disaster-related post:", post.record.text);
        fs.appendFileSync("disaster_posts_api.jsonl", JSON.stringify(post) + "\n");
        totalPosts++;
      }
    }
  }
}

main().catch(console.error);