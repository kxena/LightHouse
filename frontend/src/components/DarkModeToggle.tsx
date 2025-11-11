import type { ReactNode } from 'react';
import { useDarkMode } from '../hooks/useDarkMode';

interface DarkModeToggleProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  position?: 'fixed' | 'relative';
}

export function DarkModeToggle({ 
  className = '', 
  size = 'md', 
  position = 'fixed' 
}: DarkModeToggleProps) {
  const { isDarkMode, toggleDarkMode } = useDarkMode();
  
  const handleClick = () => {
    console.log('DarkModeToggle clicked - current mode:', isDarkMode ? 'dark' : 'light');
    toggleDarkMode();
  };
  
  const sizeClasses = {
    sm: 'p-2 w-4 h-4',
    md: 'p-3 w-5 h-5', 
    lg: 'p-4 w-6 h-6'
  };
  
  const positionClasses = position === 'fixed' 
    ? 'fixed top-4 right-4 z-50' 
    : 'relative';
  
  return (
    <button
      onClick={handleClick}
      className={`${positionClasses} bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-full shadow-lg hover:bg-white dark:hover:bg-gray-800 transition-all duration-200 ${className}`}
      aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDarkMode ? (
        <svg className={sizeClasses[size].split(' ').slice(1).join(' ')} fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
        </svg>
      ) : (
        <svg className={sizeClasses[size].split(' ').slice(1).join(' ')} fill="currentColor" viewBox="0 0 20 20">
          <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
        </svg>
      )}
    </button>
  );
}

interface DarkModeAwareProps {
  children: ReactNode;
  lightClass?: string;
  darkClass?: string;
  className?: string;
}

export function DarkModeAware({ 
  children, 
  lightClass = '', 
  darkClass = '', 
  className = '' 
}: DarkModeAwareProps) {
  return (
    <div className={`${lightClass} dark:${darkClass} ${className}`}>
      {children}
    </div>
  );
}