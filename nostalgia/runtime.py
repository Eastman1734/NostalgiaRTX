from __future__ import annotations

import os
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Callable

EventSink = Callable[[str, object], None]


class Cancelled(Exception):
    pass


class ProcessError(RuntimeError):
    pass


def data_dir() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    path = root / "NostalgiaRTX"
    path.mkdir(parents=True, exist_ok=True)
    return path


class Control:
    """Own every child process; cancellation unblocks pipe reads and writes."""

    def __init__(self, emit: EventSink = lambda *_: None):
        self.emit = emit
        self.cancelled = threading.Event()
        self._lock = threading.Lock()
        self._processes: set[subprocess.Popen] = set()

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled("Операция отменена")

    def cancel(self):
        self.cancelled.set()
        with self._lock:
            processes = tuple(self._processes)
        for process in processes:
            try:
                process.kill()
            except OSError:
                pass

    def start(self, args: list[str], **kwargs) -> subprocess.Popen:
        self.check()
        self.emit("log", subprocess.list2cmdline([str(x) for x in args]))
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        with self._lock:
            self.check()
            process = subprocess.Popen(args, shell=False, **kwargs)
            self._processes.add(process)
        return process

    def forget(self, process: subprocess.Popen):
        with self._lock:
            self._processes.discard(process)

    def finish(self, process: subprocess.Popen, timeout: float = 30) -> int:
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise ProcessError("Процесс не завершился вовремя")
        finally:
            self.forget(process)

    def run(self, args: list[str], cwd: Path | None = None) -> str:
        process = self.start(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        tail: deque[str] = deque(maxlen=70)
        try:
            assert process.stdout
            for line in iter(process.stdout.readline, b""):
                self.check()
                text = line.decode("utf-8", "replace").rstrip()
                tail.append(text)
                self.emit("log", text)
            code = self.finish(process)
            self.check()
            if code:
                raise ProcessError("\n".join(tail) or f"Код завершения: {code}")
            return "\n".join(tail)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            self.forget(process)
            if process.stdout:
                process.stdout.close()


class PipeLog:
    """Drain stderr concurrently so FFmpeg cannot deadlock on a full pipe."""

    def __init__(self, process: subprocess.Popen, control: Control):
        self.tail: deque[str] = deque(maxlen=50)
        self.stream = process.stderr
        self.control = control
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()

    def _read(self):
        if self.stream:
            for line in iter(self.stream.readline, b""):
                text = line.decode("utf-8", "replace").rstrip()
                self.tail.append(text)
                self.control.emit("log", text)

    def text(self) -> str:
        self.thread.join(timeout=2)
        return "\n".join(self.tail)
