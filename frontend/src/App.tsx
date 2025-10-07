import { Routes, Route, Navigate } from "react-router-dom";
import { SignedIn, SignedOut, UserButton } from "@clerk/clerk-react";
import SignInPage from "./components/SignIn";
import SignUpPage from "./components/SignUp";
import IncidentReport from "./components/IncidentReport";
import Dashboard from "./components/Dashboard";

export default function App() {
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
              <div className="flex flex-col items-center gap-4">
                <h1 className="text-3xl font-bold text-gray-800">
                  Welcome to LightHouse 🎉
                </h1>
                <UserButton afterSignOutUrl="/sign-in" />
              </div>
            </SignedIn>
          </div>
        }
      />

      <Route path="/sign-in/*" element={<SignInPage />} />
      <Route path="/sign-up/*" element={<SignUpPage />} />
      <Route
        path="/incident/:id"
        element={
          <>
            <SignedIn>
              <IncidentReport />
            </SignedIn>
            <SignedOut>
              <Navigate to="/sign-in" replace />
            </SignedOut>
          </>
        }
      />
      <Route
        path="/dashboard"
        element={
          <>
            <SignedIn>
              <Dashboard />
            </SignedIn>
            <SignedOut>
              <Navigate to="/sign-in" replace />
            </SignedOut>
          </>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
