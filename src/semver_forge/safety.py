from .errors import SafetyError
from .git import branch, is_dirty


def check_release_state(root, cfg, allow_dirty=False):
    if cfg["git"].get("require_clean", True) and is_dirty(root) and not allow_dirty:
        raise SafetyError(
            "working tree is dirty (including staged/untracked files); "
            "commit or stash changes before release"
        )
    if branch(root) is None:
        raise SafetyError("detached HEAD; check out a branch before releasing")
