import os
from pathlib import Path


def load_local_env(path=None):
    source = Path(path) if path is not None else Path(__file__).resolve().parents[1] / ".env"
    if not source.is_file():
        return
    allowed = {"OPENAI_API_KEY", "AX_LLM_MODEL", "AX_BGE_MODEL_PATH"}
    for raw_line in source.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not separator or name not in allowed or os.getenv(name):
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if value and "\x00" not in value:
            os.environ[name] = value
