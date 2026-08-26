import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const root = import.meta.dirname;

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    exclude: ["**/node_modules/**", "**/e2e/**", "**/.next/**"],
  },
  resolve: {
    alias: {
      "@": root,
      "@shiksha-sathi/shared-types": `${root}/../../packages/shared-types/src/index.ts`,
      // Next.js server-only stub — not needed in jsdom tests
      "server-only": `${root}/__mocks__/server-only.ts`,
    },
  },
});
