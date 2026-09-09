"""
run.py — TRÌNH KHỞI CHẠY 1 LỆNH DUY NHẤT (ALL-IN-ONE RUNNER)
AI Financial & Investment Intelligence Platform

Khởi chạy nhanh toàn bộ dự án:
    python run.py

Tuỳ chọn nâng cao:
    python run.py               -> Chạy Web Platform (Streamlit + Lamp Login)
    python run.py --with-api    -> Chạy cả FastAPI Gateway (8000) + Web App (8501)
    python run.py --desktop     -> Chạy bản Desktop Tkinter (login_lamp.py)
    python run.py --api-only    -> Chỉ chạy FastAPI Gateway
    python run.py --test        -> Chạy toàn bộ 66 ca kiểm thử tự động
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any

# Đảm bảo Windows console xuất UTF-8 an toàn, không bị lỗi cp1252
if sys.platform == "win32":
    reconf_out = getattr(sys.stdout, "reconfigure", None)
    if callable(reconf_out):
        reconf_out(encoding="utf-8", errors="replace")
    reconf_err = getattr(sys.stderr, "reconfigure", None)
    if callable(reconf_err):
        reconf_err(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent

# Tự động phát hiện Python venv cục bộ nếu có
VENV_PYTHON_WIN = ROOT_DIR / ".venv" / "Scripts" / "python.exe"
VENV_PYTHON_POSIX = ROOT_DIR / ".venv" / "bin" / "python"


def get_python_exe() -> str:
    """Chọn interpreter Python ưu tiên từ .venv cục bộ."""
    if os.name == "nt" and VENV_PYTHON_WIN.exists():
        return str(VENV_PYTHON_WIN)
    if VENV_PYTHON_POSIX.exists():
        return str(VENV_PYTHON_POSIX)
    return sys.executable


def banner() -> None:
    print(r"""
========================================================================
     _    ___   _____ _                          _       _ 
    / \  |_ _| |  ___(_)_ __   __ _ _ __   ___ (_) __ _| |
   / _ \  | |  | |_  | | '_ \ / _` | '_ \ / __|| |/ _` | |
  / ___ \ | |  |  _| | | | | | (_| | | | | (__ | | (_| | |
 /_/   \_\___| |_|   |_|_| |_|\__,_|_| |_|\___||_|\__,_|_|
               INVESTMENT INTELLIGENCE PLATFORM
========================================================================
    """)


def run_tests(py: str) -> int:
    banner()
    print("[*] Đang thực thi bộ kiểm thử toàn diện hệ thống...")
    cmd = [py, "test_system.py"]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    return res.returncode


def run_desktop(py: str) -> int:
    banner()
    print("[*] Đang khởi chạy giao diện Desktop Tkinter (Lamp Login)...")
    cmd = [py, "login_lamp.py"]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    return res.returncode


def run_web(py: str, with_api: bool = False, port: int = 8501) -> None:
    banner()
    processes: list[subprocess.Popen[Any]] = []

    # Bắt tín hiệu ngắt Ctrl+C
    def cleanup(*args: Any) -> None:
        print("\n[*] Đang dừng các dịch vụ...")
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("[+] Đã dừng toàn bộ hệ thống an toàn. Tạm biệt!")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    if with_api:
        print("[+] Khởi động FastAPI Gateway tại http://localhost:8000 ...")
        p_api = subprocess.Popen(
            [py, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=str(ROOT_DIR),
        )
        processes.append(p_api)
        time.sleep(1.0)

    url = f"http://localhost:{port}"
    print(f"[+] Khởi động Giao diện Web (Streamlit + Lamp Login) tại {url} ...")
    print("[i] Kéo dây đèn (hoặc click / phím Space) trên giao diện để mở khoá hệ thống.")
    print("[i] Nhấn Ctrl+C trong cửa sổ này để tắt toàn bộ dịch vụ.\n")

    # Tự động mở trình duyệt web sau 1.5 giây
    def open_browser():
        time.sleep(1.8)
        webbrowser.open(url)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    p_web = subprocess.Popen(
        [
            py,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--theme.base=dark",
        ],
        cwd=str(ROOT_DIR),
    )
    processes.append(p_web)

    try:
        p_web.wait()
    except KeyboardInterrupt:
        cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trình khởi chạy 1 lệnh duy nhất cho AI Financial Platform"
    )
    parser.add_argument("--desktop", action="store_true", help="Chạy bản Desktop Tkinter")
    parser.add_argument("--with-api", action="store_true", help="Chạy kèm FastAPI Gateway độc lập")
    parser.add_argument("--api-only", action="store_true", help="Chỉ chạy FastAPI Gateway")
    parser.add_argument("--test", action="store_true", help="Chạy bộ kiểm thử toàn diện")
    parser.add_argument("--port", type=int, default=8501, help="Cổng Web (mặc định: 8501)")

    args = parser.parse_args()
    py = get_python_exe()

    if args.test:
        sys.exit(run_tests(py))
    elif args.desktop:
        sys.exit(run_desktop(py))
    elif args.api_only:
        banner()
        print("[+] Đang chạy FastAPI Gateway tại http://localhost:8000 ...")
        cmd = [py, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        subprocess.run(cmd, cwd=str(ROOT_DIR))
    else:
        run_web(py, with_api=args.with_api, port=args.port)


if __name__ == "__main__":
    main()

