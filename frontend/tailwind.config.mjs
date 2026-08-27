/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#07111f",
          900: "#0d1726",
          800: "#152033",
          700: "#243248",
          600: "#34445d",
          200: "#c3d0e3",
          100: "#e7eef9"
        },
        accent: {
          50: "#eefbf5",
          100: "#d9f6e8",
          200: "#aeeacb",
          300: "#7ddfb0",
          400: "#3cc98c",
          500: "#18a56e",
          600: "#12865a"
        }
      },
      boxShadow: {
        panel: "0 20px 60px rgba(4, 11, 22, 0.35)"
      }
    }
  },
  plugins: []
};

export default config;
