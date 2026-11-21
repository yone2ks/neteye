import os
import subprocess
import sys

PROBE = (
    "from dynaconf import Dynaconf;"
    "s = Dynaconf(environments=True, settings_files=['settings.toml'],"
    " envvar_prefix='NETEYE', env='production');"
    "print(s.current_env, s.DEBUG, s.HOST)"
)


def _probe(env_name):
    env = {k: v for k, v in os.environ.items() if k != "ENV_FOR_DYNACONF"}
    if env_name:
        env["ENV_FOR_DYNACONF"] = env_name
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = subprocess.run(
        [sys.executable, "-c", PROBE], capture_output=True, text=True, cwd=root, env=env, check=True
    )
    return out.stdout.split()


def test_unset_env_falls_back_to_production_without_debug_on_loopback():
    assert _probe(None) == ["production", "False", "127.0.0.1"]


def test_development_env_still_enables_debug():
    env_name, debug, _ = _probe("development")
    assert (env_name, debug) == ("development", "True")
