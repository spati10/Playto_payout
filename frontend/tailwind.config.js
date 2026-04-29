/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f8fafc",
          100: "#f1f5f9",
          500: "#334155",
          700: "#1e293b",
          900: "#0f172a"
        }
      },
      boxShadow: {
        soft: "0 10px 30px rgba(15, 23, 42, 0.06)"
      }
    },
  },
  plugins: [],
};