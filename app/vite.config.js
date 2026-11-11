import { defineConfig } from 'vite';
import path from 'node:path';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

// Local H1 study assets are never copied from public/ into the production build.
function localCharacterReviews() {
  const routes = new Map([
    ['/__talanta_people_review/', { dir: 'app/.local-people-review', files: ['Female_Adult_01.glb', 'Male_Adult_01.glb'] }],
    ['/__talanta_match_review/', { dir: 'app/.local-people-review/match', files: ['kenya-white.glb', 'spain-red.glb', 'referee-black.glb', 'LICENSE.md'] }],
  ]);
  return { name: 'local-character-reviews', configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const url = new URL(req.url, 'http://localhost');
      const route = [...routes].find(([prefix]) => url.pathname.startsWith(prefix));
      if (!route) return next();
      const [prefix, { dir, files }] = route;
      const name = url.pathname.slice(prefix.length);
      if (!files.includes(name)) { res.writeHead(404); res.end(); return; }
      const file = path.join(repoRoot, dir, name);
      try {
        const info = await stat(file);
        if (!info.isFile()) throw new Error('not a file');
        res.writeHead(200, { 'Content-Type': name.endsWith('.glb') ? 'model/gltf-binary' : 'text/plain; charset=utf-8', 'Content-Length': info.size, 'Cache-Control': 'no-store' });
        createReadStream(file).on('error', () => res.destroy()).pipe(res);
      } catch { res.writeHead(404); res.end('Local prototype asset unavailable'); }
    });
  } };
}

export default defineConfig(({ command }) => ({
  plugins: command === 'serve' ? [localCharacterReviews()] : [],
  base: './',
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      input: {
        main: path.join(repoRoot, 'app/index.html'),
        perimeter: path.join(repoRoot, 'app/perimeter.html'),
        fullSite: path.join(repoRoot, 'app/full-site.html'),
      },
    },
  },
  ...(command === 'serve' ? {
    server: { fs: { allow: [repoRoot] } },
    define: { __TALANTA_REPO_ROOT__: JSON.stringify(repoRoot) },
  } : {}),
}));
