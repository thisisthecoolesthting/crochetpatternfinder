import typography from '@tailwindcss/typography';

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx,svelte,vue}"],
  theme: {
    extend: {
      colors: {
        cream: {
          50: "#FBF8F3",
          100: "#FAF5ED",
          200: "#EBE0CC",
        },
        terracotta: {
          400: "#8B5A3C",
          500: "#8B5A3C",
          600: "#8B5A3C",
        },
        primary: { DEFAULT: "#8B5A3C" },
        accent: { DEFAULT: "#E8A87C" },
        sage: { 400: "#8FA888", 500: "#6F8B6A", 600: "#566F52" },
        rose: { deep: "#7A2E3F" },
        ink: {
          900: "#2D1B12",
          700: "#4A4340",
          500: "#6E6863",
        },
      },
      maxWidth: {
        prose: "68ch",
      },
      typography: {
        DEFAULT: { css: { maxWidth: "68ch" } },
        ink: { css: { color: "#4A4340" } },
      },
      fontFamily: {
        display: ['Fraunces', "Georgia", "serif"],
        sans: ['Inter', "system-ui", "sans-serif"],
        body: ['Inter', "sans-serif"],
        mono: ['JetBrains Mono', "monospace"],
      },
    },
  },
  plugins: [typography],
};
