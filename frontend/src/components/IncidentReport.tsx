import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Twitter, MessageCircle, Repeat, Heart, Share2 } from "lucide-react";
import MapWidget from "./MapWidget";
import { incidents } from "../data/incidents";

export default function IncidentReport() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const incident = incidents.find((i) => i.id === id) ?? incidents[0];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-6 lg:p-10">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <div className="relative mb-6 lg:mb-10 flex items-center">
          <button
            className="absolute left-0 p-2 rounded-full hover:bg-white/40 transition"
            onClick={() => navigate("/dashboard")}
            aria-label="Back to Dashboard"
          >
            <ArrowLeft className="h-6 w-6 text-gray-700" />
          </button>

          <div className="w-full text-center">
            <h1 className="text-3xl font-extrabold tracking-wide">
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-700 to-pink-600">
                LightHouse
              </span>
            </h1>
          </div>
        </div>

        {/* 2x2 Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Map (top-left) */}
          <div className="lg:col-span-6">
            <div className="rounded-3xl bg-white/55 backdrop-blur-sm shadow ring-1 ring-black/5 p-4">
              <MapWidget
                incidents={[incident]}
                focusId={incident.id}
                showRings
                heightClass="h-64"
                lockSingleWorld
              />
            </div>
          </div>

          {/* Summary (top-right) */}
          <div className="lg:col-span-6">
            <div className="rounded-3xl bg-white/65 backdrop-blur-sm shadow ring-1 ring-black/5 p-6">
              <div className="rounded-2xl bg-white p-6">
                <h2 className="text-3xl font-extrabold tracking-wide text-center mb-2">
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-pink-600 to-rose-600">
                    {incident.type}
                  </span>
                </h2>
                <p className="text-center text-gray-700 leading-relaxed max-w-lg mx-auto">
                  Power outages reported across downtown area. Estimated restoration time:
                  <span className="font-semibold"> 4–6 hours</span>.
                </p>
                <p className="mt-5 text-center text-lg tracking-wide text-gray-900 font-semibold">
                  {incident.city}
                  {incident.state ? `, ${incident.state}` : ""}
                </p>
              </div>
            </div>
          </div>

          {/* Severity + Tags (bottom-left) */}
          <div className="lg:col-span-6">
            <div className="rounded-3xl bg-white/65 backdrop-blur-sm shadow ring-1 ring-black/5 p-6">
              <div className="rounded-2xl bg-white p-6">
                <div className="flex items-center gap-3 mb-4">
                  <h3 className="text-2xl font-bold">Severity:</h3>
                  <span
                    className={`inline-flex h-3.5 w-3.5 rounded-full ${
                      incident.severity === 3
                        ? "bg-red-500 shadow-[0_0_0_6px_rgba(239,68,68,0.18)]"
                        : incident.severity === 2
                        ? "bg-yellow-500 shadow-[0_0_0_6px_rgba(234,179,8,0.18)]"
                        : "bg-green-500 shadow-[0_0_0_6px_rgba(34,197,94,0.18)]"
                    }`}
                  />
                </div>

                <div className="flex flex-wrap gap-3">
                  {["#PowerOutage", "#Downtown", "#Restoration", "#Austin"].map((t) => (
                    <span
                      key={t}
                      className="px-3 py-1 rounded-full text-sm font-medium bg-gray-900 text-white/95 shadow-sm"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Social Feed (bottom-right) */}
          <div className="lg:col-span-6">
            <div className="rounded-3xl bg-white/65 backdrop-blur-sm shadow ring-1 ring-black/5 p-4">
              <div className="rounded-2xl bg-white p-4 lg:p-5 ring-2 ring-blue-300/60 shadow">
                <div className="space-y-5">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="pb-4 border-b last:border-b-0 border-gray-200/70">
                      <div className="flex items-start gap-3">
                        <div className="mt-1">
                          <Twitter className="h-6 w-6" />
                        </div>
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-x-2 text-sm text-gray-500">
                            <span className="font-semibold text-gray-900">Twitter</span>
                            <span>@Twitter</span>
                            <span>·</span>
                            <span>Oct 29</span>
                          </div>
                          <p className="mt-1 text-gray-800">BIG NEWS | ok jk still Twitter</p>
                          <div className="mt-2 flex items-center gap-5 text-sm text-gray-500">
                            <div className="flex items-center gap-1">
                              <MessageCircle className="h-4 w-4" />
                              <span>6.8k</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Repeat className="h-4 w-4" />
                              <span>35.9k</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <Heart className="h-4 w-4" />
                              <span>267.1k</span>
                            </div>
                            <Share2 className="h-4 w-4 ml-auto" />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          {/* End Social Feed */}
        </div>
      </div>
    </div>
  );
}
