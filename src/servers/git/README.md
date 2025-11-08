# git MCP Tools

Auto-generated wrappers for git MCP server.

## Tools

- `git_add`: Stage files for commit. Add file contents to the staging area (index) to prepare for the next commit.
- `git_blame`: Show line-by-line authorship information for a file, displaying who last modified each line and when.
- `git_branch`: Manage branches: list all branches, show current branch, create a new branch, delete a branch, or rename a branch.
- `git_checkout`: Switch branches or restore working tree files. Can checkout an existing branch, create a new branch, or restore specific files.
- `git_cherry_pick`: Cherry-pick commits from other branches. Apply specific commits to the current branch without merging entire branches.
- `git_clean`: Remove untracked files from the working directory. Requires force flag for safety. Use dry-run to preview files that would be removed.
- `git_clear_working_dir`: Clear the session working directory setting. This resets the context without restarting the server. Subsequent git operations will require an explicit path parameter unless git_set_working_dir is called again.
- `git_clone`: Clone a repository from a remote URL to a local path. Supports HTTP/HTTPS and SSH URLs, with optional shallow cloning.
- `git_commit`: Create a new commit with staged changes in the repository. Records a snapshot of the staging area with a commit message.

**Commit Message Format:**
Pass commit messages as JSON string parameters. Multi-line messages are supported using standard JSON string escaping.

**Examples:**
- Single line: { "message": "feat: add user authentication" }
- Multi-line: { "message": "feat: add user authentication\n\nImplemented OAuth2 flow with JWT tokens.\nAdded tests for login and logout." }

Note: Do not use bash heredoc syntax.
- `git_diff`: View differences between commits, branches, or working tree. Shows changes in unified diff format.
- `git_fetch`: Fetch updates from a remote repository. Downloads objects and refs without merging them.
- `git_init`: Initialize a new Git repository at the specified path. Creates a .git directory and sets up the initial branch.
- `git_log`: View commit history with optional filtering by author, date range, file path, or commit message pattern.
- `git_merge`: Merge branches together. Integrates changes from another branch into the current branch with optional merge strategies.
- `git_pull`: Pull changes from a remote repository. Fetches and integrates changes into the current branch.
- `git_push`: Push changes to a remote repository. Uploads local commits to the remote branch.
- `git_rebase`: Rebase commits onto another branch. Reapplies commits on top of another base tip for a cleaner history.
- `git_reflog`: View the reference logs (reflog) to track when branch tips and other references were updated. Useful for recovering lost commits.
- `git_remote`: Manage remote repositories: list remotes, add new remotes, remove remotes, rename remotes, or get/set remote URLs.
- `git_reset`: Reset current HEAD to specified state. Can be used to unstage files (soft), discard commits (mixed), or discard all changes (hard).
- `git_set_working_dir`: Set the session working directory for all git operations. This allows subsequent git commands to omit the path parameter and use this directory as the default.
- `git_show`: Show details of a git object (commit, tree, blob, or tag). Displays commit information and the diff of changes introduced.
- `git_stash`: Manage stashes: list stashes, save current changes (push), restore changes (pop/apply), or remove stashes (drop/clear).
- `git_status`: Show the working tree status including staged, unstaged, and untracked files.
- `git_tag`: Manage tags: list all tags, create a new tag, or delete a tag. Tags are used to mark specific points in history (releases, milestones).
- `git_worktree`: Manage multiple working trees: list worktrees, add new worktrees for parallel work, remove worktrees, or move worktrees to new locations.
- `git_wrapup_instructions`: Provides the user's desired Git wrap-up workflow and instructions. Returns custom workflow steps (if configured) or default best practices for reviewing, documenting, and committing changes. Includes current repository status to guide next actions.

## Usage

```python
from runtime.servers.git import git_add

# Use the tool
result = await git_add(params)
```

**Note**: This file is auto-generated. Do not edit manually.
