import { useState, useEffect, useCallback } from "react";

const API_BASE_URL = "http://localhost:3001/api";

// Type definitions
export interface DisasterPost {
  id: string;
  text: string;
  author: string;
  handle: string;
  createdAt: string;
  keyword: string;
  likeCount: number;
  replyCount: number;
  repostCount: number;
}

export interface Statistics {
  activeIncidents: number;
  postsPerMinute: number;
  coverageArea: string;
  lastUpdated: string;
}

export interface TrendingTopic {
  keyword: string;
  count: number;
  trend: "up" | "down" | "stable";
}

export interface ApiHealth {
  status: string;
  authenticated: boolean;
  postsLoaded?: number;
  uptime?: number;
}

// Custom hook for fetching disaster posts
export const useDisasterPosts = (searchQuery = "", limit = 20) => {
  const [posts, setPosts] = useState<DisasterPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (searchQuery) params.append("search", searchQuery);
      if (limit) params.append("limit", limit.toString());

      const response = await fetch(`${API_BASE_URL}/disaster-posts?${params}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setPosts(data.posts || []);
      setLastUpdated(data.lastUpdated);
    } catch (err) {
      console.error("Error fetching disaster posts:", err);
      setError(err instanceof Error ? err.message : "Failed to fetch posts");
      setPosts([]);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, limit]);

  useEffect(() => {
    fetchPosts();

    // Auto-refresh posts every 2 minutes
    const interval = setInterval(fetchPosts, 2 * 60 * 1000);

    return () => clearInterval(interval);
  }, [fetchPosts]);

  const refetch = useCallback(() => {
    fetchPosts();
  }, [fetchPosts]);

  return {
    posts,
    loading,
    error,
    lastUpdated,
    refetch,
  };
};

// Custom hook for dashboard statistics
export const useStatistics = () => {
  const [statistics, setStatistics] = useState<Statistics>({
    activeIncidents: 0,
    postsPerMinute: 0,
    coverageArea: "4 States",
    lastUpdated: "",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/statistics`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      console.error("Error fetching statistics:", err);
      setError(
        err instanceof Error ? err.message : "Failed to fetch statistics"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatistics();

    // Refresh statistics every 30 seconds
    const interval = setInterval(fetchStatistics, 30000);

    return () => clearInterval(interval);
  }, [fetchStatistics]);

  const refetch = useCallback(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    statistics,
    loading,
    error,
    refetch,
  };
};

// Custom hook for trending topics
export const useTrendingTopics = () => {
  const [trending, setTrending] = useState<TrendingTopic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrending = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/trending`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setTrending(data.trending || []);
    } catch (err) {
      console.error("Error fetching trending topics:", err);
      setError(
        err instanceof Error ? err.message : "Failed to fetch trending topics"
      );
      setTrending([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrending();

    // Refresh trending topics every minute
    const interval = setInterval(fetchTrending, 60000);

    return () => clearInterval(interval);
  }, [fetchTrending]);

  const refetch = useCallback(() => {
    fetchTrending();
  }, [fetchTrending]);

  return {
    trending,
    loading,
    error,
    refetch,
  };
};

// Custom hook for manual data refresh
export const useDataRefresh = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshData = useCallback(async () => {
    try {
      setRefreshing(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Data refreshed:", data);
      return data;
    } catch (err) {
      console.error("Error refreshing data:", err);
      setError(err instanceof Error ? err.message : "Failed to refresh data");
      throw err;
    } finally {
      setRefreshing(false);
    }
  }, []);

  return {
    refreshData,
    refreshing,
    error,
  };
};

// Utility hook to check API health
export const useApiHealth = () => {
  const [health, setHealth] = useState<ApiHealth | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        setHealth(data);
      } catch (err) {
        console.error("API health check failed:", err);
        setHealth({ status: "error", authenticated: false });
      } finally {
        setLoading(false);
      }
    };

    checkHealth();

    // Check health every 5 minutes
    const interval = setInterval(checkHealth, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, []);

  return { health, loading };
};
