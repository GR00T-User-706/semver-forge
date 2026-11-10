from pathlib import Path

import pytest

from semver_forge.cli import _authorization_required
from semver_forge.errors import ConfigError


def test_authorization_confirmation_defaults_to_true(tmp_path):
    assert _authorization_required(Path(tmp_path)) is True


def test_authorization_confirmation_can_be_disabled(tmp_path):
    root = Path(tmp_path)
    (root / ".semver-forge.toml").write_text(
        "[authorization]\nrequire_confirmation = false\n",
        encoding="utf-8",
    )

    assert _authorization_required(root) is False


def test_authorization_confirmation_must_be_boolean(tmp_path):
    root = Path(tmp_path)
    (root / ".semver-forge.toml").write_text(
        '[authorization]\nrequire_confirmation = "false"\n',
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="require_confirmation must be a boolean"):
        _authorization_required(root)
