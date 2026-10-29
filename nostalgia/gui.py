from __future__ import annotations
import json
import os
import sys
import time
import uuid
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSlider, QSpinBox, QSplitter,
    QVBoxLayout, QWidget, QScrollArea)
from .runtime import data_dir

ROOT = Path(__file__).resolve().parents[1]
STYLE = """
QWidget { background: #11151c; color: #e9eef5; font-family: 'Segoe UI'; font-size: 13px; }
QLabel#title { font-size: 29px; font-weight: 700; }
QLabel#muted { color: #94a0b1; }
QLabel#section { color: #a9b6c9; font-weight: 600; font-size: 11px; }
QLabel#badge { background: #203128; color: #b7f397; padding: 6px 10px; border-radius: 6px; font-weight: 600; }
QFrame#card { background: #191f29; border: 1px solid #2b3443; border-radius: 12px; }
QFrame#card QLabel, QFrame#card QCheckBox { background: transparent; }
QPushButton { background: #283241; border: 1px solid #3a475b; border-radius: 7px; padding: 10px 15px; font-weight: 600; }
QPushButton:hover { background: #344258; }
QPushButton:disabled { color: #667180; border-color: #2b3340; background: #202731; }
QPushButton#primary { background: #b3ee82; color: #14220a; border: 0; }
QPushButton#primary:hover { background: #c7ffa0; }
QPushButton#primary:disabled { background: #35452b; color: #829477; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #101720; border: 1px solid #364358; border-radius: 6px; padding: 5px 8px; min-height: 20px; selection-background-color: #436536; }
QLineEdit:focus, QComboBox:focus { border-color: #a7d97f; }
QComboBox QAbstractItemView { background: #202a38; selection-background-color: #3d5143; }
QProgressBar { border: none; background: #2a3441; border-radius: 4px; min-height: 8px; max-height: 8px; }
QProgressBar::chunk { background: #afe482; border-radius: 4px; }
QSlider::groove:horizontal { background: #354052; height: 4px; border-radius: 2px; }
QSlider::handle:horizontal { background: #b3ee82; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
QPlainTextEdit { background: #0e131a; border: 1px solid #2c3747; border-radius: 7px; font-family: Consolas; font-size: 11px; padding: 8px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 15px; height: 15px; background: #111823; border: 1px solid #607189; border-radius: 3px; }
QCheckBox::indicator:checked { background: #a5d87a; border-color: #a5d87a; }
QSplitter::handle { background: transparent; width: 16px; }
"""


def label(text, kind=""):
    widget = QLabel(text)
    if kind:
        widget.setObjectName(kind)
    return widget


def duration_text(seconds):
    seconds = max(0, round(seconds))
    return f"{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}"


class Comparison(QWidget):
    def __init__(self):
        super().__init__()
        self.before = QPixmap()
        self.after = QPixmap()
        self.position = .5
        self.setMinimumSize(400, 280)

    def clear(self):
        self.before = QPixmap(); self.after = QPixmap(); self.update()

    def load(self, before, after):
        self.before = QPixmap(str(before)); self.after = QPixmap(str(after)); self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#0c1016"))
        if self.before.isNull() or self.after.isNull():
            p.setPen(QColor("#526177"))
            p.setFont(QFont("Segoe UI", 38))
            p.drawText(self.rect().adjusted(0, -30, 0, -30), Qt.AlignmentFlag.AlignCenter, "↗")
            p.setFont(QFont("Segoe UI", 12))
            p.setPen(QColor("#acb8c8"))
            p.drawText(self.rect().adjusted(0, 65, 0, 65), Qt.AlignmentFlag.AlignCenter, "Здесь появится сравнение кадра")
            return
        scaled = self.after.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x, y = (self.width()-scaled.width())//2, (self.height()-scaled.height())//2
        from PySide6.QtCore import QRect
        target = QRect(x, y, scaled.width(), scaled.height())
        p.drawPixmap(target, self.after)
        divider = x + int(scaled.width()*self.position)
        p.save(); p.setClipRect(x, y, divider-x, scaled.height())
        p.drawPixmap(target, self.before); p.restore()
        p.setPen(QPen(QColor("#c3f599"), 2)); p.drawLine(divider, y, divider, y+scaled.height())
        for caption, px in (("ОРИГИНАЛ", x+14), ("RTX VSR", max(x+14, x+scaled.width()-89))):
            p.fillRect(px-5, y+10, 84, 24, QColor(14, 20, 28, 210))
            p.setPen(QColor("#edf3f9")); p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            p.drawText(px, y+27, caption)


