import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { DarkModeContext } from './DarkModeContextDefinition';

export function DarkModeProvider({ children }: { children: ReactNode }) {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    // Always start with light mode on fresh loads
    // Only check localStorage if we're sure it's a valid value
    try {
      const saved = localStorage.getItem('darkMode');
      if (saved !== null) {
        const parsed = JSON.parse(saved);
        // Only use saved value if it's explicitly true, otherwise default to light
        return parsed === true;
      }
    } catch {
      // In case of any localStorage error, default to light mode
      localStorage.removeItem('darkMode'); // Clear corrupted data
    }
    // Default to light mode
    return false;
  });

  useEffect(() => {
    // Save to localStorage
    localStorage.setItem('darkMode', JSON.stringify(isDarkMode));
    
    // Update document class for Tailwind dark mode
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
      console.log('Added dark class to html element');
    } else {
      document.documentElement.classList.remove('dark');
      console.log('Removed dark class from html element');
    }
    
    // Debug log - check if class was actually applied
    console.log('Dark mode state:', isDarkMode);
    console.log('HTML classes:', document.documentElement.className);
    console.log('Has dark class:', document.documentElement.classList.contains('dark'));
  }, [isDarkMode]);

  // Ensure proper initialization on mount
  useEffect(() => {
    // Make sure the document class matches the state on first load
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount to ensure proper initialization

  const toggleDarkMode = () => {
    console.log('Toggle clicked - current state:', isDarkMode, 'switching to:', !isDarkMode);
    setIsDarkMode(!isDarkMode);
  };

  const resetToLightMode = () => {
    localStorage.removeItem('darkMode');
    setIsDarkMode(false);
    console.log('Reset to light mode');
  };

  // Make resetToLightMode available globally for debugging
  useEffect(() => {
    (window as Window & { resetDarkMode?: () => void }).resetDarkMode = resetToLightMode;
    return () => {
      delete (window as Window & { resetDarkMode?: () => void }).resetDarkMode;
    };
  }, []);

  return (
    <DarkModeContext.Provider value={{ isDarkMode, toggleDarkMode }}>
      {children}
    </DarkModeContext.Provider>
  );
}