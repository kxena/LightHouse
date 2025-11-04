import { useState, useEffect } from 'react';
import { User, Mail, Phone, Shield, Edit3, Save, X, ArrowLeft, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useUser } from '@clerk/clerk-react';

export default function Profile() {
  const { user, isLoaded } = useUser();
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('personal');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isChangingEmail, setIsChangingEmail] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [emailChangeError, setEmailChangeError] = useState('');
  const [emailChangeSuccess, setEmailChangeSuccess] = useState(false);
  const [isUpdatingPhone, setIsUpdatingPhone] = useState(false);
  const [phoneUpdateError, setPhoneUpdateError] = useState('');
  const [phoneUpdateSuccess, setPhoneUpdateSuccess] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    phone: '',
    role: 'Administrator'
  });

  // Update profile data when user data is loaded
  useEffect(() => {
    if (user && isLoaded) {
      setProfileData({
        name: user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'User',
        email: user.primaryEmailAddress?.emailAddress || '',
        phone: user.phoneNumbers?.[0]?.phoneNumber || '',
        role: 'Administrator' // You can customize this based on your needs
      });
    }
  }, [user, isLoaded]);

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (!user) return;
    
    setIsSaving(true);
    setSaveError('');
    setSaveSuccess(false);
    
    try {
      // Update the user's profile in Clerk
      await user.update({
        firstName: profileData.name.split(' ')[0] || '',
        lastName: profileData.name.split(' ').slice(1).join(' ') || '',
      });
      
      // If email is different, we need to handle email verification
      if (profileData.email !== user.primaryEmailAddress?.emailAddress) {
        // Note: Email changes require verification in Clerk
        // For now, we'll show a message that email changes need verification
        setSaveError('Email changes require verification. Please use the email verification process.');
        setIsSaving(false);
        return;
      }
      
      setSaveSuccess(true);
      setIsEditing(false);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
      
    } catch (error: any) {
      console.error('Error updating profile:', error);
      setSaveError(error.message || 'Failed to update profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    // Reset profile data to original user data
    if (user && isLoaded) {
      setProfileData({
        name: user.fullName || `${user.firstName || ''} ${user.lastName || ''}`.trim() || 'User',
        email: user.primaryEmailAddress?.emailAddress || '',
        phone: user.phoneNumbers?.[0]?.phoneNumber || '',
        role: 'Administrator'
      });
    }
    setIsEditing(false);
    setSaveError('');
    setSaveSuccess(false);
  };

  const handleInputChange = (field: string, value: string) => {
    setProfileData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleEmailChange = async () => {
    if (!user || !newEmail) return;
    
    setIsChangingEmail(true);
    setEmailChangeError('');
    setEmailChangeSuccess(false);
    
    try {
      // Create a new email address for the user
      await user.createEmailAddress({ email: newEmail });
      
      // Send verification email
      const emailAddress = user.emailAddresses.find(email => email.emailAddress === newEmail);
      if (emailAddress) {
        await emailAddress.prepareVerification({ strategy: 'email_code' });
        setEmailChangeSuccess(true);
        setNewEmail('');
      }
      
    } catch (error: any) {
      console.error('Error changing email:', error);
      setEmailChangeError(error.message || 'Failed to change email. Please try again.');
    } finally {
      setIsChangingEmail(false);
    }
  };

  const handlePhoneUpdate = async () => {
    if (!user || !profileData.phone) return;
    
    setIsUpdatingPhone(true);
    setPhoneUpdateError('');
    setPhoneUpdateSuccess(false);
    
    try {
      // Create a new phone number for the user
      await user.createPhoneNumber({ phoneNumber: profileData.phone });
      
      setPhoneUpdateSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => setPhoneUpdateSuccess(false), 3000);
      
    } catch (error: any) {
      console.error('Error updating phone:', error);
      setPhoneUpdateError(error.message || 'Failed to update phone number. Please try again.');
    } finally {
      setIsUpdatingPhone(false);
    }
  };

  // Show loading state while user data is being fetched
  if (!isLoaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-center items-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading profile...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error state if user is not authenticated
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-center items-center h-96">
            <div className="text-center">
              <p className="text-gray-600 mb-4">Please sign in to view your profile.</p>
              <Link
                to="/sign-in"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors duration-200"
              >
                Sign In
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="flex items-center gap-2 bg-white/60 backdrop-blur-sm px-4 py-2 rounded-lg shadow-lg border-2 border-white hover:bg-white/80 transition-colors duration-200"
            >
              <ArrowLeft className="w-5 h-5 text-gray-700" />
              <span className="text-gray-700 font-medium">Back to Dashboard</span>
            </Link>
            <div>
              <h1 className="text-4xl font-bold">
                <span className="text-gray-800">Profile</span>
                <span className="text-pink-600"> Page</span>
              </h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <User className="w-5 h-5 text-gray-700" />
              <span className="text-gray-600">LightHouse</span>
            </div>
            <p className="text-gray-600">09/19/2025</p>
          </div>
        </div>

        {/* Success/Error Messages */}
        {saveSuccess && (
          <div className="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
            ✅ Profile updated successfully!
          </div>
        )}
        
        {saveError && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            ❌ {saveError}
          </div>
        )}

        {/* Main Profile Card */}
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-8 shadow-lg border-2 border-white mb-6">
          <div className="flex flex-col items-center text-center">
            {/* Avatar */}
            <div className="w-24 h-24 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center mb-4">
              <User className="w-12 h-12 text-white" />
            </div>
            
            {/* User Info */}
            <h2 className="text-3xl font-bold text-gray-800 mb-2">{profileData.name}</h2>
            <p className="text-gray-600 mb-1">{profileData.email}</p>
            <p className="text-sm text-gray-500 mb-6">{profileData.role}</p>
            
            {/* Edit Profile Button */}
            <button
              onClick={handleEdit}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2"
            >
              <Edit3 className="w-4 h-4" />
              Edit Profile
            </button>
          </div>
        </div>

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-800 mb-2">2</p>
              <p className="text-sm text-gray-600">Alerts Managed</p>
            </div>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-800 mb-2">99.9%</p>
              <p className="text-sm text-gray-600">System Uptime Contributions</p>
            </div>
          </div>
          
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-800 mb-2">5</p>
              <p className="text-sm text-gray-600">Regions Monitored</p>
            </div>
          </div>
        </div>

        {/* Detailed Information Section */}
        <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 shadow-lg border-2 border-white">
          {/* Tabs */}
          <div className="flex gap-6 mb-6 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('personal')}
              className={`pb-2 font-semibold ${
                activeTab === 'personal'
                  ? 'text-gray-800 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Personal Details
            </button>
            <button
              onClick={() => setActiveTab('preferences')}
              className={`pb-2 font-semibold ${
                activeTab === 'preferences'
                  ? 'text-gray-800 border-b-2 border-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Preferences
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'personal' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <User className="w-5 h-5 text-gray-500" />
                  <span className="font-medium text-gray-700">Name</span>
                </div>
                {isEditing ? (
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <span className="text-gray-600">{profileData.name}</span>
                )}
              </div>

              <div className="py-3 border-b border-gray-100">
                <div className="flex items-center gap-3 mb-3">
                  <Mail className="w-5 h-5 text-gray-500" />
                  <span className="font-medium text-gray-700">Email</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">{profileData.email}</span>
                  <button
                    onClick={() => setIsChangingEmail(!isChangingEmail)}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                  >
                    {isChangingEmail ? 'Cancel' : 'Change Email'}
                  </button>
                </div>
                
                {isChangingEmail && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          New Email Address
                        </label>
                        <input
                          type="email"
                          value={newEmail}
                          onChange={(e) => setNewEmail(e.target.value)}
                          placeholder="Enter new email address"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleEmailChange}
                          disabled={isChangingEmail || !newEmail}
                          className={`px-4 py-2 rounded-md text-sm font-medium ${
                            isChangingEmail || !newEmail
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                              : 'bg-blue-600 hover:bg-blue-700 text-white'
                          }`}
                        >
                          {isChangingEmail ? 'Sending...' : 'Send Verification Email'}
                        </button>
                        <button
                          onClick={() => {
                            setIsChangingEmail(false);
                            setNewEmail('');
                            setEmailChangeError('');
                          }}
                          className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-md text-sm font-medium"
                        >
                          Cancel
                        </button>
                      </div>
                      {emailChangeError && (
                        <p className="text-red-600 text-sm">{emailChangeError}</p>
                      )}
                      {emailChangeSuccess && (
                        <div className="flex items-center gap-2 text-green-600 text-sm">
                          <CheckCircle className="w-4 h-4" />
                          Verification email sent! Check your inbox.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <div className="py-3 border-b border-gray-100">
                <div className="flex items-center gap-3 mb-3">
                  <Phone className="w-5 h-5 text-gray-500" />
                  <span className="font-medium text-gray-700">Phone</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">{profileData.phone || 'No phone number'}</span>
                  {isEditing && (
                    <button
                      onClick={handlePhoneUpdate}
                      disabled={isUpdatingPhone || !profileData.phone}
                      className={`px-3 py-1 rounded-md text-sm font-medium ${
                        isUpdatingPhone || !profileData.phone
                          ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      {isUpdatingPhone ? 'Updating...' : 'Update Phone'}
                    </button>
                  )}
                </div>
                {isEditing && (
                  <div className="mt-2">
                    <input
                      type="tel"
                      value={profileData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="Enter phone number (e.g., +1234567890)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {phoneUpdateError && (
                      <p className="text-red-600 text-sm mt-1">{phoneUpdateError}</p>
                    )}
                    {phoneUpdateSuccess && (
                      <div className="flex items-center gap-2 text-green-600 text-sm mt-1">
                        <CheckCircle className="w-4 h-4" />
                        Phone number updated successfully!
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="flex justify-between items-center py-3">
                <div className="flex items-center gap-3">
                  <Shield className="w-5 h-5 text-gray-500" />
                  <span className="font-medium text-gray-700">Role</span>
                </div>
                {isEditing ? (
                  <select
                    value={profileData.role}
                    onChange={(e) => handleInputChange('role', e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Administrator">Administrator</option>
                    <option value="Manager">Manager</option>
                    <option value="Operator">Operator</option>
                    <option value="Viewer">Viewer</option>
                  </select>
                ) : (
                  <span className="text-gray-600">{profileData.role}</span>
                )}
              </div>

              {/* Edit Actions */}
              {isEditing && (
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className={`px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2 ${
                      isSaving
                        ? 'bg-gray-400 cursor-not-allowed text-white'
                        : 'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                  >
                    {isSaving ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4" />
                        Save Changes
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleCancel}
                    disabled={isSaving}
                    className={`px-4 py-2 rounded-lg transition-colors duration-200 flex items-center gap-2 ${
                      isSaving
                        ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                        : 'bg-gray-500 hover:bg-gray-600 text-white'
                    }`}
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Notification Settings</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input type="checkbox" className="rounded border-gray-300" defaultChecked />
                    <span className="text-gray-700">Email notifications for critical alerts</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input type="checkbox" className="rounded border-gray-300" defaultChecked />
                    <span className="text-gray-700">SMS notifications for emergency incidents</span>
                  </label>
                  <label className="flex items-center gap-3">
                    <input type="checkbox" className="rounded border-gray-300" />
                    <span className="text-gray-700">Weekly summary reports</span>
                  </label>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Display Preferences</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Theme</span>
                    <select className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                      <option value="auto">Auto</option>
                    </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-700">Timezone</span>
                    <select className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                      <option value="UTC-8">Pacific Time (UTC-8)</option>
                      <option value="UTC-5">Eastern Time (UTC-5)</option>
                      <option value="UTC">UTC</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
