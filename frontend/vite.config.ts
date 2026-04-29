import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,  // exposes on 0.0.0.0 so LAN devices can connect
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // Points to your Node.js backend
        changeOrigin: true,
      }
    }
  }
})