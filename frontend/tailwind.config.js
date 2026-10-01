/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#0a0e1a',
        panel: '#111827',
        accent: '#06b6d4',
      }
    },
  },
  plugins: [],
}
