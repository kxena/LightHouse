import { Routes, Route, Navigate } from "react-router-dom";
import SignInPage from "./components/SignIn";
import SignUpPage from "./components/SignUp";
import IncidentReport from "./components/IncidentReport";
import Dashboard from "./components/Dashboard";
import ErrorBoundary from "./components/ErrorBoundary";
import Profile from "./components/Profile";
import LandingPage from "./components/LandingPage";

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<LandingPage />} />
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
