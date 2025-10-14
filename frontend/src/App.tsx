import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { SignedIn, SignedOut, useClerk, useUser } from "@clerk/clerk-react";
import SignInPage from "./components/SignIn";
import SignUpPage from "./components/SignUp";
import IncidentReport from "./components/IncidentReport";
import Dashboard from "./components/Dashboard";
import Profile from "./components/Profile";

export default function App() {
  const navigate = useNavigate();
  const { signOut } = useClerk();
  const { user } = useUser();

  const handleSignOut = async () => {
    await signOut();
    navigate("/sign-in");
  };

  const displayName = user?.firstName || user?.username || "User";

  return (
    <Routes>
      <Route
        path="/"
        element={
          <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-purple-100 to-blue-100">
            <SignedOut>
              <Navigate to="/sign-in" replace />
            </SignedOut>

            <SignedIn>
              <div className="flex flex-col items-center gap-8 p-8 bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4">
                <div className="flex flex-col items-center gap-4">
                  <div className="text-6xl">🏠</div>
                  <h1 className="text-4xl font-bold text-gray-800 text-center">
                    Welcome, {displayName}!
                  </h1>
                  <p className="text-gray-600 text-center">
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
                    className="w-full py-3 px-6 bg-gray-200 text-gray-800 font-semibold rounded-lg shadow-md hover:bg-gray-300 transition-all duration-200"
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
  );
}
