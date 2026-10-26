import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// relative base so the build works from any folder / GitHub Pages sub path
export default defineConfig({ base: './', plugins: [react()] });
