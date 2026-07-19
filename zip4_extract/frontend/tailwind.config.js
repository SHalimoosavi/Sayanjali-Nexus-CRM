/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#12131A",        // near-black base, not pure black
        surface: "#181A24",    // panel background
        surfaceRaised: "#20222E",
        border: "#2B2E3D",
        muted: "#8A8DA0",
        brass: "#C9A15E",      // signature accent - "nexus brass"
        brassSoft: "#E4C989",
        signal: "#5B8DEF",     // info/links
        good: "#4ADE80",
        warn: "#F5A524",
        danger: "#F45B69",
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      borderRadius: { sm: "4px", md: "8px", lg: "12px" },
    },
  },
  plugins: [],
};
