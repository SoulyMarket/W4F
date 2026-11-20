/// <reference types="vitest/config" />
import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  optimizeDeps: {
    // maplibre-gl spawns its tile-processing Worker from a URL resolved
    // relative to its own module location. Vite's dev-server dependency
    // pre-bundling moves the library into `node_modules/.vite/deps/`,
    // which breaks that self-reference — confirmed live: the map's style
    // never finished loading (`Worker failed to load`), so markers never
    // rendered even though the GeoJSON endpoint returned good data.
    // Excluding it from pre-bundling serves it from its own real path
    // instead, where the worker URL resolves correctly.
    exclude: ['maplibre-gl'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
  },
})
