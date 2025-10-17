import React, { useEffect, useState } from "react";
import {
  Activity,
  TrendingUp,
  Globe,
  LogOut,
  User,
  RefreshCw,
} from "lucide-react";
import { useUser, useClerk } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
// If MapWidget is elsewhere, fix this path.
import MapWidget from "./MapWidget";
import type { Incident as MapIncident } from "../data/incidents";
import { IncidentAPI, type IncidentResponse } from "../services/incidentAPI";

export default function Dashboard() {
  const { user } = useUser();
  const { signOut } = useClerk();
  const navigate = useNavigate();

  const displayName = user?.firstName || user?.username || "User";

  // Format current date as MM/DD/YYYY
  const currentDate = new Date().toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  });

  const [viewMode, setViewMode] = useState<"points" | "heat">("points");
  const [searchQuery, setSearchQuery] = useState("");
  const [incidentsApi, setIncidentsApi] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Stub data/handlers — replace with real data wiring
  const handleRefresh = async () => {
    await loadIncidents();
  };

  // NOTE: MapWidget uses a different Incident shape with lat/lng; keeping it empty for now.
  const incidents: MapIncident[] = [];
  const activeIncidents = incidentsApi.length;
  const postsPerMin = 0; // TODO: real metric
  const activeStates = 0; // TODO: real metric

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  const loadIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await IncidentAPI.getAllIncidents();
      setIncidentsApi(data);
    } catch (err) {
      console.error("Failed to load incidents:", err);
      setError(err instanceof Error ? err.message : "Failed to load incidents");
      setIncidentsApi([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

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
            <p className="text-gray-600 mt-1">Welcome {displayName}</p>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-gray-600">{currentDate}</p>
            <button
              onClick={handleProfile}
              className="flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm text-gray-800 font-semibold rounded-lg shadow-md hover:bg-white/80 transition-all duration-200"
            >
              <User className="w-4 h-4" />
              Profile
            </button>
            <button
              onClick={handleSignOut}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/80 text-white font-semibold rounded-lg shadow-md hover:bg-red-600 transition-all duration-200"
            >
              <LogOut className="w-4 h-4" />
              Log Out
            </button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center bg-white/70 rounded-xl shadow overflow-hidden">
            <button
              className={`px-3 py-1 text-sm ${
                viewMode === "points" ? "bg-white font-semibold" : "opacity-70"
              }`}
              onClick={() => setViewMode("points")}
            >
              Points
            </button>
            <button
              className={`px-3 py-1 text-sm ${
                viewMode === "heat" ? "bg-white font-semibold" : "opacity-70"
              }`}
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

        {/* Map Card */}
        <div className="bg-white/45 backdrop-blur-sm rounded-2xl p-4 shadow mb-6">
          <MapWidget
            incidents={incidents}
            heightClass="h-72"
            initialCenter={[20, 0]}
            initialZoom={2}
            lockSingleWorld={true}
            viewMode={viewMode} /* NEW */
            onPointClick={(id: MapIncident["id"]) =>
              navigate(`/incident/${id}`)
            }
          />
        </div>

        {/* Search */}
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search"
          className="w-full rounded-xl px-4 py-2 bg-white/70 focus:bg-white outline-none shadow mb-6"
        />

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
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
            <div className="text-2xl font-bold mt-1">
              {(postsPerMin / 1000).toFixed(1)}K posts/min
            </div>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Coverage Area</span>
              <Globe className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">{activeStates} States</div>
          </div>
        </div>

        {/* Content cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
            <h3 className="font-semibold mb-2">Live Feed</h3>
            {/* TODO: live feed list */}
          </div>
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
            <h3 className="font-semibold mb-2">Trending Topics</h3>
            <div className="flex flex-wrap gap-2">
              {["#PowerOutage", "#Downtown", "#Restoration", "#Austin"].map(
                (t) => (
                  <span
                    key={t}
                    className="px-3 py-1 rounded-full bg-gray-900 text-white text-sm"
                  >
                    {t}
                  </span>
                )
              )}
            </div>
          </div>
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5 md:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold">
                Recent Incidents (from AI analysis)
              </h3>
              {loading && (
                <span className="text-sm text-gray-500">Loading…</span>
              )}
            </div>
            {error ? (
              <div className="text-red-600 text-sm">{error}</div>
            ) : incidentsApi.length === 0 ? (
              <div className="text-gray-600 text-sm">
                No incidents yet. Try seeding or check back soon.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {incidentsApi.map((it) => (
                  <button
                    key={it.id}
                    onClick={() => navigate(`/incident/${it.id}`)}
                    className="text-left p-4 rounded-xl border border-gray-200 hover:border-purple-500 hover:bg-purple-50 transition"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-sm">
                        {it.incident_type}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                        {it.severity}
                      </span>
                    </div>
                    <div className="text-xs text-gray-600 truncate">
                      {it.location}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {new Date(it.created_at).toLocaleString()}
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
