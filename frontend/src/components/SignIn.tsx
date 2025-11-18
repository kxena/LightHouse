import { SignIn } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function SignInPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 px-4 py-12">
      {/* Back to Home Button */}
      <Link
        to="/"
        className="absolute top-6 left-6 flex items-center gap-2 px-4 py-2 bg-white/60 backdrop-blur-sm text-gray-800 font-semibold rounded-xl shadow-md hover:bg-white/80 transition-all duration-200 hover:scale-105"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Home
      </Link>

      {/* Centered Content */}
      <div className="flex flex-col items-center gap-8 w-full max-w-md">
        {/* Logo and Title */}
        <div className="flex flex-col items-center gap-4 animate-fadeIn">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full blur-2xl opacity-30"></div>
            <img
              src="src/assets/logo.png"
              alt="LightHouse Logo"
              className="relative w-28 h-28 object-contain"
            />
          </div>
          <img
            src="src/assets/title.png"
            alt="LightHouse"
            className="object-contain h-12"
          />
          <p className="text-gray-700 text-center max-w-sm">
            Monitor and respond to disasters in real-time
          </p>
        </div>

        {/* Sign In Card */}
        <div className="bg-white/70 backdrop-blur-md rounded-3xl shadow-2xl w-full p-10 ring-1 ring-black/5 animate-fadeIn">
          <h2 className="text-3xl font-bold text-center mb-8 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 bg-clip-text text-transparent">
            Welcome Back
          </h2>
          
          <SignIn
            appearance={{
              variables: {
                colorPrimary: "#9333ea",
                colorBackground: "#ffffff",
                colorInputBackground: "#fafafa",
                colorInputText: "#1f2937",
                borderRadius: "1rem",
                fontFamily: "inherit",
              },
              elements: {
                rootBox: "w-full",
                card: "bg-transparent shadow-none p-0",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                socialButtonsBlockButton:
                  "bg-white border-2 border-gray-300 hover:border-purple-400 hover:bg-purple-50 rounded-xl font-semibold text-gray-800 shadow-sm transition-all duration-200 py-3",
                socialButtonsBlockButtonText: "font-semibold text-base",
                socialButtonsIconButton: "border-gray-300 hover:border-purple-400",
                formButtonPrimary:
                  "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 text-base font-bold py-3.5 transform hover:scale-[1.02]",
                formFieldInput:
                  "border-2 border-gray-300 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 text-gray-900 bg-white px-4 py-3 transition-all duration-200 placeholder:text-transparent",
                formFieldLabel: "hidden",
                formFieldLabelRow: "hidden",
                formFieldInputShowPasswordButton: "text-gray-500 hover:text-purple-600 transition-colors",
                footerActionLink: "text-purple-600 hover:text-purple-700 font-semibold hover:underline",
                dividerLine: "bg-gray-300",
                dividerText: "text-gray-600 text-sm font-medium",
                footer: "hidden",
                identityPreviewEditButton: "text-purple-600 hover:text-purple-700 font-medium",
                formResendCodeLink: "text-purple-600 hover:text-purple-700 font-medium",
                otpCodeFieldInput: "border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200",
                formFieldAction: "text-purple-600 hover:text-purple-700 font-medium",
              },
            }}
            routing="path"
            path="/sign-in"
            signUpUrl="/sign-up"
            forceRedirectUrl="/dashboard"
          />
        </div>

        {/* Sign Up Link */}
        <div className="text-center animate-fadeIn">
          <p className="text-gray-700 mb-4 font-medium">Don't have an account?</p>
          <Link
            to="/sign-up"
            className="inline-block px-10 py-3.5 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-white font-bold rounded-xl shadow-lg hover:shadow-2xl transition-all duration-200 transform hover:scale-105"
          >
            Create Account
          </Link>
        </div>

        {/* Footer Text */}
        <p className="text-gray-600 text-sm text-center animate-fadeIn">
          © 2025 LightHouse. Disaster Response Intelligence Platform.
        </p>
      </div>
    </div>
  );
}
