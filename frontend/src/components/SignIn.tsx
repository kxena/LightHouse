import { SignIn } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 px-4">
      <div className="flex flex-col lg:flex-row items-center justify-between gap-12 w-full max-w-5xl">
        <div className="flex flex-col items-center gap-6 lg:w-1/2">
          <img 
            src="src/assets/logo.png" 
            alt="LightHouse Logo" 
            className="w-100 h-100 object-contain"
          />

          <div className="text-center">
            <h1 className="text-5xl font-bold">
              <span className="text-gray-800">Light</span>
              <span className="text-pink-600">House</span>
            </h1>
            <p className="text-gray-600 mt-2">New to LightHouse?</p>
            <Link
              to="/sign-up"
              className="inline-block mt-4 px-8 py-2 bg-cyan-600 text-white rounded-full shadow-md hover:bg-cyan-700 transition"
            >
              Sign Up
            </Link>
          </div>
        </div>

        <div className="bg-[#2B3F5F] text-white rounded-3xl shadow-2xl w-full lg:w-1/2 max-w-md overflow-hidden">
          <div className="pt-10 px-10">
            <h2 className="text-4xl font-semibold text-center mb-8">Sign In</h2>
          </div>
          
          <div className="px-6 pb-8">
            <SignIn
              appearance={{
                elements: {
                  rootBox: "w-full",
                  card: "bg-transparent shadow-none p-0 w-full",
                  headerTitle: "hidden",
                  headerSubtitle: "hidden",
                  socialButtonsBlockButton: 
                    "bg-white text-gray-700 py-3 rounded-full hover:bg-gray-100 border-none",
                  socialButtonsBlockButtonText: "font-medium",
                  formButtonPrimary:
                    "bg-cyan-500 hover:bg-cyan-600 text-white py-3 rounded-full normal-case",
                  formFieldInput:
                    "bg-transparent border-2 border-white rounded-full py-3 px-4 text-white placeholder-gray-300 focus:border-cyan-400 focus:ring-0",
                  formFieldLabel: "text-white mb-2",
                  footerActionLink: "text-cyan-400 hover:text-cyan-300",
                  identityPreviewEditButton: "text-cyan-400 hover:text-cyan-300",
                  formFieldInputShowPasswordButton: "text-gray-300 hover:text-white",
                  dividerLine: "bg-gray-400",
                  dividerText: "text-gray-300",
                  footerActionText: "text-gray-300",
                  otpCodeFieldInput: "border-white text-white",
                  footer: "hidden",
                },
              }}
              routing="path"
              path="/sign-in"
              signUpUrl="/sign-up"
              afterSignInUrl="/"
            />
          </div>
        </div>
      </div>
    </div>
  );
}