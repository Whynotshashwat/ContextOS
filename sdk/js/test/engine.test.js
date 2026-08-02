import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { ContextOS } from '../contextos.js';
import { makeProject, cleanup } from './helpers.js';

test('loads context and reports status', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const status = await sdk.status();
    assert.equal(status.project, 'TestProject');
    assert.equal(status.current_task, 'Setup project');
    assert.equal(status.current_subtask, 'Create structure');
    assert.equal(status.progress, '0/2 tasks done');
  } finally {
    cleanup(root);
  }
});

test('returns next task and subtask', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const nextTask = await sdk.nextTask();
    assert.equal(nextTask.id, '2');
    const nextSubtask = await sdk.nextSubtask();
    assert.equal(nextSubtask.id, '1.1');
  } finally {
    cleanup(root);
  }
});

test('marks task done and sets completed_at', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.equal(await sdk.done('1.1'), true);
    const model = await sdk.loadContext();
    assert.equal(model.tasks[0].subtasks[0].status, 'done');
    assert.ok(model.tasks[0].subtasks[0].completed_at);
  } finally {
    cleanup(root);
  }
});

test('done with unknown id returns false', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.equal(await sdk.done('99'), false);
  } finally {
    cleanup(root);
  }
});

test('setCurrentTask validates id', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.equal(await sdk.setCurrentTask('999'), false);
    assert.equal(await sdk.setCurrentTask('2'), true);
    const model = await sdk.loadContext();
    assert.equal(model.state.current_task, '2');
  } finally {
    cleanup(root);
  }
});

test('setCurrentSubtask validates id', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    assert.equal(await sdk.setCurrentSubtask('999'), false);
    assert.equal(await sdk.setCurrentSubtask('1.2'), true);
    const model = await sdk.loadContext();
    assert.equal(model.state.current_subtask, '1.2');
  } finally {
    cleanup(root);
  }
});

test('throws when aicf.json is missing', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const { rm } = await import('node:fs/promises');
    await rm(path.join(root, '.contextos', 'aicf.json'));
    await assert.rejects(() => sdk.loadContext(), /AICF file not found/);
  } finally {
    cleanup(root);
  }
});

test('score returns 0-100', async () => {
  const root = makeProject();
  try {
    const sdk = new ContextOS(root);
    const score = await sdk.score();
    assert.ok(Number.isInteger(score));
    assert.ok(score >= 0 && score <= 100);
  } finally {
    cleanup(root);
  }
});
