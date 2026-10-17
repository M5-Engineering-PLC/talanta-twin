import { defineConfig } from 'vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

export default defineConfig(({ command }) => ({
  base: './',
  build: { target: 'es2022', chunkSizeWarningLimit: 2000 },
  ...(command === 'serve' ? {
    server: { fs: { allow: [repoRoot] } },
    define: { __TALANTA_REPO_ROOT__: JSON.stringify(repoRoot) },
  } : {}),
}));
