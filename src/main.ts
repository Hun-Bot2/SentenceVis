// AI-assisted (Claude Code, 2026-11-16). Vanilla TS entry (D-011 decision).
import { start } from './app/main';

const root = document.getElementById('app');
if (!root) throw new Error('Application root is missing.');
void start(root);
