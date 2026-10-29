import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch, Mock
import numpy as np
from PIL import Image
from nostalgia import pipeline as p
from nostalgia.media import parse_probe, probe
from nostalgia.runtime import Cancelled, Control


class FakeBackend:
    """Test double for frame transport only; never used by the production UI."""
    closed = False
    def __init__(self, width, height, scale, *args):
        self.scale = scale
    def process(self, bgra):
        rgba = bgra[..., [2, 1, 0, 3]]
        return np.repeat(np.repeat(rgba, self.scale, axis=0), self.scale, axis=1)
    def close(self):
        type(self).closed = True


def cpu_encoder(ffmpeg, job, media, target):
    command = ORIGINAL_ENCODER(ffmpeg, job, media, target)
    for option in ("-gpu", "-tune", "-rc", "-cq", "-b:v"):
        idx = command.index(option); del command[idx:idx+2]
    command[command.index(job.encoder)] = "libx264"
    command[command.index("p6")] = "ultrafast"
    command[-1:-1] = ["-threads", "1"]
    return command

ORIGINAL_ENCODER = p.encoder_command


class PipelineTests(unittest.TestCase):
    def test_small_muxer_rate_rounding_requires_verified_frame_count_and_duration(self):
        from nostalgia.media import Media
        from nostalgia.runtime import ProcessError
        from fractions import Fraction
        from dataclasses import replace
        source = Media(1920, 1080, Fraction(30000, 1001), 3.003, False, 90, "h264")
        result = Media(3840, 2160, Fraction(2997, 100), 3.003003, False, 90, "h264", reported_frames=90)
        self.assertIsNotNone(p.validate_result(source, result, 2, 90))
        for changed in (replace(result, reported_frames=None), replace(result, duration=3.1),
                        replace(result, fps=Fraction(30))):
            with self.assertRaises(ProcessError): p.validate_result(source, changed, 2, 90)

    def test_validation_reports_actual_dimensions_and_detects_dropped_frames(self):
        from nostalgia.media import Media
        from nostalgia.runtime import ProcessError
        from fractions import Fraction
        from dataclasses import replace
        source = Media(1920, 1080, Fraction(24), 1, False, 24, "h264")
        result = Media(3840, 2160, Fraction(24), 1, False, 24, "h264", reported_frames=24)
        self.assertIsNone(p.validate_result(source, result, 2, 24))
        with self.assertRaisesRegex(ProcessError, "Получено: 1920 × 2160"):
            p.validate_result(source, replace(result, width=1920), 2, 24)
        with self.assertRaisesRegex(ProcessError, "Число кадров"):
            p.validate_result(source, replace(result, reported_frames=23), 2, 24)

    def test_nvenc_checks_the_actual_requested_dimensions_and_quality(self):
        control = Control()
        control.run = Mock()
        job = p.Job(Path("source.mp4"), Path("target.mp4"), Path("."), Path("."), scale=4, cq=16)
        p.nvenc_check(Path("ffmpeg"), job, control, 7680, 4320)
        command = control.run.call_args.args[0]
        self.assertIn("color=black:size=7680x4320:rate=1", command)
        self.assertEqual(command[command.index("-cq")+1], "16")

    def test_unsupported_8k_h264_stops_before_loading_vsr(self):
        from nostalgia.media import Media
        from nostalgia.runtime import ProcessError
        from fractions import Fraction
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root/"source.mp4"; source.touch()
            job = p.Job(source, root/"output.mp4", root, root/"work", scale=4)
            control = Control()
            control.run = Mock(side_effect=ProcessError("[h264_nvenc] Width 7680 exceeds 4096\nNo capable devices found"))
            factory = Mock()
            with patch.object(p, "probe", return_value=Media(1920, 1080, Fraction(30), 1, False, 30, "h264")):
                with self.assertRaisesRegex(ProcessError, "Лимит ширины.*4096"):
                    p.convert(job, control, backend_factory=factory, tools=(Path("ffmpeg"), Path("ffprobe")))
            factory.assert_not_called()
            self.assertFalse(job.target.exists())

    def test_truncated_frame_is_an_error(self):
        with self.assertRaisesRegex(RuntimeError, "Неполный"):
            p.read_frame(io.BytesIO(b"abcd"), 5, Control())
        self.assertIsNone(p.read_frame(io.BytesIO(), 5, Control()))

    def test_hdr_and_anamorphic_input_are_rejected(self):
        base = {"codec_type": "video", "width": 64, "height": 48,
                "avg_frame_rate": "24000/1001", "duration": "1"}
        for addition in ({"color_transfer": "smpte2084"}, {"sample_aspect_ratio": "4:3"}, {"field_order": "tt"}):
            with self.assertRaises(ValueError):
                parse_probe({"streams": [{**base, **addition}]})

    def test_rotation_and_attached_picture_stream_selection(self):
        m = parse_probe({"streams": [
            {"codec_type": "video", "disposition": {"attached_pic": 1}},
            {"index": 2, "codec_type": "video", "width": 64, "height": 48,
             "avg_frame_rate": "24000/1001", "duration": "1", "side_data_list": [{"rotation": -90}]}]})
        self.assertEqual((m.width, m.height, m.stream_index), (48, 64, 2))
        self.assertEqual(str(m.fps), "24000/1001")

    def test_publish_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/"a", Path(tmp)/"b"
            a.write_bytes(b"new"); b.write_bytes(b"existing")
            with self.assertRaises(FileExistsError): p.publish_new(a, b)
            self.assertEqual(b.read_bytes(), b"existing")

    def test_preview_colour_order(self):
        before = np.full((2, 2, 4), [1, 2, 200, 255], np.uint8)
        after = np.full((4, 4, 4), [200, 2, 1, 255], np.uint8)
        with tempfile.TemporaryDirectory() as tmp:
            a, b = p.preview_images(before, after, Path(tmp))
            self.assertEqual(Image.open(a).getpixel((0, 0)), (200, 2, 1))
            self.assertEqual(Image.open(b).getpixel((0, 0)), (200, 2, 1))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
    def test_full_pipeline_audio_fractional_fps_colour_and_no_frame_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/"Исходник [1].mp4"
            target = root/"Результат.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                "color=c=red:size=64x48:rate=24000/1001", "-f", "lavfi", "-i", "sine=frequency=440",
                "-t", "1.5", "-c:v", "libx264", "-threads", "1", "-c:a", "aac", str(source)], check=True)
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            events = []
            job = p.Job(source, target, root, root/"session", start=.2, seconds=.5, audio="copy")
            FakeBackend.closed = False
            with patch.object(p, "encoder_command", cpu_encoder):
                result = p.convert(job, Control(lambda k, v: events.append((k, v))), backend_factory=FakeBackend,
                                   tools=(Path(shutil.which("ffmpeg")), Path(shutil.which("ffprobe"))), check_encoder=False)
            self.assertEqual(result, target)
            self.assertTrue(FakeBackend.closed)
            m = probe(target, Path(shutil.which("ffprobe")), Control())
            self.assertEqual((m.width, m.height), (128, 96)); self.assertTrue(m.audio)
            self.assertEqual(str(m.fps), "24000/1001")
            self.assertAlmostEqual(m.duration, 12*1001/24000, delta=.05)
            report = json.loads((root/"session/result.json").read_text())
            self.assertEqual(report["frames"], 12)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original)
            self.assertFalse(list(root.glob(".nostalgia-render-*")))
            # A validation failure must retain a completed playable video for diagnosis.
            verify_job = p.Job(source, root/"verify.mp4", root, root/"verify-session", seconds=.5)
            with patch.object(p, "encoder_command", cpu_encoder), patch.object(p, "validate_result", side_effect=p.ProcessError("diagnostic failure")):
                with self.assertRaisesRegex(p.ProcessError, "Готовый MP4 сохранён"):
                    p.convert(verify_job, Control(), backend_factory=FakeBackend,
                              tools=(Path(shutil.which("ffmpeg")), Path(shutil.which("ffprobe"))), check_encoder=False)
            self.assertFalse(verify_job.target.exists())
            recovered = list(root.glob("verify_unverified_*.mp4"))
            self.assertEqual(len(recovered), 1)
            self.assertTrue(probe(recovered[0], Path(shutil.which("ffprobe")), Control()).audio)
            self.assertTrue((verify_job.work/"input-probe.json").is_file())
            self.assertTrue((verify_job.work/"output-probe.json").is_file())
            self.assertFalse(list(root.glob(".nostalgia-render-*")))
            self.assertEqual(len(list(job.work.rglob("*.png"))), 2)
            self.assertEqual(len(list(verify_job.work.rglob("*.png"))), 2)
            raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(target), "-frames:v", "1",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"])
            pixels = np.frombuffer(raw, np.uint8).reshape(96, 128, 3)
            self.assertGreater(float(pixels[..., 0].mean()), 220)
            self.assertLess(float(pixels[..., 2].mean()), 20)
            self.assertEqual(events[-1], ("done", str(target)))
            # Cancellation after one frame cleans up children and the partial MP4.
            cancel_job = p.Job(source, root/"cancel.mp4", root, root/"cancel-session", seconds=1)
            control = Control()
            def cancel_emit(kind, value):
                if kind == "progress": control.cancel()
            control.emit = cancel_emit
            with patch.object(p, "encoder_command", cpu_encoder), self.assertRaises(Cancelled):
                p.convert(cancel_job, control, backend_factory=FakeBackend,
                          tools=(Path(shutil.which("ffmpeg")), Path(shutil.which("ffprobe"))), check_encoder=False)
            self.assertFalse(cancel_job.target.exists())
            self.assertFalse(control._processes)
            self.assertFalse(list(root.glob(".nostalgia-render-*")))

    def test_backend_errors_are_not_converted_to_success(self):
        from nostalgia.backend import RTXVideo
        if os.name != "nt":
            with self.assertRaisesRegex(RuntimeError, "Windows"):
                RTXVideo(64, 48, 2, 3, 0, Path("."), Path("."))

if __name__ == "__main__": unittest.main()
