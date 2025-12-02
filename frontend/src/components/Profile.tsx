import { useUser } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, User as UserIcon, Edit2, Save, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { DarkModeToggle } from './DarkModeToggle';

export default function Profile() {
  const { user } = useUser();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'personal' | 'preferences' | 'location'>('personal');
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  
  // Form state for personal details
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  
  // Form state for preferences
  const [notifications, setNotifications] = useState('Enabled');
  const [language, setLanguage] = useState('English');
  const [theme, setTheme] = useState('Light');
  const [timezone, setTimezone] = useState('EST (UTC-5)');
  
  // Form state for location
  const [userCity, setUserCity] = useState('');
  const [userState, setUserState] = useState('');
  const [userLat, setUserLat] = useState<number | null>(null);
  const [userLng, setUserLng] = useState<number | null>(null);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);

  // Initialize form values when user data loads
  useEffect(() => {
    if (user) {
      setFirstName(user.firstName || '');
      setLastName(user.lastName || '');
      setPhoneNumber(user.primaryPhoneNumber?.phoneNumber || '');
    }
  }, [user]);

  // Initialize location data from localStorage
  useEffect(() => {
    const savedCity = localStorage.getItem('userCity');
    const savedState = localStorage.getItem('userState');
    const savedLat = localStorage.getItem('userLat');
    const savedLng = localStorage.getItem('userLng');
    
    if (savedCity) setUserCity(savedCity);
    if (savedState) setUserState(savedState);
    if (savedLat) setUserLat(parseFloat(savedLat));
    if (savedLng) setUserLng(parseFloat(savedLng));
  }, []);

  const displayName = user?.firstName && user?.lastName 
    ? `${user.firstName} ${user.lastName}` 
    : user?.username || "User";
  const email = user?.primaryEmailAddress?.emailAddress || "No email provided";
  const phone = user?.primaryPhoneNumber?.phoneNumber || "No phone provided";
  const role = "Administrator";

  const handleEditClick = () => {
    setIsEditing(true);
    // Reset form values to current user data
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
    setPhoneNumber(user?.primaryPhoneNumber?.phoneNumber || '');
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    // Reset form values
    setFirstName(user?.firstName || '');
    setLastName(user?.lastName || '');
    setPhoneNumber(user?.primaryPhoneNumber?.phoneNumber || '');
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Update user information with Clerk
      await user?.update({
        firstName: firstName,
        lastName: lastName,
      });

      // Reload user to get updated data
      await user?.reload();

      alert('Profile updated successfully!');
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Failed to update profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const detectLocation = () => {
    setIsDetectingLocation(true);
    
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by this browser.');
      setIsDetectingLocation(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        
        try {
          // Use a reverse geocoding service to get city/state
          const response = await fetch(
            `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=en`
          );
          
          if (response.ok) {
            const data = await response.json();
            const city = data.city || data.locality || '';
            const state = data.principalSubdivision || '';
            
            setUserCity(city);
            setUserState(state);
            setUserLat(lat);
            setUserLng(lng);
          } else {
            // Fallback: just set coordinates
            setUserLat(lat);
            setUserLng(lng);
          }
        } catch (error) {
          console.error('Error getting location details:', error);
          // Still set coordinates even if reverse geocoding fails
          setUserLat(lat);
          setUserLng(lng);
        }
        
        setIsDetectingLocation(false);
      },
      (error) => {
        console.error('Error getting location:', error);
        alert('Unable to get your location. Please check your browser permissions.');
        setIsDetectingLocation(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  const saveLocation = () => {
    // Save to localStorage
    localStorage.setItem('userCity', userCity);
    localStorage.setItem('userState', userState);
    if (userLat !== null) localStorage.setItem('userLat', userLat.toString());
    if (userLng !== null) localStorage.setItem('userLng', userLng.toString());
    
    // Dispatch event to notify other components
    window.dispatchEvent(new CustomEvent('locationUpdated'));
    
    alert('Location saved successfully!');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 dark:from-slate-800 dark:via-purple-900 dark:to-blue-900 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Dark Mode Toggle */}
        <DarkModeToggle />
        
        {/* Back Button */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 mb-6 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Dashboard
        </button>

        {/* Profile Card */}
        <div className="bg-white dark:bg-slate-700 rounded-3xl shadow-2xl p-8 mb-6">
          <div className="flex flex-col items-center">
            <div className="w-24 h-24 rounded-full border-4 border-gray-800 dark:border-gray-300 flex items-center justify-center mb-4">
              <UserIcon className="w-12 h-12 text-gray-800 dark:text-gray-300" />
            </div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-2">{displayName}</h1>
            <p className="text-gray-600 mb-1">{email}</p>
            <p className="text-gray-600 mb-4">{role}</p>
            {!isEditing ? (
              <button
                onClick={handleEditClick}
                className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white font-semibold rounded-full hover:bg-indigo-700 transition-colors"
              >
                <Edit2 className="w-4 h-4" />
                Edit Profile
              </button>
            ) : (
              <div className="flex gap-3">
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white font-semibold rounded-full hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="flex items-center gap-2 px-6 py-2 bg-gray-500 text-white font-semibold rounded-full hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  <X className="w-4 h-4" />
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Personal Details / Preferences */}
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('personal')}
              className={`flex-1 py-4 px-6 text-lg font-semibold transition-colors ${
                activeTab === 'personal'
                  ? 'text-gray-800 border-b-4 border-gray-800'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Personal Details
            </button>
            <button
              onClick={() => setActiveTab('preferences')}
              className={`flex-1 py-4 px-6 text-lg font-semibold transition-colors ${
                activeTab === 'preferences'
                  ? 'text-gray-800 border-b-4 border-gray-800'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Preferences
            </button>
            <button
              onClick={() => setActiveTab('location')}
              className={`flex-1 py-4 px-6 text-lg font-semibold transition-colors ${
                activeTab === 'location'
                  ? 'text-gray-800 border-b-4 border-gray-800'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Location
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-8">
            {activeTab === 'personal' ? (
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">First Name</span>
                  {isEditing ? (
                    <input
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Enter first name"
                    />
                  ) : (
                    <span className="text-gray-800 font-semibold">{user?.firstName || 'Not set'}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Last Name</span>
                  {isEditing ? (
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Enter last name"
                    />
                  ) : (
                    <span className="text-gray-800 font-semibold">{user?.lastName || 'Not set'}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Email</span>
                  <span className="text-gray-800 font-semibold">{email}</span>
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Phone</span>
                  {isEditing ? (
                    <input
                      type="tel"
                      value={phoneNumber}
                      onChange={(e) => setPhoneNumber(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="Enter phone number"
                    />
                  ) : (
                    <span className="text-gray-800 font-semibold">{phone}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4">
                  <span className="text-gray-600 font-medium">Role</span>
                  <span className="text-gray-800 font-semibold">{role}</span>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Notifications</span>
                  {isEditing ? (
                    <select
                      value={notifications}
                      onChange={(e) => setNotifications(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option>Enabled</option>
                      <option>Disabled</option>
                    </select>
                  ) : (
                    <span className="text-gray-800 font-semibold">{notifications}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Language</span>
                  {isEditing ? (
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option>English</option>
                      <option>Spanish</option>
                      <option>French</option>
                    </select>
                  ) : (
                    <span className="text-gray-800 font-semibold">{language}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4 border-b border-gray-200">
                  <span className="text-gray-600 font-medium">Theme</span>
                  {isEditing ? (
                    <select
                      value={theme}
                      onChange={(e) => setTheme(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option>Light</option>
                      <option>Dark</option>
                    </select>
                  ) : (
                    <span className="text-gray-800 font-semibold">{theme}</span>
                  )}
                </div>
                <div className="flex justify-between items-center pb-4">
                  <span className="text-gray-600 font-medium">Time Zone</span>
                  {isEditing ? (
                    <select
                      value={timezone}
                      onChange={(e) => setTimezone(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      <option>EST (UTC-5)</option>
                      <option>CST (UTC-6)</option>
                      <option>MST (UTC-7)</option>
                      <option>PST (UTC-8)</option>
                    </select>
                  ) : (
                    <span className="text-gray-800 font-semibold">{timezone}</span>
                  )}
                </div>
              </div>
            )}

            {/* Location Tab */}
            {activeTab === 'location' && (
              <div className="p-8">
                <div className="space-y-6">
                  <div className="flex justify-between items-center pb-4">
                    <span className="text-gray-600 font-medium">City</span>
                    <input
                      type="text"
                      value={userCity}
                      onChange={(e) => setUserCity(e.target.value)}
                      placeholder="Enter your city"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="flex justify-between items-center pb-4">
                    <span className="text-gray-600 font-medium">State</span>
                    <input
                      type="text"
                      value={userState}
                      onChange={(e) => setUserState(e.target.value)}
                      placeholder="Enter your state"
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  {userLat && userLng && (
                    <div className="flex justify-between items-center pb-4">
                      <span className="text-gray-600 font-medium">Coordinates</span>
                      <span className="text-gray-800 font-semibold">
                        {userLat.toFixed(4)}, {userLng.toFixed(4)}
                      </span>
                    </div>
                  )}
                  <div className="flex gap-4 pt-4">
                    <button
                      onClick={detectLocation}
                      disabled={isDetectingLocation}
                      className="flex-1 py-2 px-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {isDetectingLocation ? 'Detecting...' : 'Auto-Detect Location'}
                    </button>
                    <button
                      onClick={saveLocation}
                      className="flex-1 py-2 px-4 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors"
                    >
                      Save Location
                    </button>
                  </div>
                  <div className="text-sm text-gray-500 mt-2">
                    Your location is used to calculate the distance to nearby incidents and will be stored locally in your browser.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
