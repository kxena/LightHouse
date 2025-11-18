import { SignUp } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import titleImg from "../assets/logo.png";
import { DarkModeToggle } from "./DarkModeToggle";
import { ArrowLeft } from "lucide-react";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 dark:from-slate-800 dark:via-purple-900 dark:to-blue-900 px-4 py-8">
      {/* Dark Mode Toggle */}
      <DarkModeToggle />
      
      {/* Back to Home Button */}
      <Link
        to="/"
        className="absolute top-6 left-6 flex items-center gap-2 px-4 py-2 bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm text-gray-800 dark:text-gray-200 font-semibold rounded-xl shadow-md hover:bg-white/80 dark:hover:bg-slate-700/80 transition-all duration-200 hover:scale-105"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Home
      </Link>
      
      <div className="flex flex-col items-center gap-8">
      <div className="flex flex-col items-center gap-8">
        <img
          src={titleImg}
          alt="LightHouse Logo"
          className="w-40 h-40 object-contain dark:brightness-200 dark:contrast-125"
        />

        <SignUp
          appearance={{
            elements: {
              card: "bg-gradient-to-br from-white/90 to-gray-50/90 dark:from-slate-800/90 dark:to-slate-700/90 backdrop-blur-lg shadow-2xl border border-white/20 dark:border-slate-600/20",
              headerTitle: "text-gray-800 dark:text-white font-bold text-2xl",
              headerSubtitle: "text-gray-600 dark:text-gray-300",
              socialButtonsBlockButton: "bg-white/70 dark:bg-slate-700/70 border border-gray-200 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-white dark:hover:bg-slate-600",
              formFieldInput: "bg-white/70 dark:bg-slate-700/70 border border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white",
              formButtonPrimary: "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold",
              footerActionLink: "text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300",
              identityPreviewEditButton: "text-gray-600 dark:text-gray-400",
              formFieldLabel: "text-gray-700 dark:text-gray-300",
              otpCodeFieldInput: "border-white text-white",
              footer: "hidden",
            },
          }}
          routing="path"
          path="/sign-up"
          signInUrl="/sign-in"
          forceRedirectUrl="/dashboard"
        />
      </div>
    </div>
  );
}