from __future__ import annotations

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import subprocess

from .runtime import Control


@dataclass(frozen=True)
class Media:
    width: int
    height: int
    fps: Fraction
    duration: float
    audio: bool
    frames: int
    codec: str
    stream_index: int = 0
    reported_frames: int | None = None


def parse_probe(document: dict) -> Media:
    streams = document.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    if not video:
        raise ValueError("В файле не найдена видеодорожка")
    if video.get("color_transfer") in {"smpte2084", "arib-std-b67"}:
        raise ValueError("В первой версии поддерживается SDR. HDR нужно сначала преобразовать в SDR.")
    if video.get("color_primaries") in {"bt2020", "smpte431", "smpte432"}:
        raise ValueError("Широкий цветовой охват сначала нужно преобразовать в SDR BT.709.")
    if video.get("field_order", "unknown") not in {"unknown", "progressive"}:
        raise ValueError("Чересстрочное видео сначала нужно деинтерлейсить. Эта версия рассчитана на progressive SDR.")
    sar = video.get("sample_aspect_ratio", "1:1")
    if sar not in {"1:1", "0:1", "N/A", None}:
        raise ValueError("Анаморфное видео сначала нужно преобразовать к квадратным пикселям (SAR 1:1).")
    width, height = int(video["width"]), int(video["height"])
    rotation = next((float(x["rotation"]) for x in video.get("side_data_list", []) if "rotation" in x),
                    float(video.get("tags", {}).get("rotate", 0)))
    if round(rotation) % 180:
        if round(rotation) % 90:
            raise ValueError("Поддерживается поворот только на 90°, 180° и 270°")
        width, height = height, width
    fps = Fraction(0)
    for key in ("avg_frame_rate", "r_frame_rate"):
        try:
            fps = Fraction(video.get(key, "0/1"))
        except (ValueError, ZeroDivisionError):
            continue
        if fps > 0:
            break
    if not 0 < fps <= 240:
        raise ValueError("Не удалось определить FPS в диапазоне 0–240")
    duration = 0.0
    for value in (video.get("duration"), document.get("format", {}).get("duration")):
        try:
            duration = float(value)
        except (ValueError, TypeError):
            continue
        if duration > 0:
            break
    if duration <= 0 or width <= 0 or height <= 0:
        raise ValueError("Не удалось определить длительность или размеры видео")
    reported_frames = None
    try:
        reported_frames = int(video.get("nb_frames", ""))
    except (ValueError, TypeError):
        pass
    return Media(width, height, fps, duration, any(s.get("codec_type") == "audio" for s in streams),
                 max(1, round(duration * float(fps))), video.get("codec_name", "?"), int(video.get("index", 0)), reported_frames)


def probe(path: Path, ffprobe: Path, control: Control, json_path: Path | None = None) -> Media:
    process = control.start([str(ffprobe), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        try:
            out, err = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise ValueError("Чтение информации о видео заняло больше минуты")
        control.check()
        if process.returncode:
            raise ValueError(err.decode("utf-8", "replace"))
        document = json.loads(out)
        if json_path:
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        return parse_probe(document)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        control.forget(process)
