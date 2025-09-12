# Git Operations Subagent

## Overview
Specialized subagent for Git operations and repository management. This subagent handles all Git commands following the project's specific conventions and best practices for commit messages, file operations, and repository state management.

## Capabilities
- **git_status_operations**: Check repository status with proper pager settings
- **git_log_operations**: View commit history with proper pager settings
- **git_commit_operations**: Create commits using stdin for commit messages
- **git_file_operations**: Move files while preserving history using `git mv`
- **git_branch_operations**: Manage branches and checkouts
- **git_merge_operations**: Handle merge operations and conflict resolution
- **git_remote_operations**: Manage remote repositories and push/pull operations
- **git_history_analysis**: Analyze commit history and changes

## Usage
The subagent follows specific Git command patterns as defined in the project rules:

```bash
# Check repository status (no pager)
git --no-pager status

# View commit history (no pager)
git --no-pager log

# Create commits with stdin message
git commit -F - << 'EOF'
Commit message
EOF

# Move files preserving history
git mv old_file.py new_file.py

# Add files to staging
git add file1.py file2.py

# Reset changes
git reset HEAD file.py
git checkout -- file.py
```

## Configuration
- **Repository**: Current working directory
- **Commit Method**: `git commit -F -` with stdin input
- **Pager Settings**: `--no-pager` for status and log commands
- **File Operations**: Always use `git mv` for file moves
- **Message Format**: Descriptive commit messages explaining purpose

## Git Command Patterns

### Status and Log Operations
```bash
# Repository status
git --no-pager status

# Recent commits
git --no-pager log --oneline -10

# Detailed log
git --no-pager log --graph --pretty=format:'%h -%d %s (%cr) <%an>'

# Show changes
git --no-pager diff
git --no-pager diff --cached
```

### Commit Operations
```bash
# Stage files
git add file1.py file2.py
git add -A  # All changes
git add .   # Current directory

# Create commit with stdin message
echo "Add user authentication endpoints" | git commit -F -

# Amend last commit
echo "Fix typo in user model" | git commit --amend -F -
```

### File Operations
```bash
# Move files (preserves history)
git mv src/old_file.py src/new_file.py

# Remove files
git rm file.py
git rm -r directory/

# Restore files
git checkout -- file.py
git checkout HEAD -- file.py
```

### Branch Operations
```bash
# List branches
git branch -a

# Create and switch to branch
git checkout -b feature/new-feature

# Switch branches
git checkout main
git checkout feature/branch

# Merge branches
git merge feature/branch
git merge --no-ff feature/branch
```

### Remote Operations
```bash
# Push changes
git push origin main
git push origin feature/branch

# Pull changes
git pull origin main
git fetch origin
git merge origin/main

# Set upstream
git push -u origin feature/branch
```

## Commit Message Guidelines

### Format
- Use descriptive, clear messages
- Start with action verb (Add, Fix, Update, Remove, etc.)
- Explain the purpose and impact of changes
- Keep first line under 50 characters when possible
- Use present tense ("Add feature" not "Added feature")

### Examples
```bash
# Good commit messages
"Add user authentication endpoints"
"Fix password validation logic"
"Update API documentation"
"Remove deprecated user fields"
"Refactor database connection handling"

# Avoid
"fix stuff"
"updates"
"WIP"
"asdf"
```

## Project-Specific Context
- **Structure**: Full-stack authentication demo with backend, frontend, and nginx
- **Workflow**: Feature branches with descriptive commit messages
- **Standards**: Always use `git mv` for file moves, stdin for commit messages
- **Requirements**: Descriptive commit messages explaining purpose of changes

## Common Operations

### Daily Workflow
1. Check status: `git --no-pager status`
2. Stage changes: `git add file1.py file2.py`
3. Create commit: `echo "Message" | git commit -F -`
4. Push changes: `git push origin branch-name`

### Feature Development
1. Create branch: `git checkout -b feature/feature-name`
2. Make changes and commit regularly
3. Push branch: `git push -u origin feature/feature-name`
4. Create pull request
5. Merge to main after review

### File Management
1. Move files: `git mv old_path new_path`
2. Remove files: `git rm file.py`
3. Restore files: `git checkout -- file.py`

## Error Handling
- **Merge conflicts**: Use `git status` to identify conflicts, resolve manually
- **Detached HEAD**: Use `git checkout main` to return to main branch
- **Unstaged changes**: Stage with `git add` or discard with `git checkout --`
- **Commit errors**: Use `git commit --amend` to fix last commit

## Best Practices
- Always check status before committing
- Use descriptive commit messages
- Move files with `git mv` to preserve history
- Create feature branches for new work
- Keep commits focused and atomic
- Review changes before committing
