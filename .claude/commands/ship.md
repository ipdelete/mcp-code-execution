---
model: haiku
---

# Ship Command

Run all quality checks from the GitHub workflow, then stage, commit, and push changes.

This ensures the code will pass CI when it reaches GitHub.

## Quality Checks

Run all tests first:

```bash
uv run pytest
```

Type checking with mypy:

```bash
uv run mypy src/
```

Linting with ruff:

```bash
uv run ruff check src/ tests/
```

Format checking with black:

```bash
uv run black --check src/ tests/
```

## Git Operations

Once all checks pass, stage all changes:

```bash
git add -A
```

Show the status before committing:

```bash
git status
```

Show recent commits for reference:

```bash
git log -5 --oneline
```

Review the staged changes:

```bash
git diff --cached
```

Generate commit message based on staged changes:

Review the changes above and create a descriptive commit message following conventional commits format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `test:` for tests
- `refactor:` for code refactoring

The message should include:
1. A clear subject line (50 chars or less)
2. A blank line
3. Detailed explanation of what changed and why
4. A blank line
5. Footer with: `🤖 Generated with Claude Code` and `Co-Authored-By: Claude <noreply@anthropic.com>`

Once you've generated the commit message, use git commit with the -m flag.

Push to remote:

```bash
git push
```
