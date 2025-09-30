import fs from "fs";
import { AtpAgent } from "@atproto/api";

async function main() {
  const agent = new AtpAgent({ service: "https://bsky.social" });

  await agent.login({
    identifier: "kxena408.bsky.social",
    password: "LIGHTHOUSE",
  });

  console.log("Logged in as:", agent.session.handle);

  const disasterKeywords = ["earthquake", "flood", "wildfire", "hurricane", "tornado"];

  // Use the new searchPosts API instead of getAuthorFeed
  for (const keyword of disasterKeywords) {
    console.log(`Searching for posts with keyword: ${keyword}`);
    const results = await agent.api.app.bsky.feed.searchPosts({
      q: keyword,
      limit: 100,
    });

    for (const post of results.data.posts) {
      if (post.record?.text) {
        console.log("Disaster-related post:", post.record.text);
        fs.appendFileSync("disaster_posts_api.jsonl", JSON.stringify(post) + "\n");
      }
    }
  }
}

main().catch(console.error);
