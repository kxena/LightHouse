import { SignUp } from "@clerk/clerk-react";
import { Link } from "react-router-dom";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 px-4 py-8">
      <div className="flex flex-col items-center gap-8">
        <img 
          src="src/assets/logo.png" 
          alt="LightHouse Logo" 
          className="w-20 h-20 object-contain"
        />

        <div className="bg-[#2B3F5F] text-white rounded-3xl shadow-2xl p-10 w-full max-w-lg">
          <h2 className="text-4xl font-semibold text-center mb-8">Sign Up</h2>
          
          <SignUp
            appearance={{
              elements: {
                card: "bg-transparent shadow-none p-0",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                socialButtonsBlockButton: 
                  "bg-white text-gray-700 py-3 rounded-full hover:bg-gray-100 border-none",
                socialButtonsBlockButtonText: "font-medium",
                formButtonPrimary:
                  "bg-cyan-500 hover:bg-cyan-600 text-white py-3 rounded-full normal-case",
                formFieldInput:
                  "bg-transparent border-b-2 border-gray-300 py-2 text-white placeholder-gray-300 focus:border-cyan-400 focus:ring-0 rounded-none",
                formFieldLabel: "text-gray-300 mb-2",
                footerActionLink: "text-cyan-400 hover:text-cyan-300",
                formFieldInputShowPasswordButton: "text-gray-300 hover:text-white",
                dividerLine: "bg-gray-400",
                dividerText: "text-gray-300",
                formHeaderTitle: "hidden",
                formHeaderSubtitle: "hidden",
                footerActionText: "text-gray-300",
                otpCodeFieldInput: "border-b-2 border-gray-300 text-white rounded-none",
              },
            }}
            routing="path"
            path="/sign-up"
            signInUrl="/sign-in"
            afterSignUpUrl="/"
          />
        </div>
      </div>
    </div>
  );
}