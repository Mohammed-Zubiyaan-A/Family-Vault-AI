/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Sampled directly from the logo.
        night: "#02091B", // logo background
        surface: "#061230", // cards / panels
        raised: "#0A1A45", // hovered / elevated surfaces
        line: "#17295E", // borders
        ink: "#EBF5FB", // primary text (logo wordmark white)
        inkFaint: "#8FA6D4", // secondary text
        brand: { DEFAULT: "#1669FB", light: "#4C8DFF", dark: "#0F4FCC" },
        aqua: "#22C8FC", // vault-door cyan
        mint: "#0CEFB0", // green document card
        violet: { DEFAULT: "#815AFD", light: "#A995FF" }, // purple document card
        // Semantic colors deliberately outside the logo's hue range so they
        // read as "state", not "brand":
        cloudflag: "#F5A524", // cloud-inference mode (amber) -- only used for cloud
        danger: "#FF6B7A", // errors + destructive actions
      },
      fontFamily: {
        display: ["Outfit", "system-ui", "sans-serif"],
        sans: ["'IBM Plex Sans'", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(34,200,252,0.25), 0 8px 30px -8px rgba(22,105,251,0.6)",
      },
    },
  },
  plugins: [],
};
