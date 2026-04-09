/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        ink: {
          950: "#07080d",
          900: "#0c0e14",
          850: "#12151e",
          800: "#1a1e2a",
          700: "#252a38",
        },
        violet: {
          glow: "#a78bfa",
          deep: "#5b21b6",
        },
        cyan: {
          glow: "#22d3ee",
        },
      },
      boxShadow: {
        panel: "0 0 0 1px rgba(139, 92, 246, 0.12), 0 24px 48px -12px rgba(0, 0, 0, 0.55)",
        glow: "0 0 40px -8px rgba(167, 139, 250, 0.35)",
      },
      animation: {
        pulseSlow: "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
    },
  },
  plugins: [],
};
