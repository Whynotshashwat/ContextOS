import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { isIgnoredPath, loadIgnoreRules, DEFAULT_IGNORE_RULES } from '../contextos.js';

const RULES = ['.venv/', '.env', 'config.json', 'dist/', 'node_modules/', '*.pyc', '*.log'];

function projectWith(fileContent) {
  const root = mkdtempSync(path.join(tmpdir(), 'ctx-ignore-'));
  writeFileSync(path.join(root, '.contextosignore'), fileContent);
  return root;
}

test('default rules loaded when no ignore file', () => {
  const root = mkdtempSync(path.join(tmpdir(), 'ctx-ignore-'));
  try {
    assert.deepEqual(loadIgnoreRules(root), DEFAULT_IGNORE_RULES);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('custom rules loaded, comments skipped', () => {
  const root = projectWith('# comment\n.venv/\n__pycache__/\n');
  try {
    const rules = loadIgnoreRules(root);
    assert.ok(!rules.some((r) => r.startsWith('#')));
    assert.ok(rules.includes('.venv/'));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('ignores matching paths', () => {
  assert.equal(isIgnoredPath('.venv/scripts/python.exe', RULES), true);
  assert.equal(isIgnoredPath('dist/x.txt', RULES), true);
  assert.equal(isIgnoredPath('node_modules/pkg/index.js', RULES), true);
  assert.equal(isIgnoredPath('core/__pycache__/a.pyc', RULES), true);
  assert.equal(isIgnoredPath('src/.env', RULES), true);
  assert.equal(isIgnoredPath('logs/2026-05-24.log', RULES), true);
});

test('does not substring-match false positives', () => {
  assert.equal(isIgnoredPath('myconfig.json', RULES), false);
  assert.equal(isIgnoredPath('my-dist-notes/notes.txt', RULES), false);
  assert.equal(isIgnoredPath('.env.local/scripts/x.py', RULES), false);
  assert.equal(isIgnoredPath('notnode_modules/x.js', RULES), false);
});

test('does not ignore normal source files', () => {
  assert.equal(isIgnoredPath('core/engine.py', RULES), false);
  assert.equal(isIgnoredPath('README.md', RULES), false);
});

test('leading-space comment is not treated as a rule', () => {
  const root = projectWith(' # header comment\n.venv/\n');
  try {
    const rules = loadIgnoreRules(root);
    assert.ok(!rules.some((r) => r.startsWith('#')));
    assert.ok(rules.includes('.venv/'));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
