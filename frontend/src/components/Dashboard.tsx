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

        <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg mb-6">
          <div className="w-full h-64 bg-gradient-to-br from-blue-900 to-blue-700 rounded-lg flex items-center justify-center">
            <p className="text-white/50 text-lg">Map Container</p>
          </div>
        </div>

        <div className="mb-6">
          <input
            type="text"
            placeholder="Search"
            className="w-full px-4 py-3 rounded-xl bg-white/60 backdrop-blur-sm border border-gray-200 focus:outline-none focus:ring-2 focus:ring-pink-400"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Active Incidents</span>
              </div>
              <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">23</p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">System Status</span>
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">2.3K <span className="text-sm font-normal text-gray-600">posts/min</span></p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-gray-700" />
                <span className="text-sm text-gray-600">Coverage Area</span>
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            </div>
            <p className="text-4xl font-bold text-gray-800">4 States</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Live Feed</h2>
              <div className="h-full flex items-center justify-center">
                <p className="text-gray-400">Feed content</p>
              </div>
            </div>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-96">
              <h2 className="text-2xl font-bold text-gray-800 mb-4">Trending Topics</h2>
              <div className="h-full flex items-center justify-center">
                <p className="text-gray-400">Trending content</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}