import {
  ArrowLeft,
  AlertCircle,
  Twitter,
  MessageCircle,
  Repeat,
  Heart,
  Clock,
} from "lucide-react";
import { useNavigate, useParams, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { IncidentAPI, type IncidentResponse } from "../api/lighthouseApi";
import MapWidget from "./MapWidget";
import type { Incident as MapIncident } from "../data/incidents";
import { DarkModeToggle } from "./DarkModeToggle";

export default function IncidentReport() {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<IncidentResponse[]>([]);
  const [currentIncident, setCurrentIncident] =
    useState<IncidentResponse | null>(null);
  const { id: incidentId } = useParams();
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  const historyDate = query.get("date") || undefined;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Add viewMode state for toggle UI
  const [viewMode, setViewMode] = useState<"points" | "heat">("points");

  // Load incidents on component mount
  useEffect(() => {
    if (incidentId) {
      loadIncidentById(incidentId, historyDate);
    } else {
      loadIncidents();
    }
  }, [incidentId, historyDate]);

  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await IncidentAPI.getAllIncidents();
      setIncidents(data);
      if (data.length > 0) {
        setCurrentIncident(data[0]);
      } else {
        setCurrentIncident(null);
      }
    } catch (err) {
      setError("Failed to load incidents generated from tweet analysis");
      console.error("Error loading incidents:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadIncidentById = async (incidentId: string, date?: string) => {
    try {
      setLoading(true);
      const incident = await IncidentAPI.getIncident(incidentId, date);
      setCurrentIncident(incident);
      setIncidents([]); // Optionally clear list, or fetch all for navigation
    } catch (err) {
      setError("Failed to load incident by id");
      console.error("Error loading incident by id:", err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "bg-red-500";
      case "high":
        return "bg-orange-500";
      case "medium":
        return "bg-yellow-500";
      case "low":
        return "bg-green-500";
      default:
        return "bg-gray-500";
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatTweetTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-700 text-lg">Loading incidents...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
          <p className="text-red-600 text-lg">{error}</p>
          <div className="mt-4 flex gap-3 justify-center">
            <button
              onClick={() =>
                incidentId ? navigate("/dashboard") : loadIncidents()
              }
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              {incidentId ? "Back to Dashboard" : "Try Again"}
            </button>
            {incidentId && (
              <button
                onClick={loadIncidents}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
              >
                View All Incidents
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 dark:from-slate-800 dark:via-purple-900 dark:to-blue-900 p-6 lg:p-10">
      <div className="mx-auto max-w-6xl">
        {/* Dark Mode Toggle */}
        <DarkModeToggle />
        
        {/* Header */}
        <div className="relative mb-6 lg:mb-10 flex items-center pr-16">
          <button
            className="absolute left-0 p-2 rounded-full hover:bg-white/40 dark:hover:bg-gray-800/40 transition"
            onClick={() => navigate("/dashboard")}
            aria-label="Back to Dashboard"
          >
            <ArrowLeft className="h-6 w-6 text-gray-700 dark:text-gray-300" />
          </button>

          <div className="w-full flex justify-between items-center">
            <div></div> {/* Spacer for back button */}
            <h1 className="text-3xl font-extrabold tracking-wide">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600 dark:from-purple-300 dark:to-pink-300">
                LightHouse
              </span>
            </h1>
            <div></div> {/* Spacer for dark mode toggle */}
          </div>
        </div>

        {/* Controls Row */}
        <div className="flex justify-between items-center mb-6">
          {/* View Mode Toggle */}
          <div className="flex items-center bg-white/70 dark:bg-gray-800/70 rounded-xl shadow overflow-hidden">
            <button
              className={`px-3 py-1 text-sm ${
                viewMode === "points"
                  ? "bg-white dark:bg-slate-600 font-semibold text-gray-900 dark:text-gray-100"
                  : "opacity-70 text-gray-700 dark:text-gray-300"
              }`}
              onClick={() => setViewMode("points")}
            >
              Points
            </button>
            <button
              className={`px-3 py-1 text-sm ${
                viewMode === "heat" ? "bg-white dark:bg-slate-600 font-semibold text-gray-900 dark:text-gray-100" : "opacity-70 text-gray-700 dark:text-gray-300"
              }`}
              onClick={() => setViewMode("heat")}
            >
              Heat
            </button>
          </div>

          {/* Tweet Analysis Badge */}
          <div className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 rounded-full">
            <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
              Tweet Analysis
            </span>
          </div>
        </div>

        {currentIncident ? (
          <>
            {/* 2x2 Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Map Card (top-left) */}
              <div className="lg:col-span-6">
                <div className="rounded-3xl bg-white/55 dark:bg-slate-700/55 backdrop-blur-sm shadow-[0_10px_30px_rgba(0,0,0,0.08)] ring-1 ring-black/5 dark:ring-white/10 p-4">
                  <MapWidget
                    incidents={
                      (currentIncident ? [currentIncident] : [])
                        .map((i) => {
                          // Try lat/lng from API; otherwise parse from location string if present
                          const parseLatLng = (
                            location?: string
                          ): { lat: number; lng: number } | null => {
                            if (!location) return null;
                            const parenMatch = location.match(
                              /\((-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)\)/
                            );
                            if (parenMatch) {
                              const lat = parseFloat(parenMatch[1]);
                              const lng = parseFloat(parenMatch[2]);
                              if (Number.isFinite(lat) && Number.isFinite(lng))
                                return { lat, lng };
                            }
                            const looseMatch = location.match(
                              /(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)/
                            );
                            if (looseMatch) {
                              const lat = parseFloat(looseMatch[1]);
                              const lng = parseFloat(looseMatch[2]);
                              if (Number.isFinite(lat) && Number.isFinite(lng))
                                return { lat, lng };
                            }
                            return null;
                          };
                          const coords =
                            typeof (
                              i as IncidentResponse & {
                                lat?: number;
                                lng?: number;
                              }
                            ).lat === "number" &&
                            typeof (
                              i as IncidentResponse & {
                                lat?: number;
                                lng?: number;
                              }
                            ).lng === "number"
                              ? {
                                  lat: (
                                    i as IncidentResponse & {
                                      lat?: number;
                                      lng?: number;
                                    }
                                  ).lat as number,
                                  lng: (
                                    i as IncidentResponse & {
                                      lat?: number;
                                      lng?: number;
                                    }
                                  ).lng as number,
                                }
                              : parseLatLng(i.location);
                          if (!coords) return null;
                          const sev = i.severity.toLowerCase();
                          const sevNum: 1 | 2 | 3 =
                            sev === "critical" ? 3 : sev === "high" ? 2 : 1;
                          const mapType = (
                            raw?: string
                          ): MapIncident["type"] => {
                            const s = (raw || "").toLowerCase();
                            if (s.includes("flood")) return "Flood";
                            if (s.includes("wildfire") || s.includes("fire"))
                              return "Wildfire";
                            if (s.includes("earthquake") || s.includes("quake"))
                              return "Earthquake";
                            if (s.includes("tornado")) return "Tornado";
                            if (s.includes("landslide")) return "Landslide";
                            if (s.includes("volcano")) return "Volcano";
                            if (s.includes("drought")) return "Drought";
                            if (s.includes("heat")) return "Heatwave";
                            if (s.includes("cold") || s.includes("freeze"))
                              return "Coldwave";
                            return "Storm";
                          };
                          return {
                            id: i.id,
                            title: i.title,
                            type: mapType(i.incident_type),
                            severity: sevNum,
                            radiusKm: 10,
                            city: i.location,
                            lat: coords.lat,
                            lng: coords.lng,
                          } as MapIncident;
                        })
                        .filter(Boolean) as MapIncident[]
                    }
                    heightClass="h-64"
                    initialCenter={[20, 0]}
                    initialZoom={2}
                    lockSingleWorld={true}
                    focusId={currentIncident.id}
                    viewMode={viewMode}
                    onPointClick={(id: string) => {
                      const dateParam = historyDate
                        ? `?date=${historyDate}`
                        : "";
                      navigate(`/incident/${id}${dateParam}`);
                    }}
                    showRings
                  />
                </div>
              </div>

              {/* Incident Summary (top-right) */}
              <div className="lg:col-span-6">
                <div className="rounded-3xl bg-white/65 dark:bg-slate-700/65 backdrop-blur-sm shadow-[0_10px_30px_rgba(0,0,0,0.08)] ring-1 ring-black/5 dark:ring-white/10 p-6">
                  <div className="rounded-2xl bg-white dark:bg-white p-6">
                    <h2 className="text-3xl font-extrabold tracking-wide text-center mb-3">
                      <span className="bg-clip-text text-transparent bg-gradient-to-r from-pink-600 to-rose-600">
                        {currentIncident.incident_type}
                      </span>
                    </h2>

                    <p className="text-center text-gray-700 leading-relaxed max-w-lg mx-auto mb-4">
                      {currentIncident.description}
                    </p>

                    {currentIncident.estimated_restoration && (
                      <p className="text-center text-gray-700 mb-4">
                        Estimated restoration:
                        <span className="font-semibold">
                          {" "}
                          {currentIncident.estimated_restoration}
                        </span>
                      </p>
                    )}

                    <p className="text-center text-lg tracking-wide text-gray-900 font-semibold">
                      {currentIncident.location}
                    </p>

                    <div className="mt-4 text-center">
                      <span
                        className={`inline-block px-3 py-1 rounded-full text-sm font-medium text-white ${
                          currentIncident.status === "active"
                            ? "bg-red-500"
                            : currentIncident.status === "resolved"
                            ? "bg-green-500"
                            : "bg-gray-500"
                        }`}
                      >
                        Status: {currentIncident.status.toUpperCase()}
                      </span>
                    </div>

                    <p className="text-center text-sm text-gray-500 mt-2">
                      Created: {formatDateTime(currentIncident.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Severity + Tags (bottom-left) */}
              <div className="lg:col-span-6">
                <div className="rounded-3xl bg-white/65 dark:bg-slate-700/65 backdrop-blur-sm shadow-[0_10px_30px_rgba(0,0,0,0.08)] ring-1 ring-black/5 dark:ring-white/10 p-6">
                  <div className="rounded-2xl bg-white dark:bg-white p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <h3 className="text-2xl font-bold text-gray-900">Severity:</h3>
                      <span
                        className={`inline-flex h-3.5 w-3.5 rounded-full ${getSeverityColor(
                          currentIncident.severity
                        )} shadow-[0_0_0_6px_rgba(239,68,68,0.18)]`}
                      />
                      <span className="font-semibold capitalize text-gray-900">
                        {currentIncident.severity}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-3">
                      {currentIncident.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 rounded-full text-sm font-medium bg-gray-900 text-white/95 shadow-sm"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Associated Tweets (bottom-right) */}
              <div className="lg:col-span-6">
                <div className="rounded-3xl bg-white/65 dark:bg-slate-700/65 backdrop-blur-sm shadow-[0_10px_30px_rgba(0,0,0,0.08)] ring-1 ring-black/5 dark:ring-white/10 p-4">
                  <div className="rounded-2xl bg-white dark:bg-white p-4 lg:p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-xl font-bold text-gray-900">Associated Tweets</h3>
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                        {currentIncident.source_tweets.length} tweets
                      </span>
                    </div>
                    <div className="space-y-4 max-h-64 overflow-y-auto">
                      {currentIncident.source_tweets.map((tweet, index) => (
                        <div
                          key={tweet.tweet_id || index}
                          className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                        >
                          <div className="flex items-start gap-3">
                            <div className="mt-1">
                              <Twitter className="h-5 w-5 text-blue-500" />
                            </div>
                            <div className="flex-1">
                              <div className="flex flex-wrap items-center gap-x-2 text-sm text-gray-500 mb-1">
                                <span className="font-semibold text-gray-900">
                                  {tweet.author}
                                </span>
                                <span>·</span>
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {formatTweetTime(tweet.timestamp)}
                                </span>
                              </div>
                              <p className="text-gray-800 text-sm leading-relaxed">
                                {tweet.text}
                              </p>
                              {tweet.engagement && (
                                <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                                  {(tweet.engagement.replies as number | undefined) && (
                                    <div className="flex items-center gap-1">
                                      <MessageCircle className="h-3 w-3" />
                                      <span>{String(tweet.engagement.replies)}</span>
                                    </div>
                                  )}
                                  {(tweet.engagement.retweets as number | undefined) && (
                                    <div className="flex items-center gap-1">
                                      <Repeat className="h-3 w-3" />
                                      <span>{String(tweet.engagement.retweets)}</span>
                                    </div>
                                  )}
                                  {(tweet.engagement.likes as number | undefined) && (
                                    <div className="flex items-center gap-1">
                                      <Heart className="h-3 w-3" />
                                      <span>{String(tweet.engagement.likes)}</span>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}

                      {currentIncident.source_tweets.length === 0 && (
                        <div className="text-center py-8">
                          <Twitter className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                          <p className="text-gray-500 text-sm">
                            No tweets associated with this incident yet
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Other Incidents Navigation */}
            {incidents.length > 1 && (
              <div className="mt-6">
                <div className="rounded-3xl bg-white/65 backdrop-blur-sm shadow-[0_10px_30px_rgba(0,0,0,0.08)] ring-1 ring-black/5 p-4">
                  <div className="rounded-2xl bg-white p-4">
                    <h3 className="text-lg font-bold mb-3 text-center">
                      Other Generated Incidents
                    </h3>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {incidents
                        .filter(
                          (incident) => incident.id !== currentIncident?.id
                        )
                        .map((incident) => (
                          <button
                            key={incident.id}
                            onClick={() => {
                              const dateParam = historyDate
                                ? `?date=${historyDate}`
                                : "";
                              navigate(`/incident/${incident.id}${dateParam}`);
                            }}
                            className="flex-shrink-0 p-3 border border-gray-200 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors min-w-[200px]"
                          >
                            <div className="text-left">
                              <div className="flex items-center gap-2 mb-1">
                                <span
                                  className={`w-2 h-2 rounded-full ${getSeverityColor(
                                    incident.severity
                                  )}`}
                                />
                                <p className="font-semibold text-sm">
                                  {incident.incident_type}
                                </p>
                              </div>
                              <p className="text-xs text-gray-500">
                                {incident.location}
                              </p>
                              <p className="text-xs text-gray-400 mt-1">
                                {incident.source_tweets.length} tweet
                                {incident.source_tweets.length !== 1 ? "s" : ""}
                              </p>
                            </div>
                          </button>
                        ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12">
            <AlertCircle className="h-16 w-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-600 dark:text-gray-400 mb-2">
              No Incidents Generated Yet
            </h2>
            <p className="text-gray-500 dark:text-gray-400 mb-6">
              Incidents will automatically appear here when tweets are analyzed
              and disaster-related content is detected.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 max-w-md mx-auto">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> Incidents are automatically generated
                from tweet analysis by the LightHouse AI system.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
