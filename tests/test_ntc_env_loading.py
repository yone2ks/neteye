import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROBE = (
    "import neteye.extensions as e;"
    "print(len(e.ntc_template_utils.get_command_list('cisco_nxos')))"
)


def test_net_textfsm_only_in_dotenv_still_populates_command_candidates(tmp_path):
    """README tells users to put NET_TEXTFSM in .env; it must not need a shell export."""
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "index").write_text(
        "Template, Hostname, Platform, Command\n"
        "cisco_nxos_show_version.textfsm, .*, cisco_nxos, sh[[ow]] ver[[sion]]\n"
    )
    shutil.copy(ROOT / "settings.toml", tmp_path / "settings.toml")
    (tmp_path / ".env").write_text(f"NET_TEXTFSM={templates}\n")

    env = {k: v for k, v in os.environ.items() if k != "NET_TEXTFSM"}
    env.update(ENV_FOR_DYNACONF="testing", PYTHONPATH=str(ROOT))
    out = subprocess.run(
        [sys.executable, "-c", PROBE], capture_output=True, text=True, cwd=tmp_path, env=env, check=True
    )
    assert out.stdout.strip() == "1"
