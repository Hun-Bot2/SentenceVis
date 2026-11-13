// Check local Markdown file targets; anchors and external links are not checked.
import fs from 'node:fs/promises';
import path from 'node:path';
const root = new URL('../../', import.meta.url);
async function walk(folder) {
  const result = [];
  for (const e of await fs.readdir(folder, { withFileTypes: true })) {
    if (['.git', 'node_modules', 'dist', 'data', 'artifacts'].includes(e.name)) continue;
    const full = path.join(folder, e.name);
    if (e.isDirectory()) result.push(...await walk(full));
    else if (e.name.endsWith('.md')) result.push(full);
  }
  return result;
}
const errors = [];
let links = 0;
const { fileURLToPath } = await import('node:url');
const files = await walk(fileURLToPath(root));
for (const file of files) {
  const text = await fs.readFile(file, 'utf8');
  if (text.split('\n').filter(x => x.startsWith('```')).length % 2) errors.push(`${file}: unbalanced fences`);
  for (const [, target] of text.matchAll(/\]\(([^)]+)\)/g)) {
    if (/^(?:[a-z]+:|#)/i.test(target)) continue;
    const name = target.split('#')[0];
    if (!name) continue;
    links++;
    try { await fs.access(path.resolve(path.dirname(file), name)); }
    catch { errors.push(`${file}: missing ${target}`); }
  }
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exitCode = 1;
} else console.log(`Markdown file targets and fences passed (${files.length} files, ${links} links).`);
