import path from 'node:path';
import { existsSync, readFileSync } from 'node:fs';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';

/**
 * ContextOS JavaScript SDK — mirrors the Python SDK surface.
 *
 * Single-file ESM module, no build step, no required dependencies.
 * All filesystem methods are async and operate on `.contextos/` in
 * the project root.
 *
 * Token counting uses `gpt-tokenizer` when installed and falls back to
 * the common `chars / 4` heuristic. Override with `setTokenEncoder`.
 */

export const DEFAULT_IGNORE_RULES = [
  '.venv/',
  '__pycache__/',
  '*.pyc',
  '*.log',
  'node_modules/',
  '.git/',
  'dist/',
  'build/',
  '*.egg-info/'
];

export const PRIORITY_LIMIT = 800;

export const CONTEXTOS_DIR_NAME = '.contextos';

// --- Tokenizer (optional) ---

let _tok = null;
let _tokLoading = null;

function getTokenizer() {
  if (_tokLoading === null) {
    _tokLoading = import('gpt-tokenizer')
      .then((m) => (m && typeof m.encode === 'function' ? m : null))
      .catch(() => null)
      .then((m) => {
        _tok = m;
        return m;
      });
  }
  return _tokLoading;
}

/**
 * Override the default token counter.
 * @param {Function|null} encodeFn `(text) => Array<number>`
 * @param {Function|null} decodeFn `(tokens) => string`
 */
export async function setTokenEncoder(encodeFn, decodeFn) {
  _tok = encodeFn ? { encode: encodeFn, decode: decodeFn || null } : null;
  _tokLoading = Promise.resolve(_tok);
}

export async function countTokens(text) {
  const tok = await getTokenizer();
  if (tok && typeof tok.encode === 'function') {
    return tok.encode(String(text)).length;
  }
  return Math.ceil(String(text).length / 4);
}

async function trimToLimit(text, limit) {
  const tok = await getTokenizer();
  if (tok && typeof tok.encode === 'function' && typeof tok.decode === 'function') {
    const tokens = tok.encode(text);
    if (tokens.length <= limit) return text;
    return tok.decode(tokens.slice(0, limit));
  }
  const maxChars = limit * 4;
  return text.length <= maxChars ? text : text.slice(0, maxChars);
}

// --- Path helpers ---

