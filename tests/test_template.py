"""Tests for envault.template."""

import os
import pytest

from envault.vault import Vault
from envault.template import TemplateError, render_string, render_file


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def vault_path(tmp_path):
    path = str(tmp_path / "vault.json")
    v = Vault(path, "secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    return path


# ---------------------------------------------------------------------------
# render_string
# ---------------------------------------------------------------------------


class TestRenderString:
    def test_single_placeholder(self, vault_path):
        result = render_string("host={{ DB_HOST }}", vault_path, "secret")
        assert result == "host=localhost"

    def test_multiple_placeholders(self, vault_path):
        result = render_string(
            "{{ DB_HOST }}:{{ DB_PORT }}", vault_path, "secret"
        )
        assert result == "localhost:5432"

    def test_no_placeholder_unchanged(self, vault_path):
        result = render_string("no placeholders here", vault_path, "secret")
        assert result == "no placeholders here"

    def test_placeholder_with_extra_spaces(self, vault_path):
        result = render_string("key={{  API_KEY  }}", vault_path, "secret")
        assert result == "key=abc123"

    def test_strict_raises_on_missing_key(self, vault_path):
        with pytest.raises(TemplateError, match="MISSING"):
            render_string("{{ MISSING }}", vault_path, "secret", strict=True)

    def test_non_strict_leaves_placeholder(self, vault_path):
        result = render_string(
            "{{ MISSING }}", vault_path, "secret", strict=False
        )
        assert result == "{{ MISSING }}"

    def test_mixed_resolved_and_unresolved_non_strict(self, vault_path):
        result = render_string(
            "{{ DB_HOST }} {{ NOPE }}", vault_path, "secret", strict=False
        )
        assert result == "localhost {{ NOPE }}"


# ---------------------------------------------------------------------------
# render_file
# ---------------------------------------------------------------------------


class TestRenderFile:
    def test_renders_template_file(self, vault_path, tmp_path):
        tmpl = tmp_path / "app.conf.tmpl"
        tmpl.write_text("host={{ DB_HOST }}\nport={{ DB_PORT }}\n")
        result = render_file(str(tmpl), vault_path, "secret")
        assert result == "host=localhost\nport=5432\n"

    def test_writes_output_file(self, vault_path, tmp_path):
        tmpl = tmp_path / "app.conf.tmpl"
        out = tmp_path / "app.conf"
        tmpl.write_text("api={{ API_KEY }}")
        render_file(str(tmpl), vault_path, "secret", str(out))
        assert out.read_text() == "api=abc123"

    def test_no_output_path_does_not_create_file(self, vault_path, tmp_path):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("{{ DB_HOST }}")
        render_file(str(tmpl), vault_path, "secret")
        assert not (tmp_path / "t.rendered").exists()

    def test_returns_rendered_content(self, vault_path, tmp_path):
        tmpl = tmp_path / "t.tmpl"
        tmpl.write_text("{{ API_KEY }}")
        result = render_file(str(tmpl), vault_path, "secret")
        assert result == "abc123"
