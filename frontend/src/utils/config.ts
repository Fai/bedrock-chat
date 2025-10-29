// Configuration utility that handles both build-time and runtime configuration
declare global {
  interface Window {
    APP_CONFIG?: Record<string, string>;
  }
}

export const getConfig = (key: string): string => {
  // First try build-time environment variables
  const buildTimeValue = import.meta.env[key];
  if (buildTimeValue) {
    return buildTimeValue;
  }

  // Fallback to runtime configuration from config.js
  const runtimeValue = window.APP_CONFIG?.[key];
  if (runtimeValue) {
    return runtimeValue;
  }

  // Return empty string if not found
  return '';
};

export const API_ENDPOINT = getConfig('VITE_APP_API_ENDPOINT');
export const WS_ENDPOINT = getConfig('VITE_APP_WS_ENDPOINT');
export const USER_POOL_ID = getConfig('VITE_APP_USER_POOL_ID');
export const USER_POOL_CLIENT_ID = getConfig('VITE_APP_USER_POOL_CLIENT_ID');
export const REGION = getConfig('VITE_APP_REGION');
export const USE_STREAMING = getConfig('VITE_APP_USE_STREAMING');
export const REDIRECT_SIGNIN_URL = getConfig('VITE_APP_REDIRECT_SIGNIN_URL');
export const REDIRECT_SIGNOUT_URL = getConfig('VITE_APP_REDIRECT_SIGNOUT_URL');
export const COGNITO_DOMAIN = getConfig('VITE_APP_COGNITO_DOMAIN');
export const SOCIAL_PROVIDERS = getConfig('VITE_APP_SOCIAL_PROVIDERS');
export const CUSTOM_PROVIDER_ENABLED = getConfig('VITE_APP_CUSTOM_PROVIDER_ENABLED');
export const CUSTOM_PROVIDER_NAME = getConfig('VITE_APP_CUSTOM_PROVIDER_NAME');
