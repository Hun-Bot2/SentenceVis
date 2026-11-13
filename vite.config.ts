// AI-assisted scaffold; see docs/records/ATTRIBUTION.md. No Atlas source was copied.
import { defineConfig } from 'vite';

export default defineConfig({
  base: './',
  // Explicit public-data export is not implemented or reviewed yet.
  publicDir: false,
  server: {
    fs: {
      deny: [
        '.env', '.env.*', '*.{crt,pem,key}', '**/.git/**',
        '**/data/raw/**', '**/data/private/**', '**/data/processed/**', '**/data/cache/**',
        '**/private/**', '**/secrets/**', '**/*.pdf',
      ],
    },
  },
});
