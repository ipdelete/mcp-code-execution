# The Generative Invocation (GI) Pattern: A New Architecture for Progressive Disclosure

## 1. Executive Summary

The existing packaging proposals (CC, CO, CX) correctly identify the agent discovery problem but converge on a conservative solution: repackaging the existing `mcp-code-execution` logic as a "meta-server." This approach, while functional, is not innovative. It introduces a clunky, stateful, multi-step workflow for the agent and centralizes a function that should be distributed. It solves a packaging problem but misses the opportunity to innovate on the MCP protocol itself.

This document proposes a brand new, more powerful pattern: **Generative Invocation (GI)**.

The core idea is to **move the progressive disclosure logic into the tool call itself**. Instead of an agent calling a separate server to execute a script, the agent provides a `result_handler` script as an optional parameter to *any* standard tool call. The tool server then executes the tool, runs the handler script against the raw output, and returns only the final, summarized result.

This transforms `mcp-code-execution` from a standalone server into a lightweight **SDK for MCP Tool Developers**. It becomes a library that any server can import to easily and safely support the GI pattern. This is a fundamental architectural shift that makes progressive disclosure a native, decentralized feature of the MCP ecosystem, rather than a bolted-on service.

## 2. The Flaw in the "Meta-Server" Model

The hybrid server model proposed by CC, CO, and CX forces an agent into a complex and inefficient conversational dance:

1.  **Agent → Meta-Server:** `generate_wrappers()`
2.  *(Meta-Server generates files in a shared workspace)*
3.  **Agent:** *(Writes a Python script that uses the generated files)*
4.  **Agent → Meta-Server:** `execute_script(script_path=...)
5.  *(Meta-Server runs the script, which does the actual work)*
6.  **Agent:** *(Receives the final, summarized result)*

This pattern has significant weaknesses:
*   **High Conversational Overhead:** It requires multiple turns, increasing token usage and the agent's cognitive load to manage the state of the interaction.
*   **Centralization:** It creates a single point of failure. If the `mcp-code-execution` server is down, this critical pattern is unavailable to all agents and tools.
*   **Clunky UX:** It feels like a workaround. The agent isn't just using a tool; it's orchestrating a complex build-and-run process with a secondary system.

## 3. The Generative Invocation (GI) Pattern

GI integrates progressive disclosure directly into the `call_tool` protocol.

**Concept:** An agent calls a tool and optionally provides a `result_handler` script. The server executes the tool, uses the script to process the output, and returns only the processed result.

### Example GI Tool Call

Imagine a `git.diff` tool that can produce a massive output.

```json
{
  "tool_name": "git.diff",
  "arguments": {
    "commit_a": "HEAD~10",
    "commit_b": "HEAD"
  },
  "result_handler": {
    "language": "python",
    "script": [
      "summary = {'files_changed': 0, 'insertions': 0, 'deletions': 0}",
      "for line in tool_output.split('\n'):",
      "    if line.startswith('---') or line.startswith('+++'):",
      "        continue",
      "    if line.startswith('diff --git'):",
      "        summary['files_changed'] += 1",
      "    elif line.startswith('+'):",
      "        summary['insertions'] += 1",
      "    elif line.startswith('-'):",
      "        summary['deletions'] += 1",
      "summary"
    ]
  }
}
```

### Server-Side Workflow

1.  The `git-server` receives the call.
2.  It executes the `git.diff` tool internally, producing a 50KB text output.
3.  It **does not** send this output to the agent.
4.  It sees the `result_handler` and invokes the GI SDK (`mcp-code-execution`).
5.  The SDK creates a secure sandbox, injects the 50KB diff into a `tool_output` variable, and executes the Python script.
6.  The script runs and produces a small JSON object: `{'files_changed': 15, 'insertions': 482, 'deletions': 109}`.
7.  The server sends **only this summary object** back to the agent as the tool's final result.

## 4. Architectural Transformation of `mcp-code-execution`

The project's role is completely reframed. It is no longer an application; it is a library.

**New Role: The "Generative Invocation SDK" for MCP Server Developers.**

The existing modules are repurposed:

*   `harness.py`: Becomes the core of the SDK. Its `execute_script` logic is wrapped into a new function, `execute_generative_invocation`, which handles sandboxing, injection, and execution of the `result_handler`.
*   `generate_wrappers.py` & `schema_utils.py`: These are no longer for agents. They become a powerful feature of the SDK, allowing a tool server to **dynamically generate and inject typed wrappers for its own tools** into the `result_handler`'s runtime scope. The agent can write a script that uses `servers.git.log()` without ever having to call `generate_wrappers` itself.
*   `mcp_client.py`: This allows the sandboxed `result_handler` script to call *other* MCP tools, enabling powerful, server-side tool chaining and data processing pipelines that are completely invisible to the agent.

### Example SDK Adoption

A tool developer for a `database-server` could support GI with minimal effort:

```python
# In a hypothetical database-server's main file
from mcp_gi_sdk import execute_generative_invocation, HandlerContext
from mcp.server import Server, Tool, TextContent

server = Server("database-server")

@server.call_tool()
async def call_tool(name: str, arguments: dict, result_handler: dict | None = None) -> list[TextContent]:
    # 1. Execute the actual tool to get the raw, large output
    raw_csv_output = await _internal_database_query(arguments.get("sql"))

    # 2. If a handler is provided, use the GI SDK to process the result
    if result_handler:
        # The context can be used by the SDK to inject typed wrappers for this server's tools
        context = HandlerContext(server_schema=server.get_schema())
        
        processed_output = await execute_generative_invocation(
            handler_script=result_handler,
            raw_tool_output=raw_csv_output,
            context=context
        )
        # Return the small, processed result
        return [TextContent(type="text", text=json.dumps(processed_output))]

    # 3. If no handler, return the raw output (or a truncated version)
    return [TextContent(type="text", text=raw_csv_output)]
```

## 5. Benefits of the GI Pattern

*   **Simplified Agent Logic:** Replaces a complex, multi-step process with a single, atomic tool call. This dramatically reduces the agent's cognitive load and prompt token count.
*   **Protocol-Native:** Makes progressive disclosure a first-class citizen of the MCP ecosystem. It's a feature of the tool, not a separate service.
*   **Decentralized & Scalable:** Execution is distributed to the edge (the tool servers), eliminating the meta-server bottleneck and improving scalability.
*   **Powerfully Composable:** `result_handler` scripts can call other tools, creating sophisticated server-side workflows without sending large intermediate payloads back to the agent.
*   **Truly Innovative:** This is a genuine "new pattern" that fundamentally improves how agents interact with data-heavy tools, moving the entire ecosystem forward.

## 6. Implementation Path

1.  **Phase 1: Create the SDK.** Refactor `mcp-code-execution` into a clean, installable Python package named `mcp-gi-sdk`. The primary export will be `execute_generative_invocation`.
2.  **Phase 2: Proof of Concept.** Modify an existing tool server (e.g., `git-server`) to import the SDK and support the `result_handler` parameter, demonstrating the pattern's viability.
3.  **Phase 3: Agent-Side Tooling.** Create helper functions and documentation for agent developers to easily construct and utilize GI calls.
4.  **Phase 4: Evangelism & Standardization.** Document the pattern and propose `result_handler` as a formal, optional extension to the MCP specification, encouraging widespread adoption by tool developers.

