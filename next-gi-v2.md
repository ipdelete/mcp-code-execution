# Declarative Tool Discovery: A New Architecture for Scaling Agent Tool Usage

## 1. Executive Summary

The existing `mcp-code-execution` pattern solves the problem of large tool *outputs* by having an agent write a script to summarize results. However, it does not solve the equally critical problem of large tool *inputs*. As the number of available tools grows into the hundreds, the current file-based discovery mechanism (`ls ./servers`) becomes a new source of context bloat, forcing the agent to read through dozens of files and function definitions to find the right tool. This is inefficient and unreliable.

This document proposes a new, more powerful pattern: **Declarative Tool Discovery**.

The core idea is to **move tool discovery into a semantic, just-in-time process driven by the agent's script itself**. Instead of exploring a filesystem, the agent writes a single script and declares the tools it needs using natural language. The execution harness intercepts these declarations, performs a semantic search against a pre-built tool registry, and dynamically injects only the requested typed tool wrappers into the script's execution scope.

This transforms `mcp-code-execution` from a passive script runner into an active, intelligent runtime that equips the agent with the precise tools it needs, exactly when it needs them, without ever cluttering its context with irrelevant options.

## 2. The Flaw in Filesystem-Based Discovery

The current progressive disclosure pattern is a significant improvement over including all tool schemas in the prompt. However, it relies on the agent exploring the `servers/` directory. This approach has critical scaling weaknesses:

*   **High Discovery Overhead:** With 150 tools, the agent must list hundreds of files and potentially read many of them to find the right one. This process consumes tokens and conversational turns, re-introducing the context bloat we seek to avoid.
*   **Brittle and Unnatural:** Agents are good at reasoning in natural language, not at parsing file structures and Python docstrings to infer functionality. This forces the agent into an unnatural workflow.
*   **Static and Inflexible:** The generated `servers/` tree is static. Adding or updating tools requires re-running a generation step and the agent re-exploring the filesystem.

## 3. The Declarative Tool Discovery Pattern

This pattern makes finding and using tools a seamless part of the script-writing process.

**Concept:** The agent writes a single Python script. At the top of the script, it uses a special function, `use_tools()`, to declare the capabilities it requires in plain English. The harness finds, generates, and injects the corresponding tools before executing the rest of the script.

### Example: Declarative Script

```python
# agent_script.py
import asyncio
from runtime.discovery import use_tools
from runtime.exceptions import ToolNotFound

# 1. Agent declares its needs in natural language.
# The harness will intercept this, search a tool registry,
# and dynamically generate and inject the typed wrappers.
try:
    use_tools(
        "a tool to get the git commit log",
        "a tool to see file changes between two commits"
    )
    # 2. The harness makes the wrappers available as if they were statically imported.
    from servers.git import git_log, git_diff, GitLogParams
except ToolNotFound as e:
    # The harness can provide feedback if a tool isn't found
    print(f"Could not find a tool for: {e.query}")
    # Agent can then try a different query.
    exit()


# 3. Agent uses the powerful, type-safe wrappers it asked for.
async def main():
    """Analyzes the last 5 commits."""
    print("Analyzing recent commits...")
    
    # Use the dynamically-loaded, typed wrapper
    log_result = await git_log(GitLogParams(max_count=5))
    
    if len(log_result.commits) < 2:
        print("Not enough commits to compare.")
        return

    # Use another loaded wrapper
    diff_result = await git_diff(
        commit_a=log_result.commits[1].sha,
        commit_b=log_result.commits[0].sha
    )

    summary = {
        "commit_count": len(log_result.commits),
        "latest_commit_author": log_result.commits[0].author,
        "files_changed_in_last_commit": len(diff_result.files)
    }

    print(f"Analysis complete: {summary}")
    return summary

if __name__ == "__main__":
    asyncio.run(main())

```

### Runtime Workflow

1.  The `harness` receives the script.
2.  **Pre-Execution Step:** It first parses the script to find the `use_tools()` call, without executing the code.
3.  It extracts the natural language queries: `"a tool to get the git commit log"`, etc.
4.  It performs a semantic search over a pre-compiled `tool_registry.json` to find the best matching tools (`git_log`, `git_diff`).
5.  It uses the logic from `generate_wrappers.py` to create the typed Pydantic models and async functions for *only these two tools* in memory.
6.  It dynamically creates a `servers.git` module and injects these functions into `sys.modules`.
7.  **Execution Step:** Only after the setup is complete does it execute the script's `main()` function. The `from servers.git import ...` line now works as expected.
8.  The script runs and returns the final JSON summary to the agent.

## 4. Architectural Transformation

This pattern reframes `mcp-code-execution` into an intelligent, agent-centric runtime.

*   **`generate_wrappers.py` → `build_tool_registry.py`**: This script's new role is to connect to all configured MCP servers, fetch their schemas, and build a single `tool_registry.json`. This registry contains tool names, servers, schemas, and, crucially, the natural language descriptions used for semantic search.
*   **`harness.py`**: The harness becomes significantly more powerful. It's no longer just a script runner; it's an execution environment that performs a vital pre-flight check to provision the script with the tools it needs.
*   **New `discovery.py` Module**: This module will contain the `use_tools()` function that scripts call, along with the logic to perform semantic search against the registry (e.g., using a lightweight sentence-transformer model).
*   **Dynamic Wrapper Generation**: The logic for creating Pydantic models and wrapper functions is centralized and used by the harness at runtime, not ahead of time.

## 5. Benefits of Declarative Tool Discovery

*   **Solves Tool Scaling:** The agent's initial context is minimal. It only needs to know how to use `use_tools()`. It never sees a list of 150 tools.
*   **Natural and Intuitive:** Agents can request tools using their core competency: natural language. This is a far more robust and flexible workflow than parsing filenames.
*   **Atomic and Efficient:** The entire discovery-and-execution process happens in a single step from the agent's perspective. It writes one script and gets one result.
*   **Retains All Existing Benefits:** The pattern preserves the core advantages of the original system: type-safety, lazy-loading of server connections, and the massive token reduction from summarizing final output.
*   **Extensible:** The semantic search can be improved over time (e.g., with better models, fine-tuning) without changing the agent's workflow at all.

## 6. Implementation Path

1.  **Phase 1: Tool Registry.** Refactor `generate_wrappers.py` into a `build_tool_registry.py` that fetches all schemas and creates a `tool_registry.json` file containing descriptions suitable for semantic search.
2.  **Phase 2: Discovery Logic.** Create the `discovery.py` module. Implement the `use_tools()` function and integrate a sentence-embedding library to perform semantic search over the registry.
3.  **Phase 3: Intelligent Harness.** Upgrade `harness.py` to implement the pre-execution/injection workflow. It must parse the script for `use_tools()`, call the discovery logic, and dynamically generate and inject the required wrappers before executing the main script body.
4.  **Phase 4: Documentation & Examples.** Update the `README.md` and create a new example script demonstrating the "Declarative Tool Discovery" pattern from end to end.
