import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        // Use Docker service name for container-to-container communication
        target: process.env.VITE_API_URL || "http://api:8000",
        changeOrigin: true,
      },
    },
  },
});
