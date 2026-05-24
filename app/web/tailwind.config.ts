import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101623",
        muted: "#667085",
        line: "#d9e1ec",
        panel: "#f8fafc",
        rail: "#0b1218",
        railLine: "#243244",
        brand: {
          DEFAULT: "#4f7cff",
          cyan: "#30c7d2",
          green: "#16b364",
          red: "#d92d20",
          orange: "#f79009",
          purple: "#7a35ff",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        card: "0 18px 45px rgba(15,23,42,.08)",
        hero: "0 24px 65px rgba(2,6,23,.22)",
      },
    },
  },
  plugins: [],
};

export default config;
