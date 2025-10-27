import { ArrowLeft } from 'lucide-react';

export default function IncidentReport() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center mb-8">
          <button className="mr-4 p-2 hover:bg-white/30 rounded-full transition">
            <ArrowLeft className="w-6 h-6 text-gray-700" />
          </button>
          <h1 className="text-4xl font-bold">
            <span className="text-gray-800">Light</span>
            <span className="text-pink-600">House</span>
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="w-full h-64 bg-gray-200 rounded-lg flex items-center justify-center">
              <p className="text-gray-500">Map Component</p>
            </div>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-full flex flex-col justify-center">
              <h2 className="text-2xl font-bold text-pink-600 mb-4">Power Outage</h2>
              <div className="space-y-2">
                <p className="text-gray-600">Content</p>
              </div>
            </div>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-full flex flex-col">
              <h2 className="text-xl font-bold mb-4">Severity: 🔴</h2>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-gray-800 text-white rounded-full text-sm">Content</span>
              </div>
            </div>
          </div>

          <div className="bg-white/40 backdrop-blur-sm rounded-2xl p-6 shadow-lg">
            <div className="bg-white rounded-xl p-6 h-full overflow-y-auto">
              <div className="space-y-4">
                <div className="border-b border-gray-200 pb-4">
                  <p className="text-gray-600">Content</p>
                </div>
                <div className="border-b border-gray-200 pb-4">
                  <p className="text-gray-600">Content</p>
                </div>
                <div className="pb-4">
                  <p className="text-gray-600">Content</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}