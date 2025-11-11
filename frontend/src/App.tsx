import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { SignedIn, SignedOut, useClerk } from "@clerk/clerk-react";
import { Moon, Sun } from "lucide-react";
import SignInPage from "./components/SignIn";
import SignUpPage from "./components/SignUp";
import IncidentReport from "./components/IncidentReport";
import Dashboard from "./components/Dashboard";
import ErrorBoundary from "./components/ErrorBoundary";
import Profile from "./components/Profile";
import { useDarkMode } from "./hooks/useDarkMode";

export default function App() {
  const navigate = useNavigate();
  const { signOut } = useClerk();
  const { isDarkMode, toggleDarkMode } = useDarkMode();

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  return (
    <ErrorBoundary>
      <Routes>
        <Route
          path="/"
          element={
            <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-purple-100 to-blue-100 dark:from-purple-900 dark:to-blue-900">
              <SignedOut>
                <Navigate to="/sign-in" replace />
              </SignedOut>

              <SignedIn>
                {/* Dark Mode Toggle - positioned absolutely */}
                <button
                  onClick={toggleDarkMode}
                  className="fixed top-4 right-4 p-3 bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-full shadow-lg hover:bg-white dark:hover:bg-gray-800 transition-all duration-200 z-10"
                  aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {isDarkMode ? (
                    <Sun className="w-5 h-5 text-yellow-500" />
                  ) : (
                    <Moon className="w-5 h-5 text-gray-700" />
                  )}
                </button>

                <div className="flex flex-col items-center gap-8 p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full mx-4">
                  <div className="flex flex-col items-center gap-4">
                    <img
                      src="src/assets/logo.png"
                      alt="LightHouse Logo"
                      className="w-100 h-100 object-contain"
                    />
                    <div className="flex justify-center items-center h-3 mb-3">
                      <img
                        src="src/assets/title.png"
                        alt="LightHouse Logo"
                        className="object-contain max-h-12"
                      />
                    </div>
                    <p className="text-gray-600 dark:text-gray-300 text-center">
                      Your disaster response management system
                    </p>
                  </div>

                  <div className="flex flex-col gap-4 w-full">
                    <button
                      onClick={() => navigate("/dashboard")}
                      className="w-full py-3 px-6 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-semibold rounded-lg shadow-md hover:from-purple-700 hover:to-blue-700 transition-all duration-200 transform hover:scale-105"
                    >
                      Go to Dashboard
                    </button>

                    <button
                      onClick={handleSignOut}
                      className="w-full py-3 px-6 bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 font-semibold rounded-lg shadow-md hover:bg-gray-300 dark:hover:bg-gray-500 transition-all duration-200"
                    >
                      Log Out
                    </button>
                  </div>
                </div>
              </SignedIn>
            </div>
          }
        />

        <Route path="/sign-in/*" element={<SignInPage />} />
        <Route path="/sign-up/*" element={<SignUpPage />} />
        <Route path="/incident/:id" element={<IncidentReport />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </ErrorBoundary>
  );
}
