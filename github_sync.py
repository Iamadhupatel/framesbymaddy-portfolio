"""
Reusable GitHub Contents API helpers for syncing JSON files.
Configure with GITHUB_TOKEN, GITHUB_REPO, and GITHUB_BRANCH.
"""

import base64
import json
import os
from typing import Any, Callable, Optional, Tuple

import requests

GITHUB_API = "https://api.github.com"
REQUEST_TIMEOUT = 10

SYNC_STATUS_SYNCED = "synced"
SYNC_STATUS_LOCAL_ONLY = "local_only"
SYNC_STATUS_FAILED = "sync_failed"

_sync_status = SYNC_STATUS_LOCAL_ONLY


class GitHubSyncError(Exception):
    """Raised when a GitHub sync operation fails."""


def github_sync_enabled() -> bool:
    return all(
        os.environ.get(name, "").strip()
        for name in ("GITHUB_TOKEN", "GITHUB_REPO", "GITHUB_BRANCH")
    )


def get_sync_status() -> str:
    return _sync_status


def set_sync_status(status: str) -> None:
    global _sync_status
    _sync_status = status


def _github_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN'].strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _repo_branch() -> Tuple[str, str]:
    return os.environ["GITHUB_REPO"].strip(), os.environ["GITHUB_BRANCH"].strip()


def _contents_url(repo_path: str) -> str:
    repo, _branch = _repo_branch()
    return f"{GITHUB_API}/repos/{repo}/contents/{repo_path.lstrip('/')}"


def fetch_remote_json(
    repo_path: str,
    logger=None,
    *,
    validator: Optional[Callable[[Any], None]] = None,
) -> Tuple[Any, Optional[str]]:
    """
    Fetch and parse a JSON file from GitHub.
    Returns (parsed_json, sha). sha is None when the remote file does not exist.
    """
    _, branch = _repo_branch()
    url = _contents_url(repo_path)
    try:
        response = requests.get(
            url,
            headers=_github_headers(),
            params={"ref": branch},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GitHubSyncError(f"GitHub fetch request failed: {exc}") from exc

    if response.status_code == 404:
        return None, None

    if response.status_code != 200:
        raise GitHubSyncError(
            f"GitHub fetch failed ({response.status_code}): {response.text[:200]}"
        )

    payload = response.json()
    encoded = payload.get("content", "")
    if payload.get("encoding") != "base64" or not encoded:
        raise GitHubSyncError("GitHub response did not include base64 file content.")

    try:
        raw = base64.b64decode(encoded).decode("utf-8")
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise GitHubSyncError(f"Remote JSON is invalid: {exc}") from exc

    if validator:
        validator(data)

    return data, payload.get("sha")


def push_remote_json(
    repo_path: str,
    data: Any,
    commit_message: str,
    logger=None,
    *,
    indent: int = 2,
) -> None:
    """Create or update a JSON file on GitHub."""
    _, branch = _repo_branch()
    url = _contents_url(repo_path)

    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        if not content.endswith("\n"):
            content += "\n"
    except (TypeError, ValueError) as exc:
        raise GitHubSyncError(f"JSON serialization failed: {exc}") from exc

    _, sha = fetch_remote_json(repo_path, logger)

    body = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha

    try:
        response = requests.put(
            url,
            headers=_github_headers(),
            json=body,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise GitHubSyncError(f"GitHub push request failed: {exc}") from exc

    if response.status_code not in (200, 201):
        raise GitHubSyncError(
            f"GitHub push failed ({response.status_code}): {response.text[:200]}"
        )

    if logger:
        logger.info("Synced %s to GitHub (%s)", repo_path, branch)


def restore_json_on_startup(
    repo_path: str,
    apply_data: Callable[[Any], None],
    logger=None,
    *,
    validator: Optional[Callable[[Any], None]] = None,
) -> bool:
    """
    Best-effort restore from GitHub on startup.
    Returns True when remote data was applied, False otherwise.
    """
    if not github_sync_enabled():
        set_sync_status(SYNC_STATUS_LOCAL_ONLY)
        return False

    try:
        data, sha = fetch_remote_json(repo_path, logger, validator=validator)
    except GitHubSyncError as exc:
        set_sync_status(SYNC_STATUS_FAILED)
        if logger:
            logger.warning(
                "GitHub restore failed for %s, using local data: %s",
                repo_path,
                exc,
            )
        return False

    if data is None:
        set_sync_status(SYNC_STATUS_FAILED)
        if logger:
            logger.info(
                "Remote file %s not found on GitHub; using local data.",
                repo_path,
            )
        return False

    try:
        apply_data(data)
    except Exception as exc:
        set_sync_status(SYNC_STATUS_FAILED)
        if logger:
            logger.warning(
                "Failed to apply GitHub data for %s: %s",
                repo_path,
                exc,
            )
        return False

    set_sync_status(SYNC_STATUS_SYNCED)
    if logger:
        logger.info("Restored %s from GitHub.", repo_path)
    return True


def sync_json_after_local_write(
    repo_path: str,
    local_path: str,
    commit_message: str,
    logger=None,
) -> None:
    """Best-effort push after a successful local write. Never raises."""
    if not github_sync_enabled():
        set_sync_status(SYNC_STATUS_LOCAL_ONLY)
        return

    try:
        with open(local_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        push_remote_json(repo_path, data, commit_message, logger)
        set_sync_status(SYNC_STATUS_SYNCED)
    except (OSError, json.JSONDecodeError, GitHubSyncError) as exc:
        set_sync_status(SYNC_STATUS_FAILED)
        if logger:
            logger.warning(
                "GitHub push failed for %s, local save preserved: %s",
                repo_path,
                exc,
            )
