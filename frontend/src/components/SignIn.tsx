import { SignIn } from "@clerk/clerk-react";
import { Link } from "react-router-dom";
import { DarkModeToggle } from "./DarkModeToggle";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 dark:from-slate-800 dark:via-purple-900 dark:to-blue-900 px-4">
      {/* Dark Mode Toggle */}
      <DarkModeToggle />
      
      <div className="flex flex-col lg:flex-row items-center justify-between gap-12 w-full max-w-5xl">
        <div className="flex flex-col items-center gap-6 lg:w-1/2">
          <img
            src="src/assets/logo.png"
            alt="LightHouse Logo"
            className="w-100 h-100 object-contain"
          />

          <div className="text-center">
            <div className="flex justify-center items-center h-3 mb-3">
              <img
                src="src/assets/title.png"
                alt="LightHouse Logo"
                className="object-contain max-h-12 dark:brightness-200 dark:contrast-125"
              />
            </div>
            <p className="text-gray-600 dark:text-gray-300 mt-2">New to LightHouse?</p>
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
                variables: {
                  fontFamily:
                    "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI",
                  colorPrimary: "#06b6d4", // Tailwind cyan-500/600
                  colorText: "#e5e7eb", // slate-200
                  colorTextSecondary: "#cbd5e1", // slate-300
                  colorBackground: "transparent", // let your panel show through
                  colorInputBackground: "transparent",
                  colorInputText: "#ffffff",
                  spacingUnit: "13px", // breathe a bit more
                },
                elements: {
                  rootBox: "w-full",
                  card: "bg-transparent shadow-none w-full",
                  headerTitle: "hidden",
                  headerSubtitle: "hidden",
                  socialButtonsBlockButton:
                    "!bg-white !text-gray-800 !rounded-full !border !border-transparent !shadow-md " +
                    "hover:!bg-gray-100 hover:!shadow-lg flex items-center justify-center",
                  socialButtonsBlockButton__google:
                    "!bg-white !text-gray-800 hover:!bg-gray-100",
                  socialButtonsBlockButtonText: "!font-medium !text-gray-800",
                  formButtonPrimary:
                    "bg-cyan-500 hover:bg-cyan-600 text-white rounded-full normal-case",
                  formFieldInput:
                    "bg-transparent border-2 border-white rounded-full text-white placeholder-gray-300 focus:border-cyan-400 focus:ring-0",
                  formFieldLabel: "text-white mb-2",
                  footerActionLink: "text-cyan-400 hover:text-cyan-300",
                  identityPreviewEditButton:
                    "text-cyan-400 hover:text-cyan-300",
                  formFieldInputShowPasswordButton:
                    "text-gray-300 hover:text-white",
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
              forceRedirectUrl="/dashboard"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
