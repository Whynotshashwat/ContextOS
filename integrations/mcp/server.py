from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import asyncio
from integrations.mcp.tools import (
    tool_get_current_task,
    tool_get_next_task,
    tool_get_status,
    tool_get_context,
    tool_explain_context,
    tool_mark_done,
    tool_decompose_task,
    tool_get_suggestions,
    tool_record_decision,
    tool_get_stats,
    tool_take_snapshot,
    tool_get_decisions
)

# --- Server Setup ---

server = Server("contextos")


# --- Tool Definitions ---

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_current_task",
            description="Get the current active task and subtask in the project.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_next_task",
            description="Get the next pending task and subtask.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_status",
            description="Get full project status including progress, context score, current task and phase.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_context",
            description="Get compressed context injection for a user prompt. Always call this before sending a prompt to AI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The user prompt to inject context into"
                    }
                },
                "required": ["prompt"]
            }
        ),
        types.Tool(
            name="explain_context",
            description="Show exactly what context would be injected without sending anything.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="mark_done",
            description="Mark a task or subtask as done. Use task IDs like '1', '1.1', '2.3'.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task or subtask ID to mark as done"
                    }
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="decompose_task",
            description="Break a task into subtasks automatically.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to decompose"
                    }
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="get_suggestions",
            description="Get A/B/C implementation suggestions for a task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID to get suggestions for"
                    }
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="record_decision",
            description="Record an A/B/C decision for a task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID the decision is for"
                    },
                    "option": {
                        "type": "string",
                        "description": "Selected option: A, B, or C"
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Optional reason for selection"
                    }
                },
                "required": ["task_id", "option"]
            }
        ),
        types.Tool(
            name="get_stats",
            description="Get project statistics including interactions, tokens, decisions.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="take_snapshot",
            description="Save a context snapshot checkpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Optional label for the snapshot"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_decisions",
            description="Get all recorded decisions for this project.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


# --- Tool Handlers ---

@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:

    try:
        if name == "get_current_task":
            result = tool_get_current_task()

        elif name == "get_next_task":
            result = tool_get_next_task()

        elif name == "get_status":
            result = tool_get_status()

        elif name == "get_context":
            result = tool_get_context(arguments["prompt"])

        elif name == "explain_context":
            result = tool_explain_context()

        elif name == "mark_done":
            result = tool_mark_done(arguments["task_id"])

        elif name == "decompose_task":
            result = tool_decompose_task(arguments["task_id"])

        elif name == "get_suggestions":
            result = tool_get_suggestions(arguments["task_id"])

        elif name == "record_decision":
            result = tool_record_decision(
                arguments["task_id"],
                arguments["option"],
                arguments.get("rationale", "")
            )

        elif name == "get_stats":
            result = tool_get_stats()

        elif name == "take_snapshot":
            result = tool_take_snapshot(
                arguments.get("label", "")
            )

        elif name == "get_decisions":
            result = tool_get_decisions()

        else:
            result = {"error": f"Unknown tool: {name}"}

        import json
        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2, default=str)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


# --- Run ---

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()