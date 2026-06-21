# framesbymaddy-portfolio

Professional video editing and photography portfolio website built with Flask, SQLite, HTML, CSS, and JavaScript.

## GitHub JSON sync

Projects are stored in `data/projects.json` with a local backup at `data/projects.backup.json`. When deployed (e.g. on Render), the filesystem is ephemeral — GitHub sync keeps project data durable across restarts.

Set these environment variables to enable sync:

| Variable | Example | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | `ghp_...` | Personal access token with repo contents read/write |
| `GITHUB_REPO` | `owner/FramesByMaddy` | Target repository (`owner/name`) |
| `GITHUB_BRANCH` | `main` | Branch to read/write |

Copy `.env.example` to `.env` for local development. Never commit tokens.

### Behavior

- **Startup**: restores `data/projects.json` from GitHub when configured; falls back to local file, backup, or defaults on failure.
- **Admin changes**: every project add/edit/delete saves locally first, then pushes to GitHub (best-effort).
- **Local safety**: if GitHub sync fails, local saves and backup/recovery are never affected.
- **Admin status**: the admin panel shows **Synced**, **Local Only** (sync not configured), or **Sync Failed**.

### Token permissions

- Classic PAT: `repo` scope, or
- Fine-grained token: **Contents** read and write on the target repository.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Visit http://localhost:5000 — admin panel at http://localhost:5000/admin.
