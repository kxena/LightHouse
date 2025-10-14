import express from "express";
import cors from "cors";
import fs from "fs";
import path from "path";
import { AtpAgent } from "@atproto/api";

const app = express();
const PORT = 3001;

// Middleware
app.use(cors());
app.use(express.json());

// In-memory storage for real-time data
let livePostsData = [];
let statisticsData = {
  activeIncidents: 0,
  postsPerMinute: 0,
  coverageArea: "4 States",
  lastUpdated: new Date().toISOString(),
};

// Initialize Bluesky agent
const agent = new AtpAgent({ service: "https://bsky.social" });
let isAuthenticated = false;

// Authentication function
async function authenticateAgent() {
  try {
    await agent.login({
      identifier: "kxena408.bsky.social",
      password: "LIGHTHOUSE",
    });
    isAuthenticated = true;
    console.log("Bluesky agent authenticated:", agent.session?.handle);
  } catch (error) {
    console.error("Authentication failed:", error);
    isAuthenticated = false;
  }
}

// Disaster keywords to search for
const disasterKeywords = [
  "earthquake",
  "flood",
  "wildfire",
  "hurricane",
  "tornado",
  "storm",
  "emergency",
  "disaster",
  "evacuation",
];

// Fetch fresh disaster posts
async function fetchDisasterPosts() {
  if (!isAuthenticated) {
    await authenticateAgent();
  }

  if (!isAuthenticated) {
    console.error("Cannot fetch posts: authentication failed");
    return [];
  }

  const allPosts = [];

  try {
    for (const keyword of disasterKeywords.slice(0, 3)) {
      // Limit to 3 keywords to avoid rate limiting
      console.log(`Fetching posts for keyword: ${keyword}`);

      const results = await agent.api.app.bsky.feed.searchPosts({
        q: keyword,
        limit: 20, // Reduced limit for faster responses
      });

      for (const post of results.data.posts) {
        if (post.record?.text) {
          allPosts.push({
            id: post.uri,
            text: post.record.text,
            author: post.author.displayName || post.author.handle,
            handle: post.author.handle,
            createdAt: post.record.createdAt,
            keyword: keyword,
            likeCount: post.likeCount || 0,
            replyCount: post.replyCount || 0,
            repostCount: post.repostCount || 0,
          });
        }
      }

      // Small delay to avoid rate limiting
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    // Sort by creation date (newest first)
    allPosts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

    return allPosts.slice(0, 50); // Return top 50 most recent posts
  } catch (error) {
    console.error("Error fetching disaster posts:", error);
    return [];
  }
}

// Update statistics based on current data
function updateStatistics() {
  const now = new Date();
  const oneMinuteAgo = new Date(now.getTime() - 60000);

  const recentPosts = livePostsData.filter(
    (post) => new Date(post.createdAt) > oneMinuteAgo
  );

  statisticsData = {
    activeIncidents: livePostsData.length,
    postsPerMinute: recentPosts.length,
    coverageArea: "4 States",
    lastUpdated: now.toISOString(),
  };
}

// API Routes

// Get all disaster posts
app.get("/api/disaster-posts", (req, res) => {
  const { search, limit = 20 } = req.query;

  let filteredPosts = livePostsData;

  if (search) {
    filteredPosts = livePostsData.filter(
      (post) =>
        post.text.toLowerCase().includes(search.toLowerCase()) ||
        post.keyword.toLowerCase().includes(search.toLowerCase())
    );
  }

  res.json({
    posts: filteredPosts.slice(0, parseInt(limit)),
    total: filteredPosts.length,
    lastUpdated: statisticsData.lastUpdated,
  });
});

// Get dashboard statistics
app.get("/api/statistics", (req, res) => {
  updateStatistics();
  res.json(statisticsData);
});

// Get trending disaster topics
app.get("/api/trending", (req, res) => {
  const keywordCounts = {};

  livePostsData.forEach((post) => {
    keywordCounts[post.keyword] = (keywordCounts[post.keyword] || 0) + 1;
  });

  const trending = Object.entries(keywordCounts)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([keyword, count]) => ({
      keyword: keyword.charAt(0).toUpperCase() + keyword.slice(1),
      count,
      trend: "up", // Could be enhanced to calculate actual trend
    }));

  res.json({ trending });
});

// Refresh data endpoint (for manual refresh)
app.post("/api/refresh", async (req, res) => {
  try {
    console.log("Manually refreshing disaster posts data...");
    livePostsData = await fetchDisasterPosts();
    updateStatistics();
    res.json({
      message: "Data refreshed successfully",
      postsCount: livePostsData.length,
      lastUpdated: statisticsData.lastUpdated,
    });
  } catch (error) {
    console.error("Error refreshing data:", error);
    res.status(500).json({ error: "Failed to refresh data" });
  }
});

// Health check endpoint
app.get("/api/health", (req, res) => {
  res.json({
    status: "ok",
    authenticated: isAuthenticated,
    postsLoaded: livePostsData.length,
    uptime: process.uptime(),
  });
});

// Initialize data and start server
async function startServer() {
  console.log("Initializing server...");

  // Authenticate and load initial data
  await authenticateAgent();

  if (isAuthenticated) {
    console.log("Fetching initial disaster posts...");
    livePostsData = await fetchDisasterPosts();
    updateStatistics();
    console.log(`Loaded ${livePostsData.length} initial posts`);

    // Set up periodic data refresh (every 5 minutes)
    setInterval(async () => {
      try {
        console.log("Refreshing disaster posts data...");
        const newPosts = await fetchDisasterPosts();
        livePostsData = newPosts;
        updateStatistics();
        console.log(`Refreshed ${livePostsData.length} posts`);
      } catch (error) {
        console.error("Error during periodic refresh:", error);
      }
    }, 5 * 60 * 1000); // 5 minutes
  }

  app.listen(PORT, () => {
    console.log(`🚀 LightHouse API Server running on http://localhost:${PORT}`);
    console.log(`📊 Dashboard: http://localhost:3000/dashboard`);
    console.log(`🔗 API Health: http://localhost:${PORT}/api/health`);
  });
}

// Start the server
startServer().catch(console.error);
