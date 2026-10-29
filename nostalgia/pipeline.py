from __future__ import annotations
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
import numpy as np
from PIL import Image

from .backend import RTXVideo
from .media import Media, probe
from .runtime import Control, PipeLog, ProcessError


@dataclass(frozen=True)
class Job:
    source: Path
    target: Path
    root: Path
    work: Path
    scale: int = 2
    quality: int = 3
    gpu: int = 0
    cq: int = 18
    encoder: str = "h264_nvenc"
    audio: str = "aac"
    start: float = 0
    seconds: float = 0
    grayscale: bool = False

    def validate(self):
        if not self.source.is_file():
            raise ValueError("Выберите существующий видеофайл")
        if self.source.resolve() == self.target.resolve() or self.target.exists():
            raise ValueError("Результат уже существует или совпадает с оригиналом. Выберите другое имя.")
        if self.target.suffix.lower() != ".mp4":
            raise ValueError("Имя результата должно оканчиваться на .mp4")
        if self.scale not in {2, 4} or self.quality not in {1, 2, 3, 4} or not 1 <= self.cq <= 51:
            raise ValueError("Недопустимые настройки качества")
        if self.encoder not in {"h264_nvenc", "hevc_nvenc"} or self.audio not in {"aac", "copy"}:
            raise ValueError("Недопустимый кодек")
        if self.start < 0 or self.seconds < 0 or not math.isfinite(self.start + self.seconds):
            raise ValueError("Начало и длительность должны быть конечными неотрицательными числами")
        if self.gpu < 0 or self.gpu > 15:
            raise ValueError("Недопустимый номер GPU")


def binaries(root: Path) -> tuple[Path, Path]:
    ffmpeg, ffprobe = root / "bin/ffmpeg.exe", root / "bin/ffprobe.exe"
    if not ffmpeg.is_file() or not ffprobe.is_file():
        raise FileNotFoundError("Не найдены FFmpeg/FFprobe. Запустите INSTALL.cmd.")
    return ffmpeg, ffprobe


def read_frame(stream: BinaryIO, size: int, control: Control) -> bytes | None:
    frame = bytearray(size)
    view = memoryview(frame)
    offset = 0
    while offset < size:
        control.check()
        data = stream.read(size-offset)
        if not data:
            if offset:
                raise ProcessError(f"Неполный кадр: {offset} из {size} байт")
            return None
        view[offset:offset+len(data)] = data
        offset += len(data)
    return bytes(frame)


def decoder_command(ffmpeg: Path, job: Job, media: Media, frames: int) -> list[str]:
    return [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-threads", "2",
            "-ss", str(job.start), "-i", str(job.source), "-map", f"0:{media.stream_index}",
            "-an", "-sn", "-dn", "-vf", f"fps={media.fps},format=bgra", "-frames:v", str(frames),
            "-f", "rawvideo", "-pix_fmt", "bgra", "pipe:1"]


