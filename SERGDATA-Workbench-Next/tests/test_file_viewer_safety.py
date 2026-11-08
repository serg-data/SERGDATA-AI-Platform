from pathlib import Path
from tempfile import TemporaryDirectory
import pytest
from workbench.tools import ProjectTools


def test_file_viewer_path_policy_blocks_secrets_and_parent_traversal():
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / 'project'
        root.mkdir()
        (root / '.env').write_text('TOKEN=do-not-read', encoding='utf-8')
        tools = ProjectTools(root)
        with pytest.raises(ValueError):
            tools.safe('.env')
        with pytest.raises(ValueError):
            tools.safe('../outside.txt')


def test_file_viewer_accepts_regular_text_and_safe_env_example():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'main.py').write_text('print("hello")\n', encoding='utf-8')
        (root / '.env.example').write_text('PORT=8787\n', encoding='utf-8')
        tools = ProjectTools(root)
        assert tools.safe('main.py').read_text(encoding='utf-8') == 'print("hello")\n'
        assert tools.safe('.env.example').is_file()


def test_file_viewer_safe_path_rejects_symlink_escape_when_supported():
    with TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = base / 'project'; root.mkdir()
        outside = base / 'outside.txt'; outside.write_text('private', encoding='utf-8')
        link = root / 'outside-link.txt'
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            pytest.skip('Symlinks are not available in this environment')
        tools = ProjectTools(root)
        with pytest.raises(ValueError):
            tools.safe('outside-link.txt')
