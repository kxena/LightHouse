import {
  Activity,
  TrendingUp,
  Globe,
  RefreshCw,
  Clock,
  AlertTriangle,
} from "lucide-react";
import { useUser, UserButton } from "@clerk/clerk-react";
import {
  useDisasterPosts,
  useStatistics,
  useTrendingTopics,
  useDataRefresh,
  useApiHealth,
} from "../hooks/useApi";
import { useState } from "react";
import {
  LoadingState,
  ErrorState,
  EmptyState,
  ConnectionStatus,
} from "./UIStates";

export default function Dashboard() {
  const { user } = useUser();
  const [searchQuery, setSearchQuery] = useState("");
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Fetch data from our API hooks
  const {
    posts,
    loading: postsLoading,
    error: postsError,
  } = useDisasterPosts(searchQuery, 10);
  const { statistics, loading: statsLoading } = useStatistics();
  const { trending, loading: trendingLoading } = useTrendingTopics();
  const { refreshData, refreshing } = useDataRefresh();
  const { health } = useApiHealth();

  // Handle manual refresh
  const handleRefresh = async () => {
    try {
      await refreshData();
      setLastRefresh(new Date());
    } catch (error) {
      console.error("Failed to refresh data:", error);
    }
  };

  // Auto-refresh timer display
  const formatTimeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    if (seconds < 5) return "Just now";
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-7xl mx-auto items-center">
        <div className="flex justify-center items-center h-12 mb-3">
          <img
            src="src/assets/title.png"
            alt="LightHouse Logo"
            className="object-contain max-h-12"
          />
        </div>

        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <p className="text-gray-600 mt-1 text-xl">
                Welcome {user?.firstName || user?.username || "User"}
              </p>
              <UserButton afterSignOutUrl="/" />
            </div>
            <ConnectionStatus
              isOnline={health?.status === "ok"}
              lastUpdated={statistics.lastUpdated}
            />
            {(postsLoading ||
              statsLoading ||
              trendingLoading ||
              refreshing) && (
              <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 rounded-lg">
                <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-sm text-blue-600">Updating...</span>
              </div>
            )}
          </div>

          <p className="text-gray-600 text-xl">
            {new Date().toLocaleDateString("en-US", {
              year: "numeric",
              month: "2-digit",
              day: "2-digit",
            })}
          </p>
        </div>

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg mb-6">
          <div className="w-full h-64 bg-gradient-to-br from-blue-900 to-blue-700 rounded-lg flex items-center justify-center">
            <p className="text-white/50 text-lg">Map Container</p>
          </div>
        </div>

        <div className="mb-6">
          <input
            type="text"
            placeholder="Search disaster posts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-3 rounded-xl bg-white/60 backdrop-blur-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-pink-400"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Active Incidents</span>
              </div>
              <div
                className={`w-3 h-3 rounded-full ${
                  statistics.activeIncidents > 30
                    ? "bg-red-500 pulse-glow"
                    : statistics.activeIncidents > 10
                    ? "bg-yellow-500"
                    : statistics.activeIncidents > 0
                    ? "bg-green-500"
                    : "bg-gray-400"
                }`}
              ></div>
            </div>
            <p className="text-4xl font-bold text-gray-800 mb-2">
              {statsLoading ? (
                <span className="animate-pulse">...</span>
              ) : (
                statistics.activeIncidents
              )}
            </p>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div
                className="bg-red-400 h-1.5 rounded-full transition-all duration-500"
                style={{
                  width: `${Math.min(
                    (statistics.activeIncidents / 50) * 100,
                    100
                  )}%`,
                }}
              ></div>
            </div>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Posts Per Minute</span>
              </div>
              <div
                className={`w-3 h-3 rounded-full ${
                  statistics.postsPerMinute > 5
                    ? "bg-green-500"
                    : statistics.postsPerMinute > 0
                    ? "bg-yellow-500"
                    : "bg-gray-400"
                }`}
              ></div>
            </div>
            <p className="text-4xl font-bold text-gray-800 mb-2">
              {statsLoading ? (
                <span className="animate-pulse">...</span>
              ) : (
                <>
                  {statistics.postsPerMinute}
                  <span className="text-lg font-normal text-gray-600 ml-1">
                    /min
                  </span>
                </>
              )}
            </p>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <TrendingUp className="w-3 h-3 text-green-500" />
              <span>Real-time monitoring</span>
            </div>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Coverage Area</span>
              </div>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800 mb-2">
              {statistics.coverageArea}
            </p>
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Globe className="w-3 h-3 text-blue-500" />
              <span>Nationwide monitoring</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96 flex flex-col">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-800">Live Feed</h2>
                <button
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="flex items-center gap-2 px-3 py-1 bg-blue-100 hover:bg-blue-200 rounded-lg text-blue-700 text-sm disabled:opacity-50"
                >
                  <RefreshCw
                    className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
                  />
                  {refreshing ? "Refreshing..." : "Refresh"}
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3">
                {postsLoading ? (
                  <LoadingState message="Loading disaster posts..." />
                ) : postsError ? (
                  <ErrorState message={postsError} onRetry={handleRefresh} />
                ) : posts.length === 0 ? (
                  <EmptyState
                    title="No Posts Found"
                    message={
                      searchQuery
                        ? `No posts match "${searchQuery}"`
                        : "No disaster posts available at the moment"
                    }
                    icon={<AlertTriangle className="w-12 h-12 text-gray-400" />}
                  />
                ) : (
                  posts.map((post, index) => (
                    <div
                      key={post.id}
                      className="border-l-4 border-red-400 pl-4 py-3 bg-gray-50 rounded-r hover:bg-gray-100 transition-all duration-200 animate-fadeIn"
                      style={{ animationDelay: `${index * 0.1}s` }}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-gray-800">
                            @{post.handle}
                          </span>
                          <span
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              post.keyword.toLowerCase() === "earthquake"
                                ? "bg-orange-100 text-orange-700"
                                : post.keyword.toLowerCase() === "flood"
                                ? "bg-blue-100 text-blue-700"
                                : post.keyword.toLowerCase() === "wildfire"
                                ? "bg-red-100 text-red-700"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {post.keyword}
                          </span>
                          {post.likeCount > 10 && (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs">
                              🔥 Hot
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-1 text-gray-500 text-xs">
                          <Clock className="w-3 h-3" />
                          {formatTimeAgo(new Date(post.createdAt))}
                        </div>
                      </div>
                      <p
                        className="text-sm text-gray-700 overflow-hidden leading-relaxed"
                        style={{
                          display: "-webkit-box",
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: "vertical" as const,
                        }}
                      >
                        {post.text}
                      </p>
                      <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-4 text-xs text-gray-500">
                          <span className="flex items-center gap-1">
                            <span className="text-red-500">❤️</span>{" "}
                            {post.likeCount}
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="text-blue-500">💬</span>{" "}
                            {post.replyCount}
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="text-green-500">🔄</span>{" "}
                            {post.repostCount}
                          </span>
                        </div>
                        <button className="text-xs text-blue-600 hover:text-blue-800 font-medium">
                          View Details →
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96 flex flex-col">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">
                Trending Topics
              </h2>

              <div className="flex-1 space-y-4">
                {trendingLoading ? (
                  <LoadingState message="Loading trending topics..." />
                ) : trending.length === 0 ? (
                  <EmptyState
                    title="No Trending Data"
                    message="Trending topics will appear as more disaster posts are collected"
                    icon={<TrendingUp className="w-12 h-12 text-gray-400" />}
                  />
                ) : (
                  trending.map((topic, index) => (
                    <div
                      key={topic.keyword}
                      className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center font-bold text-purple-700">
                          {index + 1}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-800">
                            {topic.keyword}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {topic.count} posts
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-green-500" />
                        <span className="text-green-500 text-sm font-medium">
                          {topic.trend === "up" ? "+" : ""}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
