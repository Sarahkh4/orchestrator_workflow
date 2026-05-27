/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0f0f1a",
          900: "#131421",
          800: "#1b1d2e",
          700: "#25283a"
        },
        aurora: {
          blue: "#38bdf8",
          violet: "#8b5cf6",
          indigo: "#6366f1"
        }
      },
      boxShadow: {
        glow: "0 0 42px rgba(99, 102, 241, 0.26)"
      },
      animation: {
        "fade-up": "fadeUp 520ms ease-out both",
        "soft-pulse": "softPulse 1.8s ease-in-out infinite",
        "progress": "progress 1.35s ease-in-out infinite"
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        softPulse: {
          "0%, 100%": { opacity: "0.6", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.025)" }
        },
        progress: {
          "0%": { transform: "translateX(-75%)" },
          "100%": { transform: "translateX(275%)" }
        }
      }
    }
  },
  plugins: []
};
