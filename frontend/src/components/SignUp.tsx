import { SignUp } from "@clerk/clerk-react";
import titleImg from "../assets/logo.png";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-purple-200 via-pink-100 to-blue-200 px-4 py-8">
      <div className="flex flex-col items-center gap-8">
        <img
          src={titleImg}
          alt="LightHouse Logo"
          className="w-40 h-40 object-contain"
        />

        <div className="bg-[#2B3F5F] text-white rounded-3xl shadow-2xl p-10 w-full max-w-lg">
          <h2 className="text-4xl font-semibold text-center mb-8">Sign Up</h2>

          <SignUp
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
                identityPreviewEditButton: "text-cyan-400 hover:text-cyan-300",
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
            path="/sign-up"
            signInUrl="/sign-in"
            forceRedirectUrl="/dashboard"
          />
        </div>
      </div>
    </div>
  );
}
