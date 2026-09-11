import type { Config } from "tailwindcss";
import { colors, fontFamily } from "./src/design-tokens/tokens";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors,
      fontFamily,
      borderRadius: {
        sm: "3px",
        md: "4px",
        pill: "99px",
      },
      boxShadow: {
        none: "none",
      },
    },
  },
  plugins: [],
} satisfies Config;
