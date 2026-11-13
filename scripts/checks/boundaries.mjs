// AI-assisted infrastructure. Scope: static literal TS/TSX import boundaries.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const allowed = {
  domain: ['domain'],
  data: ['data', 'domain'],
  state: ['state', 'domain'],
  vis: ['vis', 'domain'],
  components: ['components', 'domain'],
  features: ['features', 'components', 'domain', 'data', 'state', 'vis', 'styles'],
  app: ['app', 'features', 'components', 'domain', 'data', 'state', 'vis', 'styles'],
};

export function checkSource(filename, text, root) {
  const sourceRoot = path.join(root, 'src');
  const layer = path.relative(sourceRoot, filename).split(path.sep)[0];
  const syntax = ts.createSourceFile(filename, text, ts.ScriptTarget.Latest, true);
  const errors = [];
  const check = (specifier) => {
    if (!specifier.startsWith('.')) {
      if (specifier.startsWith('/') || specifier.startsWith('@/') || specifier.includes('!')) {
        errors.push(`Unsupported import path: ${specifier}`);
      }
      const packageName = specifier.startsWith('@') ? specifier.split('/').slice(0, 2).join('/') : specifier.split('/')[0];
      const pure = ['domain', 'state'].includes(layer);
      const forbidden = pure || (['data', 'vis'].includes(layer) && ['react', 'react-dom'].includes(packageName));
      if (forbidden) errors.push(`${layer} must not depend on ${specifier}`);
      return;
    }
    const destination = path.resolve(path.dirname(filename), specifier.split('?')[0]);
    const relative = path.relative(sourceRoot, destination);
    if (relative.startsWith('..') || path.isAbsolute(relative)) {
      errors.push(`Source import escapes src: ${specifier}`);
      return;
    }
    const targetLayer = relative.split(path.sep)[0];
    if (allowed[layer] && !allowed[layer].includes(targetLayer)) {
      errors.push(`${layer} must not import ${targetLayer}: ${specifier}`);
    }
  };
  const visit = (node) => {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier && ts.isStringLiteral(node.moduleSpecifier)) check(node.moduleSpecifier.text);
    if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      const arg = node.arguments[0];
      if (arg && ts.isStringLiteral(arg)) check(arg.text);
      else errors.push('Computed dynamic imports require a reviewed loader boundary.');
    }
    ts.forEachChild(node, visit);
  };
  visit(syntax);
  return errors;
}

async function walk(folder) {
  const paths = [];
  for (const entry of await fs.readdir(folder, { withFileTypes: true })) {
    const name = path.join(folder, entry.name);
    if (entry.isDirectory()) paths.push(...await walk(name));
    else if (/\.tsx?$/.test(name)) paths.push(name);
  }
  return paths;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = fileURLToPath(new URL('../../', import.meta.url));
  const files = await walk(path.join(root, 'src'));
  const errors = [];
  for (const filename of files) {
    errors.push(...checkSource(filename, await fs.readFile(filename, 'utf8'), root).map(error => `${path.relative(root, filename)}: ${error}`));
  }
  if (errors.length) {
    console.error(errors.join('\n'));
    process.exitCode = 1;
  } else console.log(`Source boundaries passed (${files.length} files).`);
}
