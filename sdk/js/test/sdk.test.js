import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ContextOS } from '../contextos.js';
import { makeProject, cleanup } from './helpers.js';

test('decide records an A/B/C decision', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const selection = await sdk.decide('1', 'B');
    assert.equal(selection.selected, 'B');
    const decisions = await sdk.decisions();
    assert.equal(decisions.length, 1);
    assert.equal(decisions[0].selected_option, 'B');
  } finally {
    cleanup(root);
  }
});

test('decide rejects invalid options', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    await assert.rejects(() => sdk.decide('1', 'D'), /Invalid selection/);
  } finally {
    cleanup(root);
  }
});

test('snapshot then rollback restores content', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    await sdk.snapshot('original');

    const model = await sdk.loadContext();
    model.project.goal = 'Changed goal';
    await sdk.saveContext(model);

    assert.equal(await sdk.rollback(), true);
    const restored = await sdk.loadContext();
    assert.equal(restored.project.goal, 'Test the SDK');
  } finally {
    cleanup(root);
  }
});

test('rollback returns false with no snapshots', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.equal(await sdk.rollback(), false);
  } finally {
    cleanup(root);
  }
});

test('decompose adds subtasks to a task', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const subtasks = await sdk.decompose('2');
    assert.ok(subtasks.length > 0);
    assert.equal(subtasks[0].id, '2.1');
    const model = await sdk.loadContext();
    assert.equal(model.tasks[1].subtasks.length, subtasks.length);
  } finally {
    cleanup(root);
  }
});

test('decompose unknown task returns empty list', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.deepEqual(await sdk.decompose('99'), []);
  } finally {
    cleanup(root);
  }
});

test('suggest returns A/B/C approaches', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const suggestions = await sdk.suggest('1');
    assert.equal(suggestions.recommended, 'B');
    assert.ok(suggestions.suggestions.A && suggestions.suggestions.B && suggestions.suggestions.C);
  } finally {
    cleanup(root);
  }
});

test('inject returns prompt and records history', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const prompt = await sdk.inject('Do something');
    assert.ok(prompt.includes('Do something'));
    assert.ok(prompt.includes('Test the SDK'));
    const stats = await sdk.stats();
    assert.equal(stats.interactions, 1);
    assert.ok(stats.total_tokens_injected > 0);
  } finally {
    cleanup(root);
  }
});

test('inject throws on invalid aicf', async () => {
  const root = makeProject({
    aicf: {
      project: { name: '', goal: '' },
      state: { phase: '', current_task: '' },
      tasks: [],
      rules: { max_subtasks: 5 }
    }
  });
  try {
    const sdk = new ContextOS(root);
    await assert.rejects(() => sdk.inject('hi'), /Invalid context/);
  } finally {
    cleanup(root);
  }
});

test('explain does not mutate persisted state', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    await sdk.explain('2');
    const model = await sdk.loadContext();
    assert.equal(model.state.current_task, '1');
  } finally {
    cleanup(root);
  }
});

test('explain previews a different task without saving', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const explanation = await sdk.explain('2');
    assert.ok(explanation.includes('Build core'));
  } finally {
    cleanup(root);
  }
});

test('stats returns all expected keys', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    await sdk.decide('1', 'A');
    await sdk.snapshot('x');
    const stats = await sdk.stats();
    assert.equal(stats.project, 'TestProject');
    assert.equal(stats.decisions_recorded, 1);
    assert.equal(stats.snapshots_saved, 1);
    assert.equal(stats.total_tasks, 2);
    assert.ok(typeof stats.context_score === 'number');
  } finally {
    cleanup(root);
  }
});

test('filterPaths respects ignore rules', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const paths = ['core/engine.py', '.venv/scripts/x.py', 'README.md', 'dist/a.js'];
    const filtered = sdk.filterPaths(paths);
    assert.deepEqual(filtered, ['core/engine.py', 'README.md']);
  } finally {
    cleanup(root);
  }
});
