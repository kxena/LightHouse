import React from "react";
import { AlertTriangle, Loader, RefreshCw } from "lucide-react";

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading...",
}) => (
  <div className="flex items-center justify-center h-full">
    <div className="flex items-center gap-3 text-gray-500">
      <Loader className="w-5 h-5 animate-spin" />
      <span>{message}</span>
    </div>
  </div>
);

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ message, onRetry }) => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-red-500" />
      <h3 className="text-lg font-semibold text-gray-800 mb-2">
        Something went wrong
      </h3>
      <p className="text-gray-600 mb-4 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-2 mx-auto px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  </div>
);

interface EmptyStateProps {
  title: string;
  message: string;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  message,
  icon,
}) => (
  <div className="flex items-center justify-center h-full">
    <div className="text-center">
      {icon && <div className="mb-3">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-800 mb-2">{title}</h3>
      <p className="text-gray-600 max-w-md">{message}</p>
    </div>
  </div>
);

interface ConnectionStatusProps {
  isOnline: boolean;
  lastUpdated?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isOnline,
  lastUpdated,
}) => (
  <div
    className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm ${
      isOnline ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
    }`}
  >
    <div
      className={`w-2 h-2 rounded-full ${
        isOnline ? "bg-green-500" : "bg-red-500"
      }`}
    ></div>
    <span>{isOnline ? "Connected" : "Disconnected"}</span>
    {lastUpdated && isOnline && (
      <span className="text-xs opacity-75">
        • Updated {new Date(lastUpdated).toLocaleTimeString()}
      </span>
    )}
  </div>
);
