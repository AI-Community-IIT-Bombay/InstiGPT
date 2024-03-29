import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "rgb(22, 25, 37)",
        "background-alt": "rgb(38, 42, 58)",
        primary: "rgb(35, 57, 91)",
        secondary: "rgb(111, 123, 255)",
        accent: "rgb(254, 81, 255)",
        foreground: "rgb(203, 247, 237)",
      },
      backgroundImage: {
        "primary-gradient":
          "linear-gradient(to left, theme('colors.accent'), theme('colors.secondary'))",
      },
    },
  },
  plugins: [
    require("tailwind-scrollbar")({ nocompatible: true }),
    require("@tailwindcss/typography"),
  ],
};
export default config;
