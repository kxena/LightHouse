import { Routes, Route, Navigate } from "react-router-dom";
import { SignedIn, SignedOut } from "@clerk/clerk-react";
import SignInPage from "./components/SignIn";
import SignUpPage from "./components/SignUp";
import IncidentReport from "./components/IncidentReport";
import Dashboard from "./components/Dashboard";
import Profile from "./components/Profile";

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <div>
            <SignedOut>
              <Navigate to="/sign-in" replace />
            </SignedOut>
            <SignedIn>
              <Navigate to="/dashboard" replace />
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