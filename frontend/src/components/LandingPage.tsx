import { useNavigate } from "react-router-dom";
import { SignedIn, SignedOut } from "@clerk/clerk-react";
import { Zap, Map, MapPin, Filter, AlertTriangle, Clock, Globe2, Users, CheckCircle } from "lucide-react";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200">
      {/* Navigation Header */}
      <nav className="bg-white/60 backdrop-blur-md shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-3">
              <img
                src="src/assets/logo.png"
                alt="LightHouse Logo"
                className="h-10 w-10 object-contain"
              />
              <span className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                LightHouse
              </span>
            </div>
            <div className="flex gap-4">
              <SignedOut>
                <button
                  onClick={() => navigate("/sign-in")}
                  className="px-4 py-2 text-gray-700 hover:text-purple-600 font-medium transition-colors"
                >
                  Sign In
                </button>
                <button
                  onClick={() => navigate("/sign-up")}
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg shadow-md hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
                >
                  Get Started
                </button>
              </SignedOut>
              <SignedIn>
                <button
                  onClick={() => navigate("/dashboard")}
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg shadow-md hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
                >
                  Go to Dashboard
                </button>
              </SignedIn>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="text-center">
          <div className="flex justify-center mb-8">
            <img
              src="src/assets/logo.png"
              alt="LightHouse Logo"
              className="h-32 w-32 object-contain animate-fadeIn"
            />
          </div>
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-6 animate-fadeIn">
            Real-Time Disaster
            <span className="block bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent">
              Response Intelligence
            </span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-700 mb-12 max-w-3xl mx-auto animate-fadeIn">
            Harness the power of AI to monitor, analyze, and respond to crises
            in real-time through social media intelligence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fadeIn">
            <SignedOut>
              <button
                onClick={() => navigate("/sign-up")}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg font-semibold rounded-xl shadow-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
              >
                Start Monitoring Now
              </button>
              <button
                onClick={() => navigate("/sign-in")}
                className="px-8 py-4 bg-white/80 backdrop-blur-sm text-gray-800 text-lg font-semibold rounded-xl shadow-lg hover:bg-white transition-all duration-200"
              >
                Sign In
              </button>
            </SignedOut>
            <SignedIn>
              <button
                onClick={() => navigate("/dashboard")}
                className="px-8 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white text-lg font-semibold rounded-xl shadow-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
              >
                View Dashboard
              </button>
            </SignedIn>
          </div>
        </div>
      </section>

      {/* Stats Section - Move up after hero */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-8 shadow-lg ring-1 ring-black/5 text-center">
            <div className="text-5xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
              24/7
            </div>
            <p className="text-gray-700 font-medium">Real-Time Monitoring</p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-8 shadow-lg ring-1 ring-black/5 text-center">
            <div className="text-5xl font-bold bg-gradient-to-r from-pink-600 to-blue-600 bg-clip-text text-transparent mb-2">
              10K+
            </div>
            <p className="text-gray-700 font-medium">Incidents Analyzed Daily</p>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-8 shadow-lg ring-1 ring-black/5 text-center">
            <div className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
              1000+
            </div>
            <p className="text-gray-700 font-medium">Global Locations</p>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
          How LightHouse Works
        </h2>
        <p className="text-center text-gray-700 mb-16 max-w-2xl mx-auto">
          Our intelligent pipeline processes disaster information in real-time
        </p>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="relative">
            <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl shadow-lg ring-1 ring-black/5 text-center">
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">1</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Collect</h3>
              <p className="text-sm text-gray-700">
                Monitor social media streams from Bluesky and other platforms
              </p>
            </div>
            {/* Connector arrow for desktop */}
            <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gradient-to-r from-pink-400 to-blue-400"></div>
          </div>

          <div className="relative">
            <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl shadow-lg ring-1 ring-black/5 text-center">
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">2</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Analyze</h3>
              <p className="text-sm text-gray-700">
                AI classifies incident types, severity, and extracts key details
              </p>
            </div>
            <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gradient-to-r from-blue-400 to-purple-400"></div>
          </div>

          <div className="relative">
            <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl shadow-lg ring-1 ring-black/5 text-center">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white font-bold text-xl">3</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-2">Map</h3>
              <p className="text-sm text-gray-700">
                Geolocate incidents and visualize on interactive heatmaps
              </p>
            </div>
            <div className="hidden md:block absolute top-1/2 -right-3 w-6 h-0.5 bg-gradient-to-r from-purple-400 to-pink-400"></div>
          </div>

          <div className="bg-white/60 backdrop-blur-sm p-6 rounded-2xl shadow-lg ring-1 ring-black/5 text-center">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-xl">4</span>
            </div>
            <h3 className="font-bold text-gray-900 mb-2">Alert</h3>
            <p className="text-sm text-gray-700">
              Deliver real-time notifications and actionable insights
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
          Powerful Features for Crisis Management
        </h2>
        <p className="text-center text-gray-700 mb-16 max-w-2xl mx-auto">
          Everything you need to monitor, analyze, and respond to disasters effectively
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {/* Feature 1 */}
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-300 ring-1 ring-black/5">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-6">
              <Zap className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              AI-Powered Analysis
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Advanced LLM integration classifies crisis types, analyzes
              sentiment, and extracts critical metadata from social media posts
              in real-time.
            </p>
          </div>

          {/* Feature 2 */}
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-300 ring-1 ring-black/5">
            <div className="w-14 h-14 bg-gradient-to-br from-pink-500 to-blue-500 rounded-xl flex items-center justify-center mb-6">
              <Map className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Interactive Heatmaps
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Visualize incident density and severity with dynamic heatmaps and
              geographic clustering to identify hotspots and emerging trends.
            </p>
          </div>

          {/* Feature 3 */}
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-300 ring-1 ring-black/5">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
              <AlertTriangle className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Real-Time Monitoring
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Track disasters as they unfold with live data streams from
              Bluesky and other social platforms, ensuring you're always
              informed.
            </p>
          </div>

          {/* Feature 4 - Location-Based Search */}
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-300 ring-1 ring-black/5">
            <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center mb-6">
              <MapPin className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Location-Based Alerts
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Enter your location to discover nearby incidents and disasters,
              keeping you informed about crises affecting your area and community.
            </p>
          </div>

          {/* Feature 5 */}
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg hover:shadow-xl hover:bg-white/80 transition-all duration-300 ring-1 ring-black/5">
            <div className="w-14 h-14 bg-gradient-to-br from-pink-500 to-purple-500 rounded-xl flex items-center justify-center mb-6">
              <Filter className="w-7 h-7 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Customizable Filters
            </h3>
            <p className="text-gray-700 leading-relaxed">
              Filter incidents by type, severity, location, and time period to
              focus on what matters most to your response team.
            </p>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
          Who Uses LightHouse?
        </h2>
        <p className="text-center text-gray-700 mb-16 max-w-2xl mx-auto">
          Trusted by professionals who need real-time disaster intelligence
        </p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg ring-1 ring-black/5 hover:bg-white/80 transition-all duration-300">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mb-4">
              <Users className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Emergency Responders
            </h3>
            <p className="text-gray-700">
              First responders use LightHouse to identify emerging crises and coordinate rapid response efforts.
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg ring-1 ring-black/5 hover:bg-white/80 transition-all duration-300">
            <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-blue-500 rounded-xl flex items-center justify-center mb-4">
              <Globe2 className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              Government Agencies
            </h3>
            <p className="text-gray-700">
              Public safety agencies monitor threats and mobilize resources based on real-time incident data.
            </p>
          </div>

          <div className="bg-white/60 backdrop-blur-sm p-8 rounded-2xl shadow-lg ring-1 ring-black/5 hover:bg-white/80 transition-all duration-300">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center mb-4">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-3">
              NGOs & Relief Organizations
            </h3>
            <p className="text-gray-700">
              Humanitarian groups track disasters globally to deploy aid and resources where needed most.
            </p>
          </div>
        </div>
      </section>

      {/* Why Choose LightHouse Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-12 shadow-xl ring-1 ring-black/5">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            Why Choose LightHouse?
          </h2>
          <p className="text-center text-gray-700 mb-12 max-w-2xl mx-auto">
            The most advanced disaster response intelligence platform available
          </p>
          <div className="grid md:grid-cols-2 gap-8">
            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Real-Time Updates</h3>
                <p className="text-gray-700">
                  Get instant alerts as incidents unfold, with data refreshed every minute from live social media streams.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">AI-Powered Accuracy</h3>
                <p className="text-gray-700">
                  Advanced machine learning models trained on thousands of incidents ensure precise classification and analysis.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Global Coverage</h3>
                <p className="text-gray-700">
                  Monitor disasters across 1000+ locations worldwide with comprehensive social media monitoring.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Easy Integration</h3>
                <p className="text-gray-700">
                  Simple, intuitive dashboard that requires no technical expertise to start monitoring crises immediately.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 rounded-3xl shadow-2xl p-12 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Transform Crisis Response?
          </h2>
          <p className="text-xl text-white/95 mb-8 max-w-2xl mx-auto">
            Join emergency responders and organizations using LightHouse to save
            lives through intelligent disaster monitoring.
          </p>
          <SignedOut>
            <button
              onClick={() => navigate("/sign-up")}
              className="px-8 py-4 bg-white text-purple-600 text-lg font-semibold rounded-xl shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-105"
            >
              Get Started Free
            </button>
          </SignedOut>
          <SignedIn>
            <button
              onClick={() => navigate("/dashboard")}
              className="px-8 py-4 bg-white text-purple-600 text-lg font-semibold rounded-xl shadow-lg hover:bg-gray-50 transition-all duration-200 transform hover:scale-105"
            >
              Go to Dashboard
            </button>
          </SignedIn>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-white/40 backdrop-blur-sm border-t border-white/60 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center gap-3 mb-4 md:mb-0">
              <img
                src="src/assets/logo.png"
                alt="LightHouse Logo"
                className="h-8 w-8 object-contain"
              />
              <span className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                LightHouse
              </span>
            </div>
            <p className="text-gray-700">
              © 2025 LightHouse. Disaster Response Intelligence Platform.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
