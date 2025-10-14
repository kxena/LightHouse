// src/Dashboard.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity, TrendingUp, Globe, RefreshCw } from "lucide-react";
import { LoadingState, ErrorState, EmptyState } from "./UIStates";
import MapWidget from "./MapWidget";
import { incidents } from "../data/incidents";

const useStatistics = () => ({ postsPerMin: 2300, activeStates: 4, activeIncidents: 23 });
const useTrendingTopics = () => ["#PowerOutage", "#Downtown", "#Restoration", "#Austin"];
const useDisasterPosts = () => ({ data: [], isLoading: false, isError: false });
const useDataRefresh = () => ({ refreshData: async () => {} });

export default function Dashboard() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"points" | "heat">("points"); // NEW

  const { postsPerMin, activeStates, activeIncidents } = useStatistics();
  const trending = useTrendingTopics();
  const { data, isLoading, isError } = useDisasterPosts();
  const { refreshData } = useDataRefresh();

  const handleRefresh = async () => {
    try { await refreshData(); } catch (e) { console.error(e); }
  };

  if (isLoading) return <LoadingState message="Loading dashboard..." />;
  if (isError) return <ErrorState message="Failed to load dashboard" />;
  if (!data && !incidents.length)
    return <EmptyState title="Nothing to show" message="No data available." />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-6 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl md:text-3xl font-bold tracking-wide">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600">
              LightHouse
            </span>
          </h1>

          <div className="flex items-center gap-3">
            {/* Toggle */}
            <div className="flex items-center bg-white/70 rounded-xl shadow overflow-hidden">
              <button
                className={`px-3 py-1 text-sm ${viewMode === "points" ? "bg-white font-semibold" : "opacity-70"}`}
                onClick={() => setViewMode("points")}
              >
                Points
              </button>
              <button
                className={`px-3 py-1 text-sm ${viewMode === "heat" ? "bg-white font-semibold" : "opacity-70"}`}
                onClick={() => setViewMode("heat")}
              >
                Heat
              </button>
            </div>

            <button
              onClick={handleRefresh}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-white/70 hover:bg-white shadow"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Map Card */}
        <div className="bg-white/45 backdrop-blur-sm rounded-2xl p-4 shadow">
          <MapWidget
            incidents={incidents}
            heightClass="h-72"
            initialCenter={[20, 0]}    // global view
            initialZoom={2}
            lockSingleWorld
            viewMode={viewMode}        // NEW
            onPointClick={(id) => navigate(`/incident/${id}`)}
          />
        </div>

        {/* Search */}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search"
          className="w-full rounded-xl px-4 py-2 bg-white/70 focus:bg-white outline-none shadow"
        />

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Active Incidents</span>
              <Activity className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">{activeIncidents}</div>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">System Status</span>
              <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">{(postsPerMin / 1000).toFixed(1)}K posts/min</div>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Coverage Area</span>
              <Globe className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">{activeStates} States</div>
          </div>
        </div>

        {/* Content cards (unchanged) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
            <h3 className="font-semibold mb-2">Live Feed</h3>
          </div>
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
            <h3 className="font-semibold mb-2">Trending Topics</h3>
            <div className="flex flex-wrap gap-2">
              {["#PowerOutage", "#Downtown", "#Restoration", "#Austin"].map((t) => (
                <span key={t} className="px-3 py-1 rounded-full bg-gray-900 text-white text-sm">
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
