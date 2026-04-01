import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        mira: {
          ivory: "#F5F0EB",
          cream: "#FAF7F2",
          sand: "#E8E0D5",
          charcoal: "#2C2C2C",
          graphite: "#4A4A4A",
          slate: "#6B6B6B",
          gold: "#C4A265",
          "gold-light": "#D4B87A",
          "gold-muted": "#B89B5E",
          rose: "#C4918A",
          "rose-muted": "#B8847D",
          burgundy: "#7A3B4A",
          midnight: "#1A1A2E",
          "deep-plum": "#4A2040",
          emerald: "#2D5A4A",
          navy: "#1E2A3A",
        },
      },
      fontFamily: {
        display: ['"Playfair Display"', "Georgia", "serif"],
        body: ['"Inter"', '"Helvetica Neue"', "Arial", "sans-serif"],
        mono: ['"JetBrains Mono"', "monospace"],
      },
      fontSize: {
        "display-xl": ["3.5rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["2.5rem", { lineHeight: "1.15", letterSpacing: "-0.015em" }],
        "display-md": ["2rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "heading": ["1.5rem", { lineHeight: "1.3", letterSpacing: "-0.005em" }],
        "subheading": ["1.125rem", { lineHeight: "1.4" }],
        "body-lg": ["1.0625rem", { lineHeight: "1.6" }],
        "body": ["0.9375rem", { lineHeight: "1.6" }],
        "caption": ["0.8125rem", { lineHeight: "1.5", letterSpacing: "0.02em" }],
        "overline": ["0.6875rem", { lineHeight: "1.4", letterSpacing: "0.1em" }],
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
        "30": "7.5rem",
      },
      borderRadius: {
        "xl": "1rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        "soft": "0 2px 20px rgba(0,0,0,0.04)",
        "elevated": "0 8px 40px rgba(0,0,0,0.08)",
        "luxury": "0 12px 60px rgba(0,0,0,0.12)",
      },
      animation: {
        "fade-in": "fadeIn 0.6s ease-out",
        "slide-up": "slideUp 0.5s ease-out",
        "shimmer": "shimmer 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
