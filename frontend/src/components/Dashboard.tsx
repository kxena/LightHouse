import { Activity, TrendingUp, Globe, User, RefreshCw, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';
import { useState, useEffect, useCallback } from 'react';
import { useAutoUpdate } from '../hooks/useAutoUpdate';

const API_BASE_URL = 'http://localhost:8000';

interface TweetData {
  id: string;
  text: string;
  ml_classification: {
    is_disaster: boolean;
    disaster_type: string | null;
    confidence: number;
  };
  llm_extraction?: {
    llm_classification: boolean;
    disaster_type: string;
    location: string;
    severity: string;
    key_details: string;
  };
  createdAt: string;
}

interface ResultsData {
  metadata: {
    generated_at: string;
    pipeline_last_run: string;
    total_tweets: number;
  };
  tweets: TweetData[];
}

// Helper to calculate disaster stats
function calculateStats(tweets: TweetData[]) {
  const disasters = tweets.filter(t => t.ml_classification.is_disaster);
  const disasterTypes: Record<string, number> = {};
  
  disasters.forEach(tweet => {
    const type = tweet.ml_classification.disaster_type || 'unknown';
    disasterTypes[type] = (disasterTypes[type] || 0) + 1;
  });

  return {
    disaster_count: disasters.length,
    disaster_types: disasterTypes
  };
}

export default function Dashboard() {
  const { user, isLoaded } = useUser();
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      setRefreshing(true);
      const response = await fetch(`${API_BASE_URL}/results`, { cache: 'no-store' });
      if (!response.ok) throw new Error('Failed to fetch');
      
      const jsonData: ResultsData = await response.json();
      setData(jsonData);
      console.log('Data refreshed:', new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Auto-update when new data is available
  const { lastUpdate, nextUpdate, hasNewData, isChecking } = useAutoUpdate({
    onUpdate: () => {
      console.log('🔄 New data detected - refreshing dashboard...');
      fetchData();
    },
    pollInterval: 60000, // Check every minute
    enabled: true
  });

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Format time helper
  const formatTime = (isoString: string | null) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit'
    });
  };

  // Get recent tweets (last 5)
  const recentTweets = data?.tweets.slice(0, 5) || [];

  // Calculate stats
  const stats = data ? calculateStats(data.tweets) : { disaster_count: 0, disaster_types: {} };
  const disasterTypes = stats.disaster_types;
  const topDisasterTypes = Object.entries(disasterTypes)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-pink-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-700 text-lg">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold">
              <span className="text-gray-800">Light</span>
              <span className="text-pink-600">House</span>
            </h1>
            <p className="text-gray-600 mt-1">
              Welcome {isLoaded && user ? (user.fullName || user.firstName || 'User') : 'User'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/profile"
              className="flex items-center gap-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-lg shadow-lg border-2 border-white hover:bg-white/80 transition-colors duration-200"
            >
              <User className="w-5 h-5 text-gray-700" />
              <span className="text-gray-700 font-medium">Profile</span>
            </Link>
            <p className="text-gray-600">{new Date().toLocaleDateString()}</p>
          </div>
        </div>

        {/* Data Status Banner */}
        <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 mb-6 shadow-lg border-2 border-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className={`w-5 h-5 ${isChecking ? 'animate-spin text-pink-600' : 'text-gray-700'}`} />
            <div>
              <p className="text-sm font-medium text-gray-700">
                Last Updated: {formatTime(lastUpdate)}
              </p>
              <p className="text-xs text-gray-600">
                Next Update: {formatTime(nextUpdate)}
              </p>
            </div>
            {hasNewData && (
              <span className="ml-3 px-2 py-1 bg-green-500 text-white text-xs font-semibold rounded-full animate-pulse">
                NEW DATA
              </span>
            )}
          </div>
          <button
            onClick={fetchData}
            disabled={refreshing}
            className="flex items-center gap-2 bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>

        {/* Map Placeholder */}
        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg mb-6">
          <div className="w-full h-64 bg-gradient-to-br from-blue-900 to-blue-700 rounded-lg flex items-center justify-center">
            <p className="text-white/50 text-lg">Map Container</p>
          </div>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search disasters, locations..."
            className="w-full px-4 py-3 rounded-xl bg-white/60 backdrop-blur-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-pink-400"
          />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Active Disasters</span>
              </div>
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">
              {stats.disaster_count}
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Total Tweets</span>
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">
              {data?.metadata.total_tweets || 0}
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Disaster Types</span>
              </div>
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">
              {Object.keys(disasterTypes).length}
            </p>
          </div>
        </div>

        {/* Live Feed and Trending */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live Feed */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96 overflow-y-auto">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Live Feed</h2>
              <div className="space-y-4">
                {recentTweets.length > 0 ? (
                  recentTweets.map((tweet) => (
                    <div key={tweet.id} className="border-b border-gray-200 pb-3 last:border-0">
                      <div className="flex items-start gap-2 mb-2">
                        <span className={`px-2 py-1 text-xs font-semibold rounded ${
                          tweet.ml_classification.disaster_type === 'earthquake' ? 'bg-orange-100 text-orange-700' :
                          tweet.ml_classification.disaster_type === 'flood' ? 'bg-blue-100 text-blue-700' :
                          tweet.ml_classification.disaster_type === 'wildfire' ? 'bg-red-100 text-red-700' :
                          tweet.ml_classification.disaster_type === 'hurricane' ? 'bg-purple-100 text-purple-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {tweet.ml_classification.disaster_type || 'Unknown'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(tweet.createdAt).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">{tweet.text}</p>
                      {tweet.llm_extraction?.location && (
                        <p className="text-xs text-gray-500 mt-1">
                          📍 {tweet.llm_extraction.location}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-8">No recent disasters</p>
                )}
              </div>
            </div>
          </div>

          {/* Trending Topics */}
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Disaster Breakdown</h2>
              <div className="space-y-3">
                {topDisasterTypes.length > 0 ? (
                  topDisasterTypes.map(([type, count]) => {
                    const percentage = data ? (count / data.metadata.total_tweets * 100).toFixed(1) : 0;
                    return (
                      <div key={type} className="flex items-center justify-between">
                        <div className="flex items-center gap-3 flex-1">
                          <span className="text-gray-700 font-medium capitalize">{type}</span>
                          <div className="flex-1 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-pink-600 h-2 rounded-full transition-all duration-500"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                        <span className="text-gray-600 font-semibold ml-3">{count}</span>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-gray-400 text-center py-8">No data available</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}