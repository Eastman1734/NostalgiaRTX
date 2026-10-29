from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import threading
import traceback
from .pipeline import Job, convert, binaries, nvenc_check
from .runtime import Control, Cancelled
from .media import probe
from .backend import RTXVideo


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.request.read_text(encoding="utf-8"))
    work = Path(payload["work"])
    work.mkdir(parents=True, exist_ok=True)
    log = (work / "session.log").open("w", encoding="utf-8")
    output_lock = threading.Lock()
    def emit(kind, value):
        with output_lock:
            log.write(json.dumps({"event": kind, "data": value}, ensure_ascii=False)+"\n")
            log.flush()
            if kind != "log":
                print(json.dumps({"event": kind, "data": value}, ensure_ascii=False), flush=True)
    control = Control(emit)
    stopped = threading.Event()
    def watch_cancel():
        while not stopped.wait(.1):
            if (work / "cancel").exists():
                control.cancel()
                return
    threading.Thread(target=watch_cancel, daemon=True).start()
    try:
        operation = payload.pop("operation", "render")
        job = Job(**{k: Path(v) if k in {"source", "target", "root", "work"} else v for k, v in payload.items()})
        if operation == "probe":
            _, ffprobe = binaries(job.root)
            m = probe(job.source, ffprobe, control)
            emit("inspected", {"width": m.width, "height": m.height, "fps": str(m.fps),
                                "duration": m.duration, "audio": m.audio})
        elif operation == "doctor":
            ffmpeg, ffprobe = binaries(job.root)
            if job.source.is_file():
                media = probe(job.source, ffprobe, control)
                nvenc_check(ffmpeg, job, control, media.width*job.scale, media.height*job.scale)
            else:
                nvenc_check(ffmpeg, job, control)
            e = RTXVideo(640, 360, 2, job.quality, job.gpu, job.root, work / "ngx-cache")
            try:
                import numpy as np
                frame = np.zeros((360, 640, 4), np.uint8)
                frame[..., 3] = 255
                e.process(frame)
            finally:
                e.close()
            emit("doctor", "RTX Video VSR и NVENC: проверка кадра пройдена")
        else:
            convert(job, control)
        return 0
    except Cancelled:
        emit("cancelled", "Обработка отменена")
        return 130
    except Exception as error:
        log.write(traceback.format_exc())
        emit("error", str(error))
        return 1
    finally:
        stopped.set()
        log.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
