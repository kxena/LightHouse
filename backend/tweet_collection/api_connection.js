import { AtpAgent } from "@atproto/api";
import fs from "fs";

async function main() {
  const agent = new AtpAgent({ service: "https://bsky.social" });

  await agent.login({
    identifier: "kxena408.bsky.social",
    password: "LIGHTHOUSE",
  });

  console.log("Logged in as:", agent.session.handle);

  const disasterKeywords = ["earthquake", "flood", "wildfire", "hurricane", "tornado"];
  let totalPosts = 0;
  const MAX_POSTS = 200;

  // Use the new searchPosts API instead of getAuthorFeed
  for (const keyword of disasterKeywords) {
    if (totalPosts >= MAX_POSTS) {
      console.log("Reached maximum post limit of 200");
      break;
    }

    console.log(`Searching for posts with keyword: ${keyword}`);
    const postsNeeded = MAX_POSTS - totalPosts;
    const limit = Math.min(postsNeeded, 100); // API max is 100

    const results = await agent.api.app.bsky.feed.searchPosts({
      q: keyword,
      limit: limit,
    });

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