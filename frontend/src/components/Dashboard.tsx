import { Activity, TrendingUp, Globe, LogOut, User } from 'lucide-react';
import { useUser, useClerk } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user } = useUser();
  const { signOut } = useClerk();
  const navigate = useNavigate();
  const displayName = user?.firstName || user?.username || "User";
  
  // Format current date as MM/DD/YYYY
  const currentDate = new Date().toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric'
  });

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-7xl mx-auto">
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
