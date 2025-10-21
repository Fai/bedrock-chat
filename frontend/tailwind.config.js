/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    fontFamily: {
      body: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      heading: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
    },
    extend: {
      transitionProperty: {
        width: 'width',
        height: 'height',
      },
      animation: {
        fastPulse: 'pulse 0.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      colors: {
        // ICON Framework Brand Colors
        'icon-red': {
          primary: '#a72b23',    // Main brand red
          dark: '#95251a',       // Darker variant
          light: '#ec5254',      // Lighter accent
          cta: '#ce282c',        // Call-to-action
        },
        'icon-gray': {
          dark: '#3c4d55',       // Text/borders
          medium: '#949ea7',     // Secondary text
          light: '#f5f5f5',      // Backgrounds
          neutral: '#eef0ef',    // Alternative bg
        },
        'icon-ui': {
          success: '#28a745',
          warning: '#ffc107',
          info: '#007fff',
          danger: '#dc3545',
        },
        // Dark mode variants
        'icon-dark': {
          bg: '#2e3639',         // Dark background
          surface: '#3c4d55',    // Surface color
          text: '#f5f5f5',       // Text on dark
        },
        // Legacy AWS colors (backward compatibility)
        'aws-squid-ink': {
          light: '#3c4d55',
          dark: '#2e3639',
        },
        'aws-sea-blue': {
          light: '#a72b23',
          dark: '#3c4d55',
        },
        'aws-sea-blue-hover': {
          light: '#95251a',
          dark: '#3c4d55',
        },
        'aws-aqua': '#a72b23',
        'aws-lab': '#28a745',
        'aws-mist': '#9ffcea',
        'aws-font-color': {
          light: '#3c4d55',
          dark: '#f5f5f5',
          gray: '#949ea7',
          blue: '#007fff',
        },
        'aws-font-color-white': {
          light: '#ffffff',
          dark:'#f5f5f5',
        },
        'aws-ui-color': {
          dark: '#2e3639',
        },
        'aws-paper': {
          light: '#f5f5f5',
          dark: '#2e3639',
        },
        red: '#dc3545',
        'light-red': '#fee2e2',
        yellow: '#ffc107',
        'light-yellow': '#fef9c3',
        'dark-gray': '#6b7280',
        gray: '#9ca3af',
        'light-gray': '#e5e7eb',
      },
    },
  },
  // eslint-disable-next-line no-undef
  plugins: [require('@tailwindcss/typography'), require('tailwind-scrollbar')],
};
