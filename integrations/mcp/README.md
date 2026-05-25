# ContextOS MCP Integration

Connect ContextOS directly to Claude Code, Cursor, and any MCP-compatible AI agent.

---

## What This Does

Instead of manually running `context next` and copy-pasting context into your AI tool,
ContextOS becomes a native tool your AI agent can call automatically.

Claude Code can ask ContextOS:
- "What should I work on next?"
- "What decisions were made?"
- "Mark this subtask done"
- "Get compressed context for this prompt"

---

## Setup for Claude Code

### Step 1 — Add to Claude Code MCP config

Find or create your Claude Code MCP config file:

**Windows:**
%APPDATA%\Claude\claude_desktop_config.json

**Mac/Linux:**
~/.config/claude/claude_desktop_config.json

### Step 2 — Add ContextOS server

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": ["-m", "integrations.mcp.server"],
      "cwd": "C:/path/to/your/project"
    }
  }
}
```

Replace `C:/path/to/your/project` with your actual project path.

### Step 3 — Restart Claude Code

Claude Code will now have access to all ContextOS tools.

---

## Setup for Cursor

Add to Cursor MCP settings:

```json
{
  "mcpServers": {
    "contextos": {
      "command": "python",
      "args": ["-m", "integrations.mcp.server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

---

## Available Tools

| Tool | Description |
|---|---|
| `get_current_task` | Get active task and subtask |
| `get_next_task` | Get next pending task |
| `get_status` | Full project status and score |
| `get_context` | Compressed context for a prompt |
| `explain_context` | Preview context injection |
| `mark_done` | Mark task or subtask complete |
| `decompose_task` | Break task into subtasks |
| `get_suggestions` | A/B/C implementation options |
| `record_decision` | Save A/B/C decision |
| `get_stats` | Project statistics |
| `take_snapshot` | Save context checkpoint |
| `get_decisions` | View all decisions |

---

## Example Claude Code Workflow

Once connected, just talk to Claude Code naturally:
You: What should I work on next?
Claude Code: [calls get_next_task] → Task 1.2: Install dependencies
You: I finished that.
Claude Code: [calls mark_done with 1.2] → Done. Next: Configure environment
You: Give me context for building the auth system.
Claude Code: [calls get_context] → Injects 52 tokens of structured context

---

## Run Server Manually

Test the server directly:

```bash
python -m integrations.mcp.server
```

---

## Supported Agents

- Claude Code ✅
- Cursor ✅
- Any MCP-compatible agent ✅