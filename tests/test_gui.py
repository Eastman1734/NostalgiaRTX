import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path
import tempfile
import unittest
from PySide6.QtWidgets import QApplication
from nostalgia.gui import Window, STYLE


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle("Fusion"); cls.app.setStyleSheet(STYLE)

    def test_settings_progress_preview_and_button_state(self):
        from PIL import Image
        w = Window(); w.show(); self.app.processEvents()
        self.assertFalse(w.render.isEnabled())
        w.source.setText("D:/Видео/фильм.mp4"); w.update_target(); w.refresh_buttons()
        self.assertTrue(w.render.isEnabled()); self.assertTrue(w.test.isEnabled())
        self.assertEqual(w.quality.currentIndex(), 2)
        self.assertFalse(w.gray.isChecked())
        with tempfile.TemporaryDirectory() as tmp:
            payload = w.payload("preview", Path(tmp))
            self.assertEqual(payload["scale"], 2); self.assertEqual(payload["seconds"], 3)
            self.assertIn("preview_", payload["target"])
            w.event_received("inspected", {"width": 1920, "height": 1080, "fps": "24000/1001", "duration": 60, "audio": True})
            self.assertIn("3840", w.size_info.text())
            w.scale.setCurrentIndex(1)
            self.assertIn("7680", w.size_info.text())
            self.assertEqual(w.codec.currentIndex(), 1)
            self.assertEqual(w.payload("preview", Path(tmp))["encoder"], "hevc_nvenc")
            w.scale.setCurrentIndex(0)
            w.event_received("progress", {"frame": 50, "total": 100, "fps": 24, "eta": 2})
            self.assertEqual(w.progress.value(), 495)
            a, b = Path(tmp)/"a.png", Path(tmp)/"b.png"
            Image.new("RGB", (640, 360), "red").save(a); Image.new("RGB", (640, 360), "blue").save(b)
            w.event_received("preview", [str(a), str(b)])
            self.assertFalse(w.comparison.before.isNull())
            w.slider.setValue(75); self.assertEqual(w.comparison.position, .75)
            w.event_received("done", str(Path(tmp)/"done.mp4"))
            self.assertTrue(w.open_output.isEnabled()); self.assertEqual(w.progress.value(), 1000)
        self.app.processEvents()
        w.close()

if __name__ == "__main__": unittest.main()
