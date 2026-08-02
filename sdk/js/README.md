# @contextos/sdk (JavaScript)

Official JavaScript SDK for ContextOS. Single-file, dependency-free (ESM),
no build step. Mirrors the [Python SDK](../python/contextos_sdk.py) API.

Requires Node.js >= 18.

## Install

```bash
npm install @contextos/sdk
```

## Quick start

```js
import { ContextOS } from '@contextos/sdk';

const sdk = new ContextOS('/path/to/project');

const prompt = await sdk.inject('implement auth for the admin panel');
console.log(prompt); // assembled context block + your request

await sdk.done('1.2');          // mark subtask complete
await sdk.decide('1', 'B');     // record a decision
await sdk.snapshot('before-refactor');
console.log(await sdk.status()); // { project, phase, current_task, progress }
```

`ContextOS` resolves the project root by walking up to the directory
containing `.contextos/` (pass `{ root: true }` in `new ContextOS` when
`path` already is that root).

## API

Core:

- `loadContext()`, `saveContext(model)` — read/write `.contextos/aicf.json`
- `status()`, `score()`, `stats()` — project summary
- `getCurrentTask()`, `getCurrentSubtask()`
- `getNextTask()`, `getNextSubtask()`, `nextTask()`, `nextSubtask()`
- `setCurrentTask(id)`, `setCurrentSubtask(id)` — validate ids, return boolean
- `done(id)` — mark a task/subtask done, sets `completed_at`
- `updateTaskStatus(id, status)`

Context assembly:

- `inject(userRequest)` — build the full prompt block, append to memory history
- `explain(id)` — preview the block for another task without saving
- `decompose(id)` — suggest subtasks for a task
- `suggest(id)` — return A/B/C approach suggestions
- `decide(id, option)` — record a decision in `decisions.json`

Memory & safety:

- `snapshot(label)`, `rollback()` — snapshot/restore `aicf.json` in `.contextos/snapshots/`
- `snapshots()` — list saved snapshots
- `decisions()` — list recorded decisions

Utilities:

- `isIgnoredPath(p)`, `loadIgnoreRules(root)`, `filterPaths(paths)`
- `countTokens(text)` — uses `gpt-tokenizer` if installed, else `chars/4` fallback
- `setTokenEncoder(fn)` — plug in a custom token counter
- `buildCompressedBlock(model, decisions)`
- `validateAicf(model)`, `contextScore(model)`
- `findProjectRoot(start)` — exported constants: `DEFAULT_IGNORE_RULES`, `PRIORITY_LIMIT`

## Tests

```bash
npm test
```

Runs the Node built-in test runner against `test/` (28 tests covering
engine, ignore rules, and SDK behaviors).

## Notes

- Token counting is heuristic when `gpt-tokenizer` is not installed. Install
  it as an optional dependency for exact counts.
- Sync (`sync push` / `sync pull`) is planned to reuse the same git-backed
  mechanism as the Python SDK.
