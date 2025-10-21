import { Activity, TrendingUp, Globe, LogOut, User, RefreshCw } from 'lucide-react';
import { useUser, useClerk } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import MapWidget from './MapWidget'
import type { Incident } from '../data/incidents';

// Label mappings
const INCIDENT_TYPES: { [key: number]: string } = {
  0: "No Useful Info",
  1: "Earthquake",
  2: "Tornado",
  3: "Flood",
  4: "Hurricane",
  5: "Wildfire"
};

interface BlueskyPost {
  author: {
    handle: string;
    displayName: string;
  };
  createdAt: string;
  text: string;
  initial_label: number;
  manual_label?: number;
  filter_reason?: string;
}

interface ProcessedIncident extends Incident {
  author: string;
  description: string;
  status: string;
  tags: string[];
  created_at: string;
}

export default function Dashboard() {
  const { user } = useUser();
  const { signOut } = useClerk();
  const navigate = useNavigate();
  const displayName = user?.firstName || user?.username || "User";
  
  const [viewMode, setViewMode] = useState<"points" | "heat">("points");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedIncidentType, setSelectedIncidentType] = useState<string | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [incidents, setIncidents] = useState<ProcessedIncident[]>([]);
  const [activeIncidents, setActiveIncidents] = useState(0);
  const [postsPerMin, setPostsPerMin] = useState(0);
  const [activeStates, setActiveStates] = useState(0);
  const [loading, setLoading] = useState(true);
  
  const currentDate = new Date().toLocaleDateString('en-US', {
    month: '2-digit',
    day: '2-digit',
    year: 'numeric'
  });

  // Fetch and parse JSONL file
  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch the JSONL file from public folder
      const response = await fetch('/manual_labeled_mc.jsonl');
      const text = await response.text();
      
      // Parse JSONL (each line is a separate JSON object)
      const lines = text.trim().split('\n');
      const posts: BlueskyPost[] = lines
        .filter(line => line.trim())
        .map(line => JSON.parse(line));
      
      console.log(`Loaded ${posts.length} posts from JSONL file`);
      
      // Process posts into incidents
      const processedIncidents: ProcessedIncident[] = [];
      let incidentCounter = 1;
      
      // Process ALL posts, including label 0
      posts.forEach(post => {
        const label = post.manual_label ?? post.initial_label;
        const incidentType = INCIDENT_TYPES[label] || "Unknown";
        
        // Extract location from text (simple approach)
        let city = "Location TBD";
        const text_lower = post.text.toLowerCase();
        const locations = [
          'Alaska', 'Indonesia', 'New Zealand', 'Japan', 'Afghanistan',
          'Oklahoma', 'Chile', 'Austin', 'Texas', 'California', 'Florida',
          'Louisiana', 'North Carolina', 'Philippines', 'Italy', 'Namibia',
          'Spain', 'Bolivia', 'Colombia', 'Nova Scotia', 'Fiji Islands',
          'Mexico', 'Oregon', 'Washington', 'Nevada', 'Arizona', 'North Dakota',
          'Massachusetts', 'Illinois', 'Georgia', 'Virginia', 'Pennsylvania',
          'Colorado', 'Montana', 'Wyoming', 'Utah', 'Idaho', 'Kentucky'
        ];
        
        for (const place of locations) {
          if (text_lower.includes(place.toLowerCase())) {
            city = place;
            break;
          }
        }
        
        // Determine severity
        let severity: 1 | 2 | 3 = 2; // medium
        if (/major|severe|critical|devastating|massive|ef-5|ef5|category 5|cat 5/i.test(post.text)) {
          severity = 3; // high
        } else if (/minor|small|weak/i.test(post.text)) {
          severity = 1; // low
        }
        
        // Map incident type to the allowed types
        const typeMapping: Record<string, "Flood" | "Wildfire" | "Earthquake" | "Storm" | "Tornado"> = {
          "Earthquake": "Earthquake",
          "Tornado": "Tornado",
          "Flood": "Flood",
          "Hurricane": "Storm",
          "Wildfire": "Wildfire",
          "No Useful Info": "Storm" // Default type for label 0
        };
        
        const mappedType = typeMapping[incidentType] || "Storm";
        
        processedIncidents.push({
          id: `INC-${String(incidentCounter).padStart(6, '0')}`,
          title: `${incidentType} - ${city}`,
          type: mappedType,
          severity,
          radiusKm: 10,
          city,
          lat: 0,
          lng: 0,
          description: post.text.substring(0, 300) + (post.text.length > 300 ? '...' : ''),
          status: "active",
          tags: [incidentType.toLowerCase().replace(' ', '_'), city.toLowerCase().replace(' ', '_')],
          created_at: post.createdAt,
          author: post.author.handle
        });
        
        incidentCounter++;
      });
      
      // Sort incidents by creation date (most recent first)
      processedIncidents.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      
      console.log(`Processed ${processedIncidents.length} incidents from JSONL`);
      
      setIncidents(processedIncidents);
      
      // Calculate metrics from the actual data
      setActiveIncidents(processedIncidents.length);
      
      // Calculate posts per minute based on actual post count
      const totalPosts = posts.length;
      setPostsPerMin(Math.round(totalPosts / 60)); // Rough estimate
      
      // Calculate unique locations (states/countries)
      const uniqueLocations = new Set(
        processedIncidents
          .map(inc => inc.city)
          .filter(loc => loc !== "Location TBD")
      );
      setActiveStates(uniqueLocations.size);
      
    } catch (error) {
      console.error('Error loading JSONL file:', error);
      setActiveIncidents(0);
      setPostsPerMin(0);
      setActiveStates(0);
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  const handleProfile = () => {
    navigate("/profile");
  };

  const handleRefresh = () => {
    fetchDashboardData();
  };

  // Helper function to calculate time ago
  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diffInSeconds = Math.floor((now.getTime() - then.getTime()) / 1000);
    
    if (diffInSeconds < 60) {
      return `${diffInSeconds} sec ago`;
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} min ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  };

  // Filter incidents based on search query and selected type
  const filteredIncidents = incidents.filter(incident => {
    const matchesType = !selectedIncidentType || incident.type === selectedIncidentType;
    return matchesType;
  });

  // Search results - separate from Live Feed
  const searchResults = incidents.filter(incident => 
    searchQuery.trim() && (
      incident.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.city.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  // Handler for clicking incident type tags
  const handleIncidentTypeClick = (type: string) => {
    if (selectedIncidentType === type) {
      // If clicking the same type, deselect it
      setSelectedIncidentType(null);
    } else {
      // Select the new type
      setSelectedIncidentType(type);
    }
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

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="text-lg font-semibold text-gray-700">Loading incidents from JSONL file...</div>
          </div>
        ) : (
          <>
            <div className="mb-4 flex items-center gap-3">
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
              
              <div className="text-sm text-gray-600 ml-auto">
                Showing {filteredIncidents.length} of {incidents.length} incidents
              </div>
            </div>

            {/* Map Card */}
            <div className="bg-white/45 backdrop-blur-sm rounded-2xl p-4 shadow mb-4">
              <MapWidget
                incidents={filteredIncidents}
                heightClass="h-72"
                initialCenter={[20, 0]}
                initialZoom={2}
                lockSingleWorld
                viewMode={viewMode}
                onPointClick={(id) => navigate(`/incident/${id}`)}
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
                        Found {searchResults.length} incident{searchResults.length !== 1 ? 's' : ''}
                      </span>
                      <button
                        onClick={() => {
                          setSearchQuery('');
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
                            <div className="font-semibold text-gray-900">{incident.title}</div>
                            <div className="text-sm text-gray-600 mt-1">{incident.city}</div>
                            <div className="text-xs text-gray-500 mt-1">
                              {incident.type} • @{incident.author}
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
              
              {showSearchResults && searchResults.length === 0 && searchQuery.trim() && (
                <div className="absolute z-10 w-full mt-2 bg-white rounded-xl shadow-lg p-4">
                  <p className="text-sm text-gray-500 text-center">
                    No incidents found matching "{searchQuery}"
                  </p>
                </div>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
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
                <div className="text-2xl font-bold mt-1">{activeStates} Locations</div>
              </div>
            </div>

            {/* Content cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
                <h3 className="font-semibold mb-2">Live Feed</h3>
                <div className="space-y-2 max-h-[180px] overflow-y-auto">
                  {filteredIncidents.slice(0, 10).map((incident) => (
                    <div key={incident.id} className="text-sm border-b pb-2 hover:bg-gray-50 cursor-pointer transition-colors" onClick={() => navigate(`/incident/${incident.id}`)}>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="font-medium text-gray-800">{incident.type}</div>
                          <div className="text-gray-600 text-xs">{incident.city}</div>
                          <div className="text-gray-500 text-xs mt-1">@{incident.author}</div>
                          <div className="text-gray-400 text-xs mt-1">
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
              <div className="bg-white rounded-2xl p-6 min-h-[220px] shadow ring-1 ring-black/5">
                <h3 className="font-semibold mb-2">Incident Types</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(
                    incidents.reduce((acc, inc) => {
                      acc[inc.type] = (acc[inc.type] || 0) + 1;
                      return acc;
                    }, {} as Record<string, number>)
                  ).map(([type, count]) => (
                    <span 
                      key={type} 
                      onClick={() => handleIncidentTypeClick(type)}
                      className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-all ${
                        selectedIncidentType === type 
                          ? 'bg-pink-600 text-white ring-2 ring-pink-400' 
                          : 'bg-gray-900 text-white hover:bg-gray-700'
                      }`}
                    >
                      {type} ({count})
                    </span>
                  ))}
                </div>
                {selectedIncidentType && (
                  <div className="mt-3 text-sm text-gray-600">
                    Filtering by: <span className="font-semibold">{selectedIncidentType}</span>
                    <button 
                      onClick={() => setSelectedIncidentType(null)}
                      className="ml-2 text-pink-600 hover:text-pink-700 underline"
                    >
                      Clear filter
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
