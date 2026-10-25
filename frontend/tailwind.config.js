/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      boxShadow: {
        soft: '0 8px 24px rgba(15, 23, 42, 0.08)',
      },
      colors: {
        slatebg: '#f3f6fb',
        deep: '#0f172a',
        accent: '#0ea5a4',
      },
    },
  },
  plugins: [],
};