export function findProjectRoot(start) {
  let current = path.resolve(start || process.cwd());
  for (;;) {
    if (existsSync(path.join(current, CONTEXTOS_DIR_NAME))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

function contextosDirOf(projectRoot) {
  return path.join(projectRoot, CONTEXTOS_DIR_NAME);
}

function aicfPathOf(projectRoot) {
  return path.join(contextosDirOf(projectRoot), 'aicf.json');
}

// --- JSON helpers ---

async function readJson(file) {
  return JSON.parse(await readFile(file, 'utf-8'));
}

async function writeJson(file, data) {
  await mkdir(path.dirname(file), { recursive: true });
  await writeFile(file, JSON.stringify(data, null, 2), 'utf-8');
}

// --- Timestamp helpers ---

function nowIso() {
  return new Date().toISOString();
}

function snapshotStamp() {
  const d = new Date();
  const pad = (n, l = 2) => String(n).padStart(l, '0');
  return (
    `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_` +
    `${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}_` +
    `${pad(d.getMilliseconds(), 6)}`
  );
}

// --- Ignore rules ---

export function loadIgnoreRules(projectRoot) {
  const ignoreFile = path.join(projectRoot, '.contextosignore');
  if (!existsSync(ignoreFile)) {
    return DEFAULT_IGNORE_RULES.slice();
  }
  return readFileSync(ignoreFile, 'utf-8')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));
}

export function isIgnoredPath(pathStr, rules) {
  const normalized = pathStr.replace(/\\/g, '/').replace(/\/+$/, '');
  const segments = normalized.split('/').filter(Boolean);

  for (const rawRule of rules) {
    const rule = rawRule.trim().replace(/\/+$/, '');
    if (!rule || rule.startsWith('#')) continue;

    // Wildcard rule (e.g. *.pyc)
    if (rule.startsWith('*')) {
      const suffix = rule.slice(1);
      if (normalized.endsWith(suffix)) return true;
      continue;
    }

    const ruleSegments = rule.split('/').filter(Boolean);

    // Multi-segment rule (e.g. docs/build/) — path prefix match
    if (ruleSegments.length > 1) {
      if (ruleSegments.every((seg, i) => segments[i] === seg)) return true;
      continue;
    }

    // Single segment rule — exact path segment match
    if (segments.includes(ruleSegments[0])) return true;
  }

  return false;
}

// --- Validation ---

export function validateAicf(model) {
  const errors = [];
  if (!model.project || !String(model.project.name || '').trim()) {
    errors.push('Project name is empty');
  }
  if (!model.project || !String(model.project.goal || '').trim()) {
    errors.push('Project goal is empty');
  }
  if (!model.state || !String(model.state.phase || '').trim()) {
    errors.push('Project phase is empty');
  }
  for (const task of model.tasks || []) {
    errors.push(...validateTask(task));
  }
  return errors;
}

function validateTask(task) {
  const errors = [];
  if (!String(task.id || '').trim()) {
    errors.push('Task missing id');
  }
  if (!String(task.title || '').trim()) {
    errors.push(`Task ${task.id} has empty title`);
  }
  if (!['pending', 'in_progress', 'done', 'blocked'].includes(task.status)) {
    errors.push(`Task ${task.id} has invalid status: ${task.status}`);
  }
  if (!['low', 'medium', 'high'].includes(task.priority)) {
    errors.push(`Task ${task.id} has invalid priority: ${task.priority}`);
  }
  if ((task.subtasks || []).length > 5) {
    errors.push(`Task ${task.id} exceeds maximum subtask limit of 5`);
  }
  for (const sub of task.subtasks || []) {
    errors.push(...validateTask(sub));
  }
  return errors;
}

export function contextScore(model) {
  let score = 0;
  if (model.project) {
    if (String(model.project.name || '').trim()) score += 15;
    if (String(model.project.goal || '').trim()) score += 20;
    if (String(model.project.description || '').trim()) score += 10;
  }
  if (model.state) {
    if (String(model.state.phase || '').trim()) score += 10;
    if (String(model.state.current_task || '').trim()) score += 15;
    if (String(model.state.current_subtask || '').trim()) score += 10;
  }
  const tasks = model.tasks || [];
  if (tasks.length > 0) score += 10;
  if (tasks.some((t) => (t.subtasks || []).length > 0)) score += 10;
  return Math.min(score, 100);
}

// --- Decomposer suggestions ---

function suggestSubtasks(taskTitle) {
  const title = String(taskTitle || '').toLowerCase();

  if (['auth', 'login', 'signup'].some((k) => title.includes(k))) {
    return ['Create login UI', 'Validate credentials', 'Create auth middleware', 'Add session handling', 'Add logout support'];
  }
  if (['api', 'endpoint', 'route'].some((k) => title.includes(k))) {
    return ['Define API schema', 'Create route handlers', 'Add input validation', 'Add error handling', 'Write API tests'];
  }
  if (['database', 'db', 'model', 'schema'].some((k) => title.includes(k))) {
    return ['Define data models', 'Create migrations', 'Add CRUD operations', 'Add indexes', 'Test database operations'];
  }
  if (['ui', 'frontend', 'page', 'component'].some((k) => title.includes(k))) {
    return ['Create component structure', 'Add styling', 'Add state management', 'Connect to API', 'Test UI interactions'];
  }
  if (['test', 'testing', 'spec'].some((k) => title.includes(k))) {
    return ['Write unit tests', 'Write integration tests', 'Add test fixtures', 'Run test suite', 'Fix failing tests'];
  }
  if (['setup', 'init', 'install', 'config'].some((k) => title.includes(k))) {
    return ['Create project structure', 'Install dependencies', 'Configure environment', 'Add configuration files', 'Verify setup'];
  }
  if (['doc', 'readme', 'guide'].some((k) => title.includes(k))) {
    return ['Write overview section', 'Document installation steps', 'Document usage examples', 'Add API reference', 'Review and publish'];
  }
  return ['Research and plan', 'Implement core logic', 'Add error handling', 'Write tests', 'Review and refine'];
}

// --- Suggester ---

function suggestApproaches(taskTitle) {
  const title = taskTitle;
  return {
    task: title,
    suggestions: {
      A: {
        label: 'Safe',
        description: `Simple and stable implementation of ${title}`,
        pros: ['Easy to implement', 'Low risk', 'Easy to debug', 'Familiar patterns'],
        cons: ['May not scale well', 'Limited flexibility', 'Basic architecture'],
        complexity: 'Low',
        time_estimate: 'Short',
        risk: 'Low'
      },
      B: {
        label: 'Optimized',
        description: `Balanced architecture for ${title}`,
        pros: ['Good performance', 'Maintainable code', 'Moderate scalability', 'Industry standard patterns'],
        cons: ['Moderate complexity', 'Requires planning', 'More initial setup'],
        complexity: 'Medium',
        time_estimate: 'Moderate',
        risk: 'Medium'
      },
      C: {
        label: 'Advanced',
        description: `Scalable and future-proof implementation of ${title}`,
        pros: ['Highly scalable', 'Maximum flexibility', 'Production ready', 'Future proof'],
        cons: ['High complexity', 'Longer implementation', 'Requires expertise', 'Over-engineering risk'],
        complexity: 'High',
        time_estimate: 'Long',
        risk: 'Medium-High'
      }
    },
    recommended: 'B'
  };
}

function recordSelection(taskId, selected) {
  const normalized = String(selected || '').toUpperCase();
  if (!['A', 'B', 'C'].includes(normalized)) {
    throw new Error(`Invalid selection: ${selected}. Must be A, B or C`);
  }
  return { task_id: taskId, selected: normalized, rationale: 'user selected' };
}

// --- Compressed context block ---

async function buildCompressedBlock(model, decisions) {
  const c = {
    current_task: model.state?.current_task || '',
    current_subtask: model.state?.current_subtask || '',
    rules: {
      execute_one_subtask_only: Boolean(model.rules?.execute_one_subtask_only),
      always_use_context: Boolean(model.rules?.always_use_context)
    },
    decisions: (decisions || []).slice(-3),
    pending_tasks: (model.tasks || [])
      .filter((t) => t.status === 'pending')
      .slice(0, 5)
      .map((t) => ({ id: t.id, title: t.title })),
    project_goal: model.project?.goal || '',
    phase: model.state?.phase || ''
  };

  let currentTaskTitle = '';
  let currentSubtaskTitle = '';
  for (const task of model.tasks || []) {
    if (task.id === c.current_task) {
      currentTaskTitle = task.title;
      for (const sub of task.subtasks || []) {
        if (sub.id === c.current_subtask) {
          currentSubtaskTitle = sub.title;
        }
      }
    }
  }

  const lines = [
    '=== CONTEXT OS ===',
    `CURRENT TASK: ${currentTaskTitle || c.current_task}`
  ];

  if (currentSubtaskTitle) {
    lines.push(`CURRENT SUBTASK: ${currentSubtaskTitle}`);
  }

  lines.push('RULES: one subtask at a time');

  for (const d of c.decisions) {
    lines.push(`DECISION [${d.task_id}]: ${d.selected_option}`);
  }

  if (c.pending_tasks.length > 0) {
    lines.push(`PENDING: ${c.pending_tasks.map((t) => t.title).join(', ')}`);
  }

  lines.push(`PHASE: ${c.phase}`);
  lines.push(`GOAL: ${c.project_goal}`);
  lines.push('=================');

  let block = lines.join('\n');
  const tokenCount = await countTokens(block);
  if (tokenCount > PRIORITY_LIMIT) {
    block = await trimToLimit(block, PRIORITY_LIMIT);
  }
  return block;
}

// --- ContextOS client ---

export class ContextOS {
  /**
   * @param {string} [projectRoot] Directory containing `.contextos/`.
   */
  constructor(projectRoot) {
    this.projectRoot = path.resolve(projectRoot || process.cwd());
    this.contextosDir = contextosDirOf(this.projectRoot);
    this.aicfPath = aicfPathOf(this.projectRoot);
    this.ignoreRules = loadIgnoreRules(this.projectRoot);
  }

  // --- Load / Save ---

  async loadContext() {
    if (!existsSync(this.aicfPath)) {
      throw new Error(`AICF file not found at ${this.aicfPath}`);
    }
    return readJson(this.aicfPath);
  }

  async saveContext(model) {
    await writeJson(this.aicfPath, model);
  }

  async _loadMemory() {
    return readJson(path.join(this.contextosDir, 'memory.json')).catch(() => ({
      snapshots: [],
      compressed_history: [],
      last_compressed: null
    }));
  }

  async _saveMemory(data) {
    await writeJson(path.join(this.contextosDir, 'memory.json'), data);
  }

  async _loadDecisions() {
    return readJson(path.join(this.contextosDir, 'decisions.json')).catch(() => ({ decisions: [] }));
  }

  async _saveDecisions(data) {
    await writeJson(path.join(this.contextosDir, 'decisions.json'), data);
  }

  // --- Read ---

  async getCurrentTask() {
    const model = await this.loadContext();
    const id = model.state?.current_task;
    return (model.tasks || []).find((t) => t.id === id) || null;
  }

  async getCurrentSubtask() {
    const task = await this.getCurrentTask();
    if (!task) return null;
    const model = await this.loadContext();
    const id = model.state?.current_subtask;
    if (!id) return null;
    return (task.subtasks || []).find((s) => s.id === id) || null;
  }

  async getNextTask() {
    const model = await this.loadContext();
    return (model.tasks || []).find((t) => t.status === 'pending') || null;
  }

  async getNextSubtask() {
    const task = await this.getCurrentTask();
    if (!task) return null;
    return (task.subtasks || []).find((s) => s.status === 'pending') || null;
  }

  // --- Update ---

  async updateTaskStatus(taskId, status) {
    const model = await this.loadContext();
    let updated = false;
    for (const task of model.tasks || []) {
      if (task.id === taskId) {
        task.status = status;
        if (status === 'done') task.completed_at = nowIso();
        updated = true;
        break;
      }
      for (const sub of task.subtasks || []) {
        if (sub.id === taskId) {
          sub.status = status;
          if (status === 'done') sub.completed_at = nowIso();
          updated = true;
          break;
        }
      }
      if (updated) break;
    }
    if (updated) await this.saveContext(model);
    return updated;
  }

  async setCurrentTask(taskId) {
    const model = await this.loadContext();
    const found = (model.tasks || []).some((t) => t.id === taskId);
    if (!found) return false;
    model.state.current_task = taskId;
    await this.saveContext(model);
    return true;
  }

  async setCurrentSubtask(subtaskId) {
    const model = await this.loadContext();
    const found = (model.tasks || []).some((t) =>
      (t.subtasks || []).some((s) => s.id === subtaskId)
    );
    if (!found) return false;
    model.state.current_subtask = subtaskId;
    await this.saveContext(model);
    return true;
  }

  // --- Status ---

  async status() {
    const model = await this.loadContext();
    const task = await this.getCurrentTask();
    const subtask = await this.getCurrentSubtask();
    const tasks = model.tasks || [];
    const done = tasks.filter((t) => t.status === 'done').length;
    return {
      project: model.project?.name,
      goal: model.project?.goal,
      phase: model.state?.phase,
      current_task: task ? task.title : 'None',
      current_subtask: subtask ? subtask.title : 'None',
      progress: `${done}/${tasks.length} tasks done`,
      tasks
    };
  }

  async score() {
    return contextScore(await this.loadContext());
  }

  // --- Tasks ---

  async nextTask() {
    const task = await this.getNextTask();
    return task || {};
  }

  async nextSubtask() {
    const sub = await this.getNextSubtask();
    return sub || {};
  }

  async done(taskId) {
    return this.updateTaskStatus(taskId, 'done');
  }

  async decompose(taskId) {
    const model = await this.loadContext();
    const task = (model.tasks || []).find((t) => t.id === taskId);
    if (!task) return [];
    const titles = suggestSubtasks(task.title).slice(0, 5);
    const subtasks = titles.map((title, i) => ({
      id: `${taskId}.${i + 1}`,
      title,
      status: 'pending',
      priority: task.priority || 'medium',
      notes: null,
      subtasks: [],
      created_at: nowIso(),
      completed_at: null
    }));
    task.subtasks = subtasks;
    await this.saveContext(model);
    return subtasks;
  }

  async suggest(taskId) {
    const model = await this.loadContext();
    const task = (model.tasks || []).find((t) => t.id === taskId);
    if (!task) return {};
    return suggestApproaches(task.title);
  }

  async decide(taskId, option) {
    const selection = recordSelection(taskId, option);
    const data = await this._loadDecisions();
    data.decisions.push({
      id: `d${data.decisions.length + 1}`,
      task_id: taskId,
      selected_option: String(option).toUpperCase(),
      rationale: 'sdk selected',
      timestamp: nowIso()
    });
    await this._saveDecisions(data);
    return selection;
  }

  // --- Context injection ---

  async inject(prompt, overrides) {
    const model = await this.loadContext();
    const errors = validateAicf(model);
    if (errors.length > 0) {
      throw new Error(`Invalid context:\n${errors.join('\n')}`);
    }

    const decisions = (await this._loadDecisions()).decisions;
    let block = await buildCompressedBlock(model, decisions);

    if (overrides) {
      for (const [key, value] of Object.entries(overrides)) {
        block += `\nOVERRIDE ${key.toUpperCase()}: ${value}`;
      }
    }

    const finalPrompt = `${block}\n\nUSER REQUEST:\n${prompt}`;
    const tokenCount = await countTokens(finalPrompt);

    const memory = await this._loadMemory();
    memory.compressed_history.push({
      type: 'interaction',
      token_count: tokenCount,
      timestamp: nowIso()
    });
    memory.last_compressed = nowIso();
    await this._saveMemory(memory);

    return finalPrompt;
  }

  async explain(taskId) {
    let model = await this.loadContext();
    if (taskId) {
      model = JSON.parse(JSON.stringify(model));
      model.state.current_task = taskId;
    }
    const decisions = (await this._loadDecisions()).decisions;
    const block = await buildCompressedBlock(model, decisions);
    const tokenCount = await countTokens(block);
    const score = contextScore(model);
    return (
      `\n=== CONTEXT EXPLAIN ===\n${block}\n` +
      `\nContext Score : ${score}/100` +
      `\nToken Count   : ${tokenCount} tokens` +
      `\n=======================\n`
    );
  }

  // --- Memory ---

  async snapshot(label) {
    const model = await this.loadContext();
    const memory = await this._loadMemory();
    const snapshotId = `snap_${snapshotStamp()}`;
    const timestamp = nowIso();
    const snapshot = { id: snapshotId, label: label || '', timestamp, aicf: model };
    await writeJson(path.join(this.contextosDir, 'snapshots', `${snapshotId}.json`), snapshot);

    memory.snapshots.push({ id: snapshotId, label: label || '', timestamp });
    if (memory.snapshots.length > 10) {
      const oldest = memory.snapshots.shift();
      await rm(path.join(this.contextosDir, 'snapshots', `${oldest.id}.json`), { force: true });
    }
    await this._saveMemory(memory);
    return snapshotId;
  }

  async snapshots() {
    const memory = await this._loadMemory();
    return memory.snapshots;
  }

  async rollback() {
    const memory = await this._loadMemory();
    if (!memory.snapshots.length) return false;
    const latest = memory.snapshots[memory.snapshots.length - 1];
    const snapshot = await readJson(
      path.join(this.contextosDir, 'snapshots', `${latest.id}.json`)
    );
    if (!snapshot?.aicf) return false;

    await this.snapshot('before_rollback');
    await this.saveContext(snapshot.aicf);
    return true;
  }

  async decisions() {
    const data = await this._loadDecisions();
    return data.decisions;
  }

  // --- Stats ---

  async stats() {
    const model = await this.loadContext();
    const decisions = (await this._loadDecisions()).decisions;
    const memory = await this._loadMemory();
    const snapshots = memory.snapshots;

    const tasksCompleted = (model.tasks || []).filter((t) => t.status === 'done').length;
    const subtasksCompleted = (model.tasks || []).reduce(
      (sum, t) => sum + (t.subtasks || []).filter((s) => s.status === 'done').length,
      0
    );

    const interactions = (memory.compressed_history || []).filter(
      (h) => h.type === 'interaction'
    );
    const totalTokensInjected = interactions.reduce(
      (sum, h) => sum + (Number(h.token_count) || 0),
      0
    );

    const block = await buildCompressedBlock(model, decisions);
    const currentTokens = await countTokens(block);

    return {
      project: model.project?.name,
      context_score: contextScore(model),
      interactions: interactions.length,
      total_tokens_injected: totalTokensInjected,
      current_context_tokens: currentTokens,
      decisions_recorded: decisions.length,
      snapshots_saved: snapshots.length,
      tasks_completed: tasksCompleted,
      subtasks_completed: subtasksCompleted,
      total_tasks: (model.tasks || []).length
    };
  }

  // --- Ignore utilities ---

  isIgnored(pathStr) {
    return isIgnoredPath(pathStr, this.ignoreRules);
  }

  filterPaths(paths) {
    return paths.filter((p) => !this.isIgnored(p));
  }

  async countTokens(text) {
    return countTokens(text);
  }
}

export default ContextOS;
