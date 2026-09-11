import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  envDir: "..", // .env único na raiz do repo, compartilhado com o backend
});
