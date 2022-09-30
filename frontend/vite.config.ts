import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
// import basicSsl from "@vitejs/plugin-basic-ssl";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    // https: true,
    host: true,
  },
  watch: {
    usePolling: true,
  },
});
