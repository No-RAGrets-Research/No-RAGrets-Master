/**
 * Conditional logger - only logs when DEBUG is enabled
 * Set window.DEBUG = true in console to enable debug logging
 */

const isDebugEnabled = () => {
  return typeof window !== 'undefined' && (window as any).DEBUG === true;
};

export const logger = {
  log: (...args: any[]) => {
    if (isDebugEnabled()) {
      console.log(...args);
    }
  },
  warn: (...args: any[]) => {
    if (isDebugEnabled()) {
      console.warn(...args);
    }
  },
  error: (...args: any[]) => {
    // Always log errors
    console.error(...args);
  },
  info: (...args: any[]) => {
    if (isDebugEnabled()) {
      console.info(...args);
    }
  },
};
