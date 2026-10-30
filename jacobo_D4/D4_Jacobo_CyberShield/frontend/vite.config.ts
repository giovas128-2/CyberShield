import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base "./" permite cargar el build desde file:// (necesario si lo empaquetas con Electron/Tauri)
export default defineConfig({ plugins: [react()], base: "./" });
