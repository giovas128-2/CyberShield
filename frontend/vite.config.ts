import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" permite cargar el build desde file:// (necesario si lo empaquetas con Electron/Tauri)
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    proxy: {
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/dashboard": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/events": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/incidents": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/incident-assignments": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/agents": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/servers": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/notifications": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/response-actions": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/devices": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/device-trust": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/sessions": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/protections": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/lab": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/auth": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      "/intelligence": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
