import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import eslint from "vite-plugin-eslint";
import viteYaml from "@modyfi/vite-plugin-yaml";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig(() => {
  return {
    base: "./",
    server: {
      port: 8080,
    },
    plugins: [react(), eslint(), viteYaml()],
    resolve: {
      alias: {
        "~": path.resolve(__dirname, "src"),
      },
    },
    build: {
      outDir: "../deploy/build",
    },
  };
});
