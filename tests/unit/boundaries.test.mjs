// Synthetic code snippets test architecture violations, not legal observations.
import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';
import { checkSource } from '../../scripts/checks/boundaries.mjs';
const root = path.resolve('/synthetic-project');
const inspect = (file, code) => checkSource(path.join(root, 'src', file), code, root);

test('domain rejects rendering dependencies and outward feature imports', () => {
  assert.equal(inspect('domain/entity.ts', "import {scaleLinear} from 'd3';").length, 1);
  assert.equal(inspect('domain/entity.ts', "import type { X } from '../features/reasoning/X';").length, 1);
});
test('private data cannot be reached by relative imports, re-exports or dynamic imports', () => {
  for (const code of [
    "import raw from '../../data/raw/case.json';",
    "export {default} from '../../data/private/case.json';",
    "const raw = import('../../data/processed/case.json');",
  ]) assert.equal(inspect('data/loader.ts', code).length, 1);
});
test('data and geometry reject framework imports', () => {
  for (const layer of ['data', 'vis']) assert.equal(inspect(`${layer}/module.ts`, "import {useState} from 'react';").length, 1);
});
test('geometry may use D3 and pure domain types; app may compose features', () => {
  assert.deepEqual(inspect('vis/layout.ts', "import {scaleLinear} from 'd3'; import type {X} from '../domain/X';"), []);
  assert.deepEqual(inspect('app/App.tsx', "import {View} from '../features/evidence/View';"), []);
});
test('computed dynamic imports require a reviewed loader boundary', () => {
  assert.equal(inspect('data/loader.ts', 'const data = import(file);').length, 1);
});
