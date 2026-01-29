import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local dev:
// - Web: http://localhost:5173
// - API: http://localhost:20000
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://localhost:20000",
      "/health": "http://localhost:20000",
    },
  },
});
