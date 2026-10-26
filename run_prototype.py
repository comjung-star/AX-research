from pathlib import Path
import os
import sys


def main():
    root = Path(__file__).resolve().parent
    os.chdir(root)
    if (root / ".local/models/bge-m3/config.json").exists():
        os.environ.setdefault("AX_BGE_MODEL_PATH", str(root / ".local/models/bge-m3"))
    from prototype.server import main as serve
    serve()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log = Path(__file__).resolve().parent / ".local/ax-prototype/startup-error.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        message = "프로그램을 시작하지 못했습니다. 실행 안내의 환경 준비 단계를 확인해 주세요."
        log.write_text(message + "\n" + type(sys.exception()).__name__, encoding="utf-8")
        if os.name == "nt":
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "AX 나침반", 0x10)
        else:
            print(message, file=sys.stderr)
        sys.exit(1)
