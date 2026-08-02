import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

export function makeProject(overrides = {}) {
  const root = mkdtempSync(path.join(tmpdir(), 'ctx-'));
  const dir = path.join(root, '.contextos');
  mkdirSync(path.join(dir, 'snapshots'), { recursive: true });
  mkdirSync(path.join(dir, 'logs'), { recursive: true });

  const aicf = {
    aicf_version: '1.0',
    project: { name: 'TestProject', goal: 'Test the SDK', description: 'A test project' },
    state: { phase: 'Testing', current_task: '1', current_subtask: '1.1' },
    tasks: [
      {
        id: '1',
        title: 'Setup project',
        status: 'in_progress',
        priority: 'high',
        subtasks: [
          { id: '1.1', title: 'Create structure', status: 'pending', priority: 'high', subtasks: [] },
          { id: '1.2', title: 'Install deps', status: 'pending', priority: 'high', subtasks: [] }
        ]
      },
      { id: '2', title: 'Build core', status: 'pending', priority: 'high', subtasks: [] }
    ],
    rules: { max_subtasks: 5, execute_one_subtask_only: true, always_use_context: true },
    config: { provider: '', model: '', api_key_env: '' }
  };

  const finalAicf = overrides.aicf ? { ...aicf, ...overrides.aicf } : aicf;
  writeFileSync(path.join(dir, 'aicf.json'), JSON.stringify(finalAicf, null, 2));
  writeFileSync(
    path.join(dir, 'memory.json'),
    JSON.stringify({ snapshots: [], compressed_history: [], last_compressed: null }, null, 2)
  );
  writeFileSync(
    path.join(dir, 'decisions.json'),
    JSON.stringify({ decisions: overrides.decisions || [] }, null, 2)
  );
  return root;
}

export function cleanup(root) {
  rmSync(root, { recursive: true, force: true });
}