def encoder_command(ffmpeg: Path, job: Job, media: Media, target: Path) -> list[str]:
    args = [str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-nostdin", "-n",
            "-threads", "2", "-f", "rawvideo", "-pix_fmt", "rgba",
            "-video_size", f"{media.width*job.scale}x{media.height*job.scale}",
            "-framerate", str(media.fps), "-i", "pipe:0", "-an", "-c:v", job.encoder,
            "-gpu", str(job.gpu), "-preset", "p6", "-tune", "hq", "-rc", "vbr",
            "-cq", str(job.cq), "-b:v", "0", "-pix_fmt", "yuv420p",
            "-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709,setsar=1",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-color_range", "tv", "-metadata:s:v:0", "rotate=0", str(target)]
    return args


def mux_command(ffmpeg: Path, job: Job, video: Path, target: Path, duration: float) -> list[str]:
    return [str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-nostdin", "-n",
            "-i", str(video), "-ss", str(job.start), "-i", str(job.source),
            "-map", "0:v:0", "-map", "1:a?", "-map_metadata", "1", "-map_chapters", "-1",
            "-c:v", "copy", "-c:a", job.audio, *(["-b:a", "192k"] if job.audio == "aac" else []),
            "-t", f"{duration:.9f}", "-metadata:s:v:0", "rotate=0", "-movflags", "+faststart", str(target)]


def nvenc_check(ffmpeg: Path, job: Job, control: Control, width: int = 256, height: int = 256):
    name = "H.264" if job.encoder == "h264_nvenc" else "H.265"
    control.emit("status", f"Проверка {name} NVENC: {width} × {height}…")
    try:
        control.run([str(ffmpeg), "-hide_banner", "-loglevel", "error", "-nostdin", "-f", "lavfi",
                     "-i", f"color=black:size={width}x{height}:rate=1", "-frames:v", "1", "-c:v", job.encoder,
                     "-gpu", str(job.gpu), "-preset", "p6", "-tune", "hq", "-rc", "vbr",
                     "-cq", str(job.cq), "-b:v", "0", "-pix_fmt", "yuv420p", "-f", "null", "-"])
    except ProcessError as error:
        details = str(error)
        limit = re.search(r"(Width|Height)\s+(\d+)\s+exceeds\s+(\d+)", details, re.IGNORECASE)
        if limit:
            dimension = "ширины" if limit.group(1).lower() == "width" else "высоты"
            advice = "Для 4K из Full HD выберите ×2. Для 8K попробуйте H.265." if job.encoder == "h264_nvenc" else "Уменьшите масштаб или разрешение результата."
            raise ProcessError(f"{name} NVENC не поддерживает результат {width} × {height} на этом ПК.\n"
                               f"Лимит {dimension} по сообщению кодировщика: {limit.group(3)} пикселей.\n\n"
                               f"{advice}\n\nVSR ещё не запускался. Технический вывод сохранён в session.log.") from error
        raise ProcessError(f"Не удалось проверить {name} NVENC для {width} × {height}.\n"
                           "Проверьте кодек, выбранную видеокарту и драйвер.\n\n" + details[-1400:]) from error


def preview_images(original: np.ndarray, result: np.ndarray, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    before = Image.fromarray(original[..., [2, 1, 0]])
    after = Image.fromarray(result[..., :3])
    # Save just one comparison pair, with matching displayed geometry.
    before = before.resize(after.size, Image.Resampling.LANCZOS)
    for name, image in (("before.png", before), ("after.png", after)):
        image.thumbnail((1600, 1000), Image.Resampling.LANCZOS)
        image.save(folder / name)
    return str(folder / "before.png"), str(folder / "after.png")


def publish_new(temporary: Path, target: Path):
    # Both files live on the same volume; never overwrite an existing result.
    if os.name == "nt":
        temporary.rename(target)
    else:
        os.link(temporary, target)
        temporary.unlink()


def validate_result(source: Media, result: Media, scale: int, count: int) -> str | None:
    expected_size = (source.width*scale, source.height*scale)
    summary = (f"Ожидалось: {expected_size[0]} × {expected_size[1]}, "
               f"{source.fps} ({float(source.fps):.9f}) FPS, {count} кадров.\n"
               f"Получено: {result.width} × {result.height}, "
               f"{result.fps} ({float(result.fps):.9f}) FPS, "
               f"{result.reported_frames if result.reported_frames is not None else 'неизвестно'} кадров.")
    if (result.width, result.height) != expected_size:
        raise ProcessError("Размер результата отличается от выбранного.\n"+summary)
    if result.reported_frames is not None and result.reported_frames != count:
        raise ProcessError("Число кадров результата отличается от обработанного.\n"+summary)
    # A muxer may round the last sample's duration, changing avg_frame_rate
    # slightly without changing the frame cadence. Accept only a small rate
    # difference, with an independently verified exact frame count and duration.
    rounded_rate = result.fps != source.fps
    if rounded_rate and not (result.reported_frames == count and math.isclose(
            float(result.fps), float(source.fps), rel_tol=1e-4, abs_tol=1e-6)):
        raise ProcessError("Частота кадров результата отличается от выбранной.\n"+summary)
    expected_duration = count/float(source.fps)
    tolerance = max(.02, 1/float(source.fps))
    if abs(result.duration-expected_duration) > tolerance:
        raise ProcessError(f"Длительность результата отличается от ожидаемой.\n"
                           f"Ожидалось {expected_duration:.6f} с, получено {result.duration:.6f} с.\n"+summary)
    if source.audio and not result.audio:
        raise ProcessError("В результате отсутствует исходная звуковая дорожка.\n"+summary)
    if rounded_rate:
        return f"Небольшое округление FPS контейнером: {source.fps} → {result.fps}; число кадров и длительность проверены."
    return None


def convert(job: Job, control: Control, *, backend_factory=RTXVideo,
            tools: tuple[Path, Path] | None = None, check_encoder=True) -> Path:
    job.validate()
    ffmpeg, ffprobe = tools or binaries(job.root)
    job.target.parent.mkdir(parents=True, exist_ok=True)
    job.work.mkdir(parents=True, exist_ok=True)
    control.emit("status", "Чтение видео…")
    media = probe(job.source, ffprobe, control, json_path=job.work / "input-probe.json")
    if max(media.width*job.scale, media.height*job.scale) > 8192:
        raise ValueError("В этой версии размер результата ограничен 8192 пикселями по каждой стороне")
    if job.start >= media.duration:
        raise ValueError("Начало фрагмента находится за концом видео")
    duration = min(job.seconds or media.duration, media.duration-job.start)
    requested = max(1, math.ceil(duration*float(media.fps)-1e-8))
    control.emit("media", {"width": media.width, "height": media.height, "fps": str(media.fps),
                           "duration": media.duration, "output_width": media.width*job.scale,
                           "output_height": media.height*job.scale, "audio": media.audio,
                           "frames": requested})
    if shutil.disk_usage(job.target.parent).free < 256*1024**2:
        raise ValueError("Для начала нужно хотя бы 256 МБ свободного места в папке результата")
    if check_encoder:
        control.emit("status", "Проверка NVENC…")
        nvenc_check(ffmpeg, job, control, media.width*job.scale, media.height*job.scale)
    control.check()
    control.emit("status", "Инициализация NVIDIA RTX Video Super Resolution…")
    engine = backend_factory(media.width, media.height, job.scale, job.quality, job.gpu,
                             job.root, job.work / "ngx-cache")
    decoder = encoder = None
    count = 0
    begun = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix=".nostalgia-render-", dir=job.target.parent) as tmp:
            folder = Path(tmp)
            video = folder / "video.mp4"
            decoder = control.start(decoder_command(ffmpeg, job, media, requested),
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            encoder = control.start(encoder_command(ffmpeg, job, media, video),
                                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            decode_log, encode_log = PipeLog(decoder, control), PipeLog(encoder, control)
            control.emit("status", "Увеличение видео…")
            try:
                while count < requested:
                    control.check()
                    data = read_frame(decoder.stdout, media.width*media.height*4, control)
                    if data is None:
                        break
                    frame = np.frombuffer(data, dtype=np.uint8).reshape(media.height, media.width, 4)
                    output = engine.process(frame)
                    if output.shape != (media.height*job.scale, media.width*job.scale, 4) or output.dtype != np.uint8:
                        raise ProcessError("Движок вернул кадр неправильного размера или формата")
                    if job.grayscale:
                        rgb = output[..., :3].astype(np.float32)
                        luma = np.rint(rgb @ np.array([.2126, .7152, .0722], np.float32)).astype(np.uint8)
                        output = output.copy()
                        output[..., :3] = luma[..., None]
                    if not count:
                        control.emit("preview", preview_images(frame, output, job.work / "preview"))
                    try:
                        encoder.stdin.write(output.tobytes())
                    except (BrokenPipeError, OSError) as error:
                        control.check()
                        raise ProcessError("Ошибка кодирования:\n" + encode_log.text()) from error
                    count += 1
                    elapsed = time.monotonic()-begun
                    speed = count/max(.001, elapsed)
                    control.emit("progress", {"frame": count, "total": requested, "fps": speed,
                                               "eta": max(0, (requested-count)/speed)})
                    if count % 100 == 0 and shutil.disk_usage(folder).free < 64*1024**2:
                        raise ProcessError("Заканчивается место на диске; обработка остановлена")
                decoder.stdout.close()
                if control.finish(decoder, 60):
                    raise ProcessError("Ошибка декодирования:\n" + decode_log.text())
                encoder.stdin.close()
                if control.finish(encoder, 120):
                    raise ProcessError("Ошибка кодирования:\n" + encode_log.text())
                decode_log.text(); encode_log.text()
            finally:
                for process in (decoder, encoder):
                    if process and process.poll() is None:
                        process.kill(); process.wait()
                    if process:
                        control.forget(process)
                        for stream in (process.stdin, process.stdout, process.stderr):
                            if stream and not stream.closed:
                                stream.close()
            if not count:
                raise ProcessError("Не удалось прочитать ни одного кадра")
            control.check()
            control.emit("status", "Сохранение звука и MP4…")
            final = folder / "final.mp4"
            control.run(mux_command(ffmpeg, job, video, final, count/float(media.fps)))
            control.check()
            try:
                result = probe(final, ffprobe, control, json_path=job.work / "output-probe.json")
                control.emit("validation", {"expected_size": [media.width*job.scale, media.height*job.scale],
                    "actual_size": [result.width, result.height], "expected_fps": str(media.fps),
                    "actual_fps": str(result.fps), "expected_frames": count,
                    "actual_frames": result.reported_frames, "actual_duration": result.duration})
                rate_note = validate_result(media, result, job.scale, count)
                if rate_note:
                    control.emit("log", rate_note)
            except (ProcessError, ValueError) as error:
                recovery = job.target.with_name(job.target.stem+"_unverified_"+uuid.uuid4().hex[:8]+".mp4")
                publish_new(final, recovery)
                control.emit("log", "Unverified completed output preserved: "+str(recovery))
                raise ProcessError(str(error)+"\n\nГотовый MP4 сохранён для проверки (пока не подтверждён):\n"
                                   +str(recovery)+"\n\nПодробности: "+str(job.work / "session.log")) from error
            publish_new(final, job.target)
            report = {"backend": "NVIDIA RTX Video SDK 1.1 / NGX VSR / D3D11", "scale": job.scale,
                      "quality": job.quality, "frames": count, "fps": str(media.fps),
                      "output_fps": str(result.fps), "fps_note": rate_note,
                      "encoder": job.encoder, "cq": job.cq, "audio": job.audio,
                      "elapsed": time.monotonic()-begun, "source": str(job.source), "output": str(job.target)}
            # Reports are session files, not user output sidecars that might overwrite other files.
            (job.work / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            control.emit("done", str(job.target))
            return job.target
    finally:
        # Also covers failure while starting the second process or its log reader.
        for process in (decoder, encoder):
            if process:
                if process.poll() is None:
                    process.kill()
                    process.wait()
                control.forget(process)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream and not stream.closed:
                        stream.close()
        engine.close()