class Window(QMainWindow):
    def __init__(self, root: Path = ROOT):
        super().__init__()
        self.root = root
        self.setWindowTitle("Nostalgia RTX 0.2.2 · Увеличение видео")
        self.resize(1230, 900); self.setMinimumSize(1000, 720)
        self.process: QProcess | None = None
        self.operation = ""
        self.buffer = b""
        self.job_folder: Path | None = None
        self.last_output: Path | None = None
        self.saw_terminal_event = False
        self.source_meta = None
        main = QWidget(); self.setCentralWidget(main)
        layout = QVBoxLayout(main); layout.setContentsMargins(26, 22, 26, 22); layout.setSpacing(18)
        header = QHBoxLayout()
        names = QVBoxLayout(); names.addWidget(label("Nostalgia RTX", "title"))
        names.addWidget(label("Больше деталей. Тот же фильм.", "muted")); header.addLayout(names)
        header.addStretch(); badge = label("NVIDIA RTX VIDEO", "badge"); badge.setMaximumHeight(34); header.addWidget(badge)
        layout.addLayout(header)
        split = QSplitter(Qt.Orientation.Horizontal)
        left = QFrame(); left.setObjectName("card"); left.setMinimumWidth(330); left.setMaximumWidth(390)
        settings = QVBoxLayout(left); settings.setContentsMargins(18, 18, 18, 18); settings.setSpacing(9)
        settings.addWidget(label("01  ИСХОДНОЕ ВИДЕО", "section"))
        self.choose = QPushButton("+  Выбрать видео")
        self.choose.clicked.connect(self.select_source); settings.addWidget(self.choose)
        self.source = QLineEdit(); self.source.setReadOnly(True); self.source.setPlaceholderText("MP4, MKV, MOV, AVI…")
        settings.addWidget(self.source)
        self.info = label("Выберите progressive SDR-видео", "muted"); self.info.setWordWrap(True); settings.addWidget(self.info)
        settings.addSpacing(9); settings.addWidget(label("02  УВЕЛИЧЕНИЕ", "section"))
        grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(9)
        self.scale = QComboBox(); self.scale.addItems(["×2", "×4"])
        self.quality = QComboBox(); self.quality.addItems(["1 · Скорость", "2 · Баланс", "3 · Качество", "4 · Максимум"]); self.quality.setCurrentIndex(2)
        self.scale.currentIndexChanged.connect(self.update_target)
        grid.addWidget(label("Масштаб"), 0, 0); grid.addWidget(self.scale, 0, 1)
        grid.addWidget(label("Качество VSR"), 1, 0); grid.addWidget(self.quality, 1, 1)
        self.gpu = QSpinBox(); self.gpu.setRange(0, 15); self.gpu.setPrefix("RTX #")
        self.gpu.setToolTip("Номер NVIDIA GPU, начиная с 0. Для одного GPU оставьте 0.")
        grid.addWidget(label("Видеокарта"), 2, 0); grid.addWidget(self.gpu, 2, 1)
        settings.addLayout(grid)
        self.gray = QCheckBox("Чёрно-белый результат"); settings.addWidget(self.gray)
        self.size_info = label("1080p → 4K при увеличении ×2", "muted"); self.size_info.setWordWrap(True); settings.addWidget(self.size_info)
        settings.addSpacing(9); settings.addWidget(label("03  ЭКСПОРТ", "section"))
        export = QGridLayout(); export.setSpacing(9)
        self.codec = QComboBox(); self.codec.addItems(["H.264 · Совместимость", "H.265 · Компактнее"])
        self.audio = QComboBox(); self.audio.addItems(["AAC · 192 кбит/с", "Копировать оригинал"])
        export.addWidget(label("Видео"), 0, 0); export.addWidget(self.codec, 0, 1)
        export.addWidget(label("Звук"), 1, 0); export.addWidget(self.audio, 1, 1)
        self.cq = QSpinBox(); self.cq.setRange(1, 51); self.cq.setValue(18)
        self.cq.setToolTip("Качество NVENC: меньшее число — больше размер файла и меньше потерь.")
        export.addWidget(label("CQ"), 2, 0); export.addWidget(self.cq, 2, 1)
        settings.addLayout(export)
        self.target = QLineEdit(); self.target.setPlaceholderText("Новый файл .mp4")
        settings.addWidget(self.target)
        self.browse_target = QPushButton("Папка и имя результата…"); self.browse_target.clicked.connect(self.select_target); settings.addWidget(self.browse_target)
        settings.addStretch()
        self.doctor = QPushButton("Проверить RTX и NVENC"); self.doctor.clicked.connect(lambda: self.start_operation("doctor")); settings.addWidget(self.doctor)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(left); scroll.setMinimumWidth(350); scroll.setMaximumWidth(410)
        split.addWidget(scroll)
        right = QFrame(); right.setObjectName("card")
        previews = QVBoxLayout(right); previews.setContentsMargins(18, 18, 18, 18); previews.setSpacing(12)
        top = QHBoxLayout(); top.addWidget(label("СРАВНЕНИЕ ПЕРВОГО КАДРА ФРАГМЕНТА", "section")); top.addStretch(); previews.addLayout(top)
        self.comparison = Comparison(); previews.addWidget(self.comparison, 1)
        self.slider = QSlider(Qt.Orientation.Horizontal); self.slider.setRange(0, 100); self.slider.setValue(50)
        self.slider.valueChanged.connect(lambda value: self.set_comparison(value)); previews.addWidget(self.slider)
        hint = label("Слева — оригинал, увеличенный для сравнения. Справа — результат RTX VSR.", "muted")
        hint.setWordWrap(True); previews.addWidget(hint)
        times = QHBoxLayout()
        times.addWidget(label("Начало, сек")); self.start = QDoubleSpinBox(); self.start.setRange(0, 999999); self.start.setDecimals(1); times.addWidget(self.start)
        times.addSpacing(10); times.addWidget(label("Проба, сек")); self.seconds = QDoubleSpinBox(); self.seconds.setRange(.1, 60); self.seconds.setValue(3); self.seconds.setDecimals(1); times.addWidget(self.seconds); times.addStretch()
        previews.addLayout(times)
        note = label("Проба сохраняет короткий MP4 со звуком. Полный рендер идёт от выбранного начала до конца видео.", "muted"); note.setWordWrap(True); previews.addWidget(note)
        log_header = QHBoxLayout(); log_header.addWidget(label("ЖУРНАЛ", "section")); log_header.addStretch()
        self.log_folder = QPushButton("Открыть папку журнала")
        self.log_folder.setEnabled(False)
        self.log_folder.clicked.connect(self.open_session)
        log_header.addWidget(self.log_folder); previews.addLayout(log_header)
        self.logs = QPlainTextEdit(); self.logs.setReadOnly(True); self.logs.setMaximumBlockCount(300); self.logs.setFixedHeight(100); self.logs.setPlaceholderText("Журнал обработки")
        previews.addWidget(self.logs)
        split.addWidget(right); split.setSizes([350, 760]); layout.addWidget(split, 1)
        bottom = QHBoxLayout(); status_box = QVBoxLayout()
        self.status = label("Готово к работе"); self.stats = label("Локальная обработка · исходный файл сохраняется", "muted")
        status_box.addWidget(self.status); status_box.addWidget(self.stats); bottom.addLayout(status_box, 1)
        self.open_output = QPushButton("Открыть результат"); self.open_output.setEnabled(False); self.open_output.clicked.connect(self.open_result); bottom.addWidget(self.open_output)
        self.cancel = QPushButton("Отменить"); self.cancel.setEnabled(False); self.cancel.clicked.connect(self.cancel_job); bottom.addWidget(self.cancel)
        self.test = QPushButton("Пробный фрагмент"); self.test.clicked.connect(lambda: self.start_operation("preview")); bottom.addWidget(self.test)
        self.render = QPushButton("Увеличить видео  ↗"); self.render.setObjectName("primary"); self.render.clicked.connect(lambda: self.start_operation("render")); bottom.addWidget(self.render)
        layout.addLayout(bottom)
        self.progress = QProgressBar(); self.progress.setTextVisible(False); self.progress.setRange(0, 1000); self.progress.setValue(0); layout.addWidget(self.progress)
        self.setAcceptDrops(True)
        self.refresh_buttons()

    def set_comparison(self, value):
        self.comparison.position = value/100; self.comparison.update()

    def refresh_buttons(self):
        busy = self.process is not None
        for widget in (self.choose, self.browse_target, self.scale, self.quality, self.gpu,
                       self.gray, self.codec, self.audio, self.cq, self.start, self.seconds, self.target, self.doctor):
            widget.setEnabled(not busy)
        self.render.setEnabled(not busy and bool(self.source.text()))
        self.test.setEnabled(not busy and bool(self.source.text()))
        self.cancel.setEnabled(busy)

    def select_source(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите видео", "", "Видео (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.ts);;Все файлы (*)")
        if filename:
            self.load_source(Path(filename))

    def load_source(self, path):
        if self.process:
            return
        self.source.setText(str(path)); self.source.setToolTip(str(path)); self.comparison.clear()
        self.source_meta = None; self.start.setValue(0); self.update_target()
        self.start_operation("probe")

    def update_target(self):
        if self.source.text():
            source = Path(self.source.text())
            scale = 2 if self.scale.currentIndex() == 0 else 4
            self.target.setText(str(source.with_name(source.stem+f"_rtx_x{scale}.mp4")))
        self.update_size()

    def update_size(self):
        if self.source_meta:
            m = self.source_meta; scale = 2 if self.scale.currentIndex() == 0 else 4
            self.size_info.setText(f"{m['width']} × {m['height']} → {m['width']*scale} × {m['height']*scale}")
            if max(m['width']*scale, m['height']*scale) > 4096 and self.codec.currentIndex() == 0:
                self.codec.setCurrentIndex(1)
                self.size_info.setText(self.size_info.text()+"\nДля большого разрешения выбран H.265")

    def select_target(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Новый файл результата", self.target.text(), "MP4 (*.mp4)")
        if filename:
            self.target.setText(filename)

    def payload(self, operation, folder):
        source = Path(self.source.text())
        target = Path(self.target.text()) if self.target.text() else self.root / "unused.mp4"
        if operation == "preview":
            target = target.with_name(target.stem+"_preview_"+uuid.uuid4().hex[:6]+".mp4")
        return {"source": str(source), "target": str(target), "root": str(self.root), "work": str(folder),
                "scale": 2 if self.scale.currentIndex() == 0 else 4, "quality": self.quality.currentIndex()+1,
                "gpu": self.gpu.value(), "encoder": "h264_nvenc" if self.codec.currentIndex() == 0 else "hevc_nvenc",
                "cq": self.cq.value(), "audio": "aac" if self.audio.currentIndex() == 0 else "copy",
                "start": self.start.value(), "seconds": self.seconds.value() if operation == "preview" else 0,
                "grayscale": self.gray.isChecked(), "operation": operation}

    def start_operation(self, operation):
        if self.process:
            return
        if operation in {"render", "preview"}:
            from .pipeline import Job
            payload = self.payload(operation, data_dir())
            try:
                Job(**{k: Path(v) if k in {"source", "target", "root", "work"} else v
                       for k, v in payload.items() if k != "operation"}).validate()
            except Exception as error:
                QMessageBox.warning(self, "Проверьте настройки", str(error)); return
        folder = data_dir() / "sessions" / (time.strftime("%Y%m%d-%H%M%S")+"-"+uuid.uuid4().hex[:6])
        folder.mkdir(parents=True)
        request = folder / "request.json"
        request.write_text(json.dumps(self.payload(operation, folder), ensure_ascii=False), encoding="utf-8")
        self.job_folder = folder; self.operation = operation; self.saw_terminal_event = False; self.buffer = b""
        self.log_folder.setEnabled(True)
        self.logs.clear(); self.status.setText("Подготовка…"); self.progress.setRange(0, 0)
        process = QProcess(self); self.process = process
        process.setWorkingDirectory(str(self.root))
        process.readyReadStandardOutput.connect(self.read_stdout)
        process.readyReadStandardError.connect(self.read_stderr)
        process.finished.connect(self.finished)
        process.errorOccurred.connect(self.process_error)
        python = Path(sys.executable)
        if python.name.lower() == "pythonw.exe":
            python = python.with_name("python.exe")
        process.start(str(python), ["-u", "-m", "nostalgia.worker", str(request)])
        self.refresh_buttons()

    def read_stdout(self):
        if self.process:
            self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                event = json.loads(line)
                if isinstance(event, dict) and "event" in event:
                    self.event_received(event["event"], event.get("data"))
            except (ValueError, TypeError):
                self.logs.appendPlainText(line.decode("utf-8", "replace"))

    def read_stderr(self):
        if self.process:
            text = bytes(self.process.readAllStandardError()).decode("utf-8", "replace")
            if text.strip(): self.logs.appendPlainText(text.strip())

    def event_received(self, kind, data):
        if kind == "status":
            self.status.setText(data)
        elif kind == "inspected":
            self.saw_terminal_event = True; self.source_meta = data
            self.info.setText(f"{data['width']} × {data['height']}  ·  {data['fps']} FPS\n{duration_text(data['duration'])}  ·  {'со звуком' if data['audio'] else 'без звука'}")
            self.update_size(); self.status.setText("Видео готово. Начните с пробного фрагмента.")
        elif kind == "media":
            self.progress.setRange(0, 1000)
        elif kind == "progress":
            self.progress.setRange(0, 1000); self.progress.setValue(min(990, int(data["frame"]/data["total"]*990)))
            self.stats.setText(f"{data['frame']} / ~{data['total']} кадров  ·  {data['fps']:.2f} кадр/с  ·  осталось ~{duration_text(data['eta'])}")
        elif kind == "preview":
            self.comparison.load(*data)
        elif kind in {"done", "doctor", "cancelled", "error"}:
            self.saw_terminal_event = True
            if kind == "done":
                self.last_output = Path(data); self.open_output.setEnabled(True)
                self.status.setText("Готово · результат проверен"); self.stats.setText(data)
                self.progress.setRange(0, 1000); self.progress.setValue(1000)
            elif kind == "error":
                self.status.setText("Обработка остановлена с ошибкой")
                self.logs.appendPlainText(data)
                self.stats.setText("Журнал: "+str(self.job_folder / "session.log"))
                QMessageBox.warning(self, "Ошибка обработки", data)
            else:
                self.status.setText(data)
                self.progress.setRange(0, 1000); self.progress.setValue(0)

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.saw_terminal_event = True; self.status.setText("Не удалось запустить обработчик")
            self.logs.appendPlainText(self.process.errorString())
            self.process.deleteLater(); self.process = None; self.refresh_buttons()

    def finished(self, code, status):
        self.read_stdout(); self.read_stderr()
        if not self.saw_terminal_event:
            self.status.setText(f"Обработчик завершился неожиданно (код {code})")
            self.stats.setText("Проверьте журнал и драйвер NVIDIA")
        if self.progress.maximum() == 0:
            self.progress.setRange(0, 1000); self.progress.setValue(0)
        if self.process:
            self.process.deleteLater()
        self.process = None; self.refresh_buttons()

    def cancel_job(self):
        if self.job_folder and self.process:
            (self.job_folder / "cancel").touch()
            self.cancel.setEnabled(False); self.status.setText("Отмена · ожидаю завершения текущего кадра…")
            process = self.process
            def force_stop():
                if self.process is process and process.state() != QProcess.ProcessState.NotRunning:
                    self.status.setText("Принудительная остановка обработчика…")
                    if os.name == "nt":
                        QProcess.startDetached("taskkill.exe", ["/PID", str(process.processId()), "/T", "/F"])
                    else:
                        process.kill()
            QTimer.singleShot(8000, force_stop)

    def open_result(self):
        if self.last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.last_output)))

    def open_session(self):
        if self.job_folder:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.job_folder)))

    def dragEnterEvent(self, event):
        if not self.process and event.mimeData().hasUrls(): event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile(): self.load_source(Path(urls[0].toLocalFile()))

    def closeEvent(self, event):
        if self.process:
            self.cancel_job(); self.status.setText("Сначала дождитесь отмены обработки, затем закройте окно.")
            event.ignore()
        else:
            event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion"); app.setStyleSheet(STYLE)
    app.setApplicationName("Nostalgia RTX")
    window = Window(); window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
