import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true, // Listen on all addresses for Docker
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    // Security: Generate source maps only for debugging
    sourcemap: false,
    // Security: Minify for production
    minify: 'esbuild', // 'esbuild' is the default, so you can also just delete the line
    // minify: 'terser',
    // terserOptions: {
    //   compress: {
    //     // Remove console.log in production
    //     drop_console: true,
    //     drop_debugger: true,
    //   },
    // },
  },
})
