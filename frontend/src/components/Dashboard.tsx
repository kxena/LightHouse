import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  TrendingUp,
  Globe,
  LogOut,
  User,
  RefreshCw,
  MapPin,
} from "lucide-react";
import { useUser, useClerk } from "@clerk/clerk-react";
import { useNavigate } from "react-router-dom";
import MapWidget from "./MapWidget";
import type { Incident as MapIncident } from "../data/incidents";
import { IncidentAPI, type IncidentResponse } from "../services/incidentAPI";

// Compact, dynamic vertical list for trending topics (adjacent to Live Feed)
function TrendingList({
  trending,
  selectedTag,
  onTagClick,
}: {
  trending: Array<[string, number]>;
  selectedTag: string | null;
  onTagClick: (tag: string) => void;
}) {
  const max = trending.length ? Math.max(...trending.map(([, c]) => c)) : 1;
  const formatCount = (n: number) => n.toString();
  return (
    <div className="flex flex-col gap-2 max-h-80 overflow-y-auto pr-1">
      {trending.map(([tag, count]) => {
        const ratio = count / max;
        const isSelected = selectedTag === tag;
        let textCls = "text-sm md:text-base";
        let gradCls = "text-blue-700";
        if (ratio >= 0.75) {
          textCls = "text-lg md:text-xl";
          gradCls =
            "bg-gradient-to-r from-fuchsia-600 to-rose-600 bg-clip-text text-transparent";
        } else if (ratio >= 0.5) {
          textCls = "text-base md:text-lg";
          gradCls =
            "bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent";
        } else if (ratio >= 0.25) {
          textCls = "text-base";
          gradCls =
            "bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent";
        }
        return (
          <div
            key={tag}
            onClick={() => onTagClick(tag)}
            className={`flex items-center justify-between rounded-lg px-2 py-1.5 transition cursor-pointer ${
              isSelected
                ? "bg-purple-100 ring-2 ring-purple-500"
                : "hover:bg-gray-50"
            }`}
            title={`${count} incident${count !== 1 ? "s" : ""} - Click to ${
              isSelected ? "clear filter" : "filter"
            }`}
          >
            <span className={`font-semibold ${textCls} ${gradCls}`}>{tag}</span>
            <span className="text-xs md:text-sm text-gray-600 tabular-nums">
              {formatCount(count)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

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
  const [activeStates] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [incidentsApi, setIncidentsApi] = useState<IncidentResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [nearestIncident, setNearestIncident] = useState<{ distance: number; type: string; city: string } | null>(null);

  // Helper function to get time ago string
  const getTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Computed search results
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const query = searchQuery.toLowerCase();
    return incidentsApi.filter((incident) => {
      return (
        incident.title?.toLowerCase().includes(query) ||
        incident.location?.toLowerCase().includes(query) ||
        incident.incident_type?.toLowerCase().includes(query) ||
        incident.description?.toLowerCase().includes(query)
      );
    });
  }, [searchQuery, incidentsApi]);

  const trending = useMemo(() => {
    const freq: Record<string, number> = {};
    const hashtagRegex = /#[\p{L}0-9_]+/giu; // unicode letters, numbers, underscore
    for (const it of incidentsApi) {
      const perIncident = new Set<string>();
      // From structured tags
      (it.tags || []).forEach((t) =>
        perIncident.add(`#${String(t).toLowerCase()}`)
      );
      // From tweet texts
      (it.source_tweets || []).forEach((tw) => {
        const matches = tw.text.match(hashtagRegex) || [];
        matches.forEach((h) => perIncident.add(h.toLowerCase()));
      });
      // Accumulate once per incident
      for (const h of perIncident) {
        freq[h] = (freq[h] || 0) + 1;
      }
    }
    return Object.entries(freq)
      .filter(([, count]) => count >= 2) // shared/frequent across incidents
      .sort((a, b) => b[1] - a[1])
      .slice(0, 12);
  }, [incidentsApi]);

  // Stub data/handlers — replace with real data wiring
  const handleRefresh = async () => {
    await loadIncidents();
  };

  // Helpers
  const mapIncidentType = (raw?: string): MapIncident["type"] => {
    const s = (raw || "").toLowerCase();
    if (s.includes("flood")) return "Flood";
    if (s.includes("wildfire") || s.includes("fire")) return "Wildfire";
    if (s.includes("earthquake") || s.includes("quake")) return "Earthquake";
    if (s.includes("tornado")) return "Tornado";
    if (s.includes("landslide")) return "Landslide";
    if (s.includes("volcano")) return "Volcano";
    if (s.includes("drought")) return "Drought";
    if (s.includes("heat")) return "Heatwave";
    if (s.includes("cold") || s.includes("freeze")) return "Coldwave";
    return "Storm";
  };

  const mapSeverity = (sev?: string): 1 | 2 | 3 => {
    const s = (sev || "").toLowerCase();
    if (s === "critical") return 3;
    if (s === "high") return 2;
    return 1;
  };

  const parseLatLng = (
    location?: string
  ): { lat: number; lng: number } | null => {
    if (!location) return null;
    // Try to find "(lat,lng)" or "lat,lng" patterns
    const parenMatch = location.match(
      /\((-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)\)/
    );
    if (parenMatch) {
      const lat = parseFloat(parenMatch[1]);
      const lng = parseFloat(parenMatch[2]);
      if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
    }
    const looseMatch = location.match(
      /(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)/
    );
    if (looseMatch) {
      const lat = parseFloat(looseMatch[1]);
      const lng = parseFloat(looseMatch[2]);
      if (Number.isFinite(lat) && Number.isFinite(lng)) return { lat, lng };
    }
    return null;
  };

  // Helper function to check if incident matches selected tag
  const incidentMatchesTag = (
    incident: IncidentResponse,
    tag: string
  ): boolean => {
    const tagLower = tag.toLowerCase();
    const hashtagRegex = /#[\p{L}0-9_]+/giu;

    // Check structured tags
    const hasTags = incident.tags?.some(
      (t) => `#${String(t).toLowerCase()}` === tagLower
    );
    if (hasTags) return true;

    // Check hashtags in tweet texts
    const hasTweetHashtag = incident.source_tweets?.some((tw) => {
      const matches = tw.text.match(hashtagRegex) || [];
      return matches.some((h) => h.toLowerCase() === tagLower);
    });

    return hasTweetHashtag || false;
  };

  // Filter incidents based on selected tag
  const filteredIncidentsApi = useMemo(() => {
    if (!selectedTag) return incidentsApi;
    return incidentsApi.filter((incident) =>
      incidentMatchesTag(incident, selectedTag)
    );
  }, [incidentsApi, selectedTag]);

  // MapWidget expects a different Incident shape (with lat/lng, severity as 1-3)
  const incidents: MapIncident[] = filteredIncidentsApi
    .map((i: IncidentResponse) => {
      const coords =
        typeof i.lat === "number" && typeof i.lng === "number"
          ? { lat: i.lat, lng: i.lng }
          : parseLatLng(i.location);
      if (!coords) return null;
      return {
        id: i.id,
        title: i.title,
        type: mapIncidentType(i.incident_type),
        severity: mapSeverity(i.severity),
        radiusKm: 10,
        city: i.location,
        lat: coords.lat,
        lng: coords.lng,
      } as MapIncident;
    })
    .filter(Boolean) as MapIncident[];
  const postsPerMin = 0; // TODO: real metric

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  const handleTagClick = (tag: string) => {
    // Toggle: if same tag is clicked, deselect it; otherwise select it
    if (selectedTag === tag) {
      setSelectedTag(null);
    } else {
      setSelectedTag(tag);
    }
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

  // Load user location from localStorage and listen for updates
  useEffect(() => {
    const handleStorageChange = () => {
      const savedLat = localStorage.getItem('userLat');
      const savedLng = localStorage.getItem('userLng');
      
      if (savedLat && savedLng) {
        setUserLocation({
          lat: parseFloat(savedLat),
          lng: parseFloat(savedLng)
        });
      } else {
        setUserLocation(null);
      }
    };

    const handleLocationUpdate = () => {
      handleStorageChange();
    };

    // Initial load
    handleStorageChange();
    
    // Listen for updates
    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('locationUpdated', handleLocationUpdate);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('locationUpdated', handleLocationUpdate);
    };
  }, []);
  
  // Calculate nearest incident when user location or incidents change
  useEffect(() => {
    if (!userLocation || incidentsApi.length === 0) {
      setNearestIncident(null);
      return;
    }
    
    // Geocode incident locations
    const incidentCoordinates: { [key: string]: { lat: number; lng: number } } = {
      'alaska': { lat: 61.3707, lng: -152.4044 },
      'california': { lat: 36.7783, lng: -119.4179 },
      'florida': { lat: 27.9944, lng: -81.7603 },
      'texas': { lat: 31.9686, lng: -99.9018 },
      'new york': { lat: 40.7128, lng: -74.0060 },
      'oklahoma': { lat: 35.0078, lng: -97.0929 },
      'north carolina': { lat: 35.7596, lng: -79.0193 },
      'louisiana': { lat: 30.9843, lng: -91.9623 },
      'chile': { lat: -35.6751, lng: -71.5430 },
      'austin': { lat: 30.2672, lng: -97.7431 },
      'indonesia': { lat: -0.7893, lng: 113.9213 },
      'new zealand': { lat: -40.9006, lng: 174.8860 },
    };
    
    let nearest: { distance: number; type: string; city: string } | null = null;
    let minDistance = Infinity;
    
    incidentsApi.forEach(incident => {
      const location = incident.location?.toLowerCase();
      if (!location) return;
      
      // Try to find coordinates for this location
      let coords: { lat: number; lng: number } | null = null;
      
      // Check direct coordinate parsing first
      coords = parseLatLng(incident.location);
      
      // If no coordinates found, try geocoding common locations
      if (!coords) {
        for (const [place, placeCoords] of Object.entries(incidentCoordinates)) {
          if (location.includes(place)) {
            coords = placeCoords;
            break;
          }
        }
      }
      
      if (coords) {
        // Calculate distance using Haversine formula
        const R = 3959; // Earth's radius in miles
        const dLat = (coords.lat - userLocation.lat) * (Math.PI / 180);
        const dLon = (coords.lng - userLocation.lng) * (Math.PI / 180);
        const a = 
          Math.sin(dLat / 2) * Math.sin(dLat / 2) +
          Math.cos(userLocation.lat * (Math.PI / 180)) * Math.cos(coords.lat * (Math.PI / 180)) *
          Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        const distance = R * c;
        
        if (distance < minDistance) {
          minDistance = distance;
          nearest = {
            distance,
            type: incident.incident_type || 'Unknown',
            city: incident.location || 'Unknown'
          };
        }
      }
    });
    
    setNearestIncident(nearest);
  }, [userLocation, incidentsApi]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          {/* Top: Centered brand/logo */}
          <div className="flex justify-center items-center h-12 mb-3">
            <img
              src="src/assets/title.png"
              alt="LightHouse Logo"
              className="object-contain max-h-12"
            />
          </div>

          {/* Bottom: Left welcome, right date + actions */}
          <div className="flex justify-between items-center">
            <p className="text-gray-600 text-xl mt-1">Welcome {displayName},</p>
            <div className="flex items-center gap-4">
              <p className="text-gray-600 text-xl">{currentDate}</p>
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
            viewMode={viewMode}
            onPointClick={(id: MapIncident["id"]) =>
              navigate(`/incident/${id}`)
            }
          />
        </div>

        {/* Search with dropdown results */}
        <div className="mb-4 relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setShowSearchResults(e.target.value.trim().length > 0);
            }}
            onFocus={() => setShowSearchResults(searchQuery.trim().length > 0)}
            placeholder="Search incidents by type, location, or description..."
            className="w-full rounded-xl px-4 py-2 bg-white/70 focus:bg-white outline-none shadow"
          />

          {/* Search results dropdown */}
          {showSearchResults && searchResults.length > 0 && (
            <div className="absolute z-10 w-full mt-2 bg-white rounded-xl shadow-lg max-h-96 overflow-y-auto">
              <div className="p-2">
                <div className="flex justify-between items-center px-3 py-2 border-b">
                  <span className="text-sm font-semibold text-gray-700">
                    Found {searchResults.length} incident
                    {searchResults.length !== 1 ? "s" : ""}
                  </span>
                  <button
                    onClick={() => {
                      setSearchQuery("");
                      setShowSearchResults(false);
                    }}
                    className="text-xs text-gray-500 hover:text-gray-700"
                  >
                    Clear
                  </button>
                </div>
                {searchResults.map((incident) => (
                  <div
                    key={incident.id}
                    onClick={() => {
                      navigate(`/incident/${incident.id}`);
                      setShowSearchResults(false);
                    }}
                    className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">
                          {incident.title}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          {incident.location}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {incident.incident_type}
                          {incident.source_tweets?.[0]?.author &&
                            ` • @${incident.source_tweets[0].author}`}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {new Date(incident.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 ml-2 whitespace-nowrap">
                        {getTimeAgo(incident.created_at)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {showSearchResults &&
            searchResults.length === 0 &&
            searchQuery.trim() && (
              <div className="absolute z-10 w-full mt-2 bg-white rounded-xl shadow-lg p-4">
                <p className="text-sm text-gray-500 text-center">
                  No incidents found matching "{searchQuery}"
                </p>
              </div>
            )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Active Incidents</span>
              <Activity className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">{incidentsApi.length}</div>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Posts/Min</span>
              <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">
              {(postsPerMin / 1000).toFixed(1)}K
            </div>
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Nearest Incident</span>
              <MapPin className="h-4 w-4 text-red-500" />
            </div>
            {userLocation && nearestIncident ? (
              <>
                <div className="text-2xl font-bold mt-1">
                  {nearestIncident.distance.toFixed(1)} mi
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  from {localStorage.getItem('userCity')}, {localStorage.getItem('userState')}
                </div>
                <div className="text-xs text-gray-500 mt-1 truncate">
                  Closest: {nearestIncident.type} in {nearestIncident.city}
                </div>
              </>
            ) : !userLocation ? (
              <div className="text-sm text-gray-500 mt-1">
                Set location in Profile to see nearby incidents
              </div>
            ) : (
              <div className="text-sm text-gray-500 mt-1">
                No incidents with location data
              </div>
            )}
          </div>
          <div className="bg-white rounded-2xl p-4 shadow ring-1 ring-black/5">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Coverage Area</span>
              <Globe className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold mt-1">
              {activeStates} Locations
            </div>
          </div>
        </div>

        {/* Content cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Live Feed (same as previous Recent Incidents) */}
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5 md:col-span-1">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold">Live Feed</h3>
                {selectedTag && (
                  <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                    Filtered by {selectedTag}
                  </span>
                )}
              </div>
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
            ) : filteredIncidentsApi.length === 0 && selectedTag ? (
              <div className="text-gray-600 text-sm">
                No incidents found for tag "{selectedTag}".
                <button
                  onClick={() => setSelectedTag(null)}
                  className="text-purple-600 hover:underline ml-1"
                >
                  Clear filter
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 max-h-80 overflow-y-auto pr-1">
                {filteredIncidentsApi.map((it) => (
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

          {/* Trending Topics computed from shared/frequent tags across incidents */}
          <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5 md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-4 w-4 text-gray-700" />
              <h3 className="font-semibold">Trending Topics</h3>
            </div>
            {incidentsApi.length === 0 ? (
              <div className="text-gray-600 text-sm">No data yet.</div>
            ) : trending.length === 0 ? (
              <div className="text-gray-600 text-sm">
                No trending topics yet.
              </div>
            ) : (
              <TrendingList
                trending={trending}
                selectedTag={selectedTag}
                onTagClick={handleTagClick}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
