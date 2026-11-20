import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        graphite: "#1C1D20",
        cloud: "#F2F4F1",
        sunshine: "#FFC928",
        muted: "#989BA3",
        panel: "#25262A",
        line: "#3A3B40",
      },
    },
  },
  plugins: [typography],
};
export default config;
