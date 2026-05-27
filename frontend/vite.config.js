import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/generate": "http://127.0.0.1:8000",
      "/download-docx": "http://127.0.0.1:8000",
      "/download": "http://127.0.0.1:8000",
      "/status": "http://127.0.0.1:8000",
      "/pdf-status": "http://127.0.0.1:8000",
      "/docx-status": "http://127.0.0.1:8000",
      "/download-pdf": "http://127.0.0.1:8000"
    }
  }
});
