// AI-assisted scaffold (Codex) and local data route (Claude Code, 2026-11-16); see docs/records/ATTRIBUTION.md.
import { defineConfig, normalizePath, type Plugin } from 'vite';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

// Serves ONE private, git-ignored file to the local dev server only (never bundled into a build).
// The export excludes text of documents that are not display_ok (scripts/publish/export_prototype.py).
const localPrototypeData = (): Plugin => ({
  name: 'local-prototype-data',
  apply: 'serve',
  configureServer(server) {
    const file = fileURLToPath(new URL('./data/private/export/prototype.json', import.meta.url));
    server.middlewares.use('/__local/prototype.json', async (_req, res) => {
      try {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.setHeader('Cache-Control', 'no-store');
        res.end(await readFile(file));
      } catch {
        res.statusCode = 404;
        res.end('{"error":"run scripts/publish/export_prototype.py first"}');
      }
    });
  },
});

export default defineConfig({
  base: './',
  publicDir: false,
  plugins: [localPrototypeData()],
  server: {
    fs: {
      deny: [
        '.env', '.env.*', '*.{crt,pem,key}', '**/.git/**',
        `${normalizePath(fileURLToPath(new URL('./data', import.meta.url)))}/**`,
        '**/data/raw/**', '**/data/private/**', '**/data/processed/**', '**/data/cache/**',
        '**/private/**', '**/secrets/**', '**/*.pdf',
      ],
    },
  },
});
