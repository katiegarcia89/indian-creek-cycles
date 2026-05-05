# Git Command Shortcuts

Quick Git commands for the Indian Creek Cycles project.

## Check Where You Are

Show current branch:

```bash
git branch --show-current
```

Show all local branches:

```bash
git branch
```

Show local and remote branches:

```bash
git branch -a
```

Check changed files:

```bash
git status
```

## Switch Branches

Switch to an existing branch:

```bash
git checkout branch-name
```

Example:

```bash
git checkout Newktbranch
```

Create a new branch and switch to it:

```bash
git checkout -b new-branch-name
```

## Save Work Before Switching

Stash changes:

```bash
git stash
```

See saved stashes:

```bash
git stash list
```

Bring stashed changes back:

```bash
git stash pop
```

## Pull Updates

Fetch remote branches:

```bash
git fetch origin
```

Pull the current branch:

```bash
git pull origin branch-name
```

Example:

```bash
git pull origin Newktbranch
```

If Git says branches diverged:

```bash
git pull --rebase origin branch-name
```

## Save and Push Your Work

Stage all changed files:

```bash
git add .
```

Stage one file:

```bash
git add path/to/file
```

Commit:

```bash
git commit -m "describe your change"
```

Push the current branch:

```bash
git push
```

Push a branch the first time:

```bash
git push -u origin branch-name
```

## Useful Recovery Commands

Check recent commits:

```bash
git log --oneline -5
```

Throw away local changes in one file:

```bash
git restore path/to/file
```

Throw away local changes in many files:

```bash
git restore .
```

Abort a rebase:

```bash
git rebase --abort
```

Continue after fixing conflicts:

```bash
git rebase --continue
```

Abort a cherry-pick:

```bash
git cherry-pick --abort
```

Continue after fixing cherry-pick conflicts:

```bash
git cherry-pick --continue
```

## PythonAnywhere Update Flow

From the Bash console:

```bash
cd ~/indian-creek-cycles
git branch --show-current
git pull origin branch-name
source .venv/bin/activate
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
touch /var/www/www_indiancreekcycles_com_wsgi.py
```

