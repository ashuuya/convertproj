"""
download_tab.py — Вкладка скачивания с качеством 360p по умолчанию и drag & drop .txt.
"""

import os
import re
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QRadioButton, QButtonGroup,
    QProgressBar, QFrame, QMessageBox, QFileDialog, QSlider,
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from gui.worker import DownloadWorker
from gui.translations import tr

# Регулярка для поиска YouTube-ссылок в тексте
_YOUTUBE_RE = re.compile(
    r'https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be)/\S+'
)


class _DropTextEdit(QTextEdit):
    """QTextEdit, который принимает только файловые дропы .txt/.m3u/.m3u8."""

    file_dropped = pyqtSignal(str)  # путь к сброшенному файлу

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if _has_txt_url(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if _has_txt_url(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and path.lower().endswith(('.txt', '.m3u', '.m3u8')):
                self.file_dropped.emit(path)
                event.acceptProposedAction()
                return
        event.ignore()


def _has_txt_url(mime):
    """Проверить, есть ли среди URL файл .txt/.m3u/.m3u8."""
    if not mime.hasUrls():
        return False
    for url in mime.urls():
        path = url.toLocalFile()
        if path and path.lower().endswith(('.txt', '.m3u', '.m3u8')):
            return True
    return False


class DownloadTab(QWidget):
    """Вкладка скачивания YouTube + drag & drop текстовых файлов."""

    downloads_finished = pyqtSignal(object)

    def __init__(self, app_dir: Path, bin_dir: Path, config: dict):
        super().__init__()
        self._app_dir = app_dir
        self._bin_dir = bin_dir
        self._config = config
        self._out = app_dir / "Downloads" / "Recode"
        self._worker = None
        self._thread = None
        self._setup_ui()
        self._apply_config()

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        lo = self.layout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(12)

        # ── Карточка ссылок ──
        card = QFrame(); card.setObjectName("glassCard")
        cl = QVBoxLayout(card); cl.setSpacing(6)
        self._lbl_links = QLabel("🔗 Ссылки YouTube", objectName="subtitleLabel")
        cl.addWidget(self._lbl_links)

        self._links = _DropTextEdit()
        self._links.setPlaceholderText(
            "Каждая ссылка с новой строки…\nhttps://youtube.com/watch?v=..."
        )
        self._links.setMinimumHeight(100)
        self._links.setToolTip(
            "Вставьте ссылки или перетащите .txt / .m3u файл"
        )
        self._links.file_dropped.connect(self._on_file_dropped)
        cl.addWidget(self._links)

        hb = QHBoxLayout()
        self._load_btn = QPushButton("📂 Загрузить из links.txt")
        self._load_btn.clicked.connect(self._load_links)
        hb.addWidget(self._load_btn)
        hb.addStretch()
        cl.addLayout(hb)
        lo.addWidget(card)

        # ── Карточка качества — 360p по умолчанию ──
        qc = QFrame(); qc.setObjectName("glassCard")
        qcl = QVBoxLayout(qc); qcl.setSpacing(6)
        self._lbl_quality = QLabel("📊 Качество", objectName="subtitleLabel")
        qcl.addWidget(self._lbl_quality)

        self._qg = QButtonGroup(self)
        hr = QHBoxLayout(); hr.setSpacing(14)
        self._rb_360 = QRadioButton("360p")
        self._rb_720 = QRadioButton("720p")
        self._rb_1080 = QRadioButton("1080p")
        self._rb_max = QRadioButton("Макс.")
        for rb in (self._rb_360, self._rb_720, self._rb_1080, self._rb_max):
            self._qg.addButton(rb); hr.addWidget(rb)
        self._rb_360.setChecked(True)  # ← 360p по умолчанию
        hr.addStretch()
        qcl.addLayout(hr)

        # ── Строка: число потоков загрузки (слайдер) ──
        thr_row = QHBoxLayout(); thr_row.setSpacing(8)
        cpu_cores = self._config.get("cpu_cores", os.cpu_count() or 4)
        recommended = max(1, cpu_cores // 2)
        saved_threads = self._config.get("download_threads", recommended)
        self._lbl_threads = QLabel("Потоков загрузки:")
        self._threads_slider = QSlider(Qt.Orientation.Horizontal)
        self._threads_slider.setRange(1, max(1, (os.cpu_count() or 4) * 2))
        self._threads_slider.setValue(saved_threads)
        self._threads_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._threads_slider.setTickInterval(1)
        self._threads_slider.valueChanged.connect(self._on_threads_changed)
        self._lbl_threads_val = QLabel(str(saved_threads))
        self._lbl_threads_val.setFixedWidth(24)
        self._lbl_threads_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_threads_hint = QLabel(f"(реком. {recommended})")
        thr_row.addWidget(self._lbl_threads)
        thr_row.addWidget(self._threads_slider, 1)
        thr_row.addWidget(self._lbl_threads_val)
        thr_row.addWidget(self._lbl_threads_hint)
        qcl.addLayout(thr_row)
        lo.addWidget(qc)

        # ── Кнопка скачивания ──
        bc = QFrame(); bc.setObjectName("glassCard")
        bl = QHBoxLayout(bc); bl.setSpacing(10)
        self._dl_btn = QPushButton("▶ Скачать")
        self._dl_btn.setObjectName("primaryBtn")
        self._dl_btn.clicked.connect(self._start)
        bl.addWidget(self._dl_btn)

        self._folder_btn = QPushButton("📂 Папка загрузок")
        self._folder_btn.clicked.connect(self._open_downloads)
        bl.addWidget(self._folder_btn)
        bl.addStretch()
        lo.addWidget(bc)

        # ── Карточка прогресса ──
        pc = QFrame(); pc.setObjectName("glassCard")
        pcl = QVBoxLayout(pc); pcl.setSpacing(5)
        self._status = QLabel("Готов", objectName="subtitleLabel")
        pcl.addWidget(self._status)

        self._bar = QProgressBar(); self._bar.setValue(0)
        pcl.addWidget(self._bar)

        self._log = QTextEdit(); self._log.setObjectName("logArea")
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(120)
        pcl.addWidget(self._log)
        lo.addWidget(pc)
        lo.addStretch()

    def _open_downloads(self):
        """Открыть папку загрузок, создав её при необходимости."""
        self._out.mkdir(parents=True, exist_ok=True)
        os.startfile(str(self._out))

    def showEvent(self, event):
        """При каждом показе вкладки пересчитываем рекомендуемое значение."""
        super().showEvent(event)
        cpu_cores = self._config.get("cpu_cores", os.cpu_count() or 4)
        recommended = max(1, cpu_cores // 2)
        self._lbl_threads_hint.setText(f"(реком. {recommended})")
        self._threads_slider.setRange(1, max(1, cpu_cores * 2))

    def _on_threads_changed(self, value: int):
        self._lbl_threads_val.setText(str(value))

    def retranslate_ui(self):
        """Обновить все тексты UI для текущего языка (мгновенное переключение)."""
        self._lbl_links.setText(f"🔗 {tr('Ссылки YouTube')}")
        self._links.setPlaceholderText(
            f"{tr('Каждая ссылка с новой строки')}…\nhttps://youtube.com/watch?v=..."
        )
        self._load_btn.setText(f"📂 {tr('Загрузить из links.txt')}")
        self._lbl_quality.setText(f"📊 {tr('Качество')}")
        self._rb_360.setText(tr("360p"))
        self._rb_720.setText(tr("720p"))
        self._rb_1080.setText(tr("1080p"))
        self._rb_max.setText(tr("Макс."))
        self._lbl_threads.setText(tr("Потоков загрузки:"))
        self._dl_btn.setText(f"▶ {tr('Скачать')}")
        self._folder_btn.setText(f"📂 {tr('Папка загрузок')}")
        self._status.setText(tr("Готов"))
        self._load_btn.setToolTip(tr("Загрузить из links.txt"))

    def _apply_config(self):
        q = self._config.get("download_quality", "360p")
        m = {"360p": self._rb_360, "720p": self._rb_720,
             "1080p": self._rb_1080, "max": self._rb_max}
        rb = m.get(q)
        if rb: rb.setChecked(True)

    def _load_links(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Выберите файл со ссылками"),
            str(self._app_dir),
            f"{tr('Текстовые файлы')} (*.txt *.m3u *.m3u8);;{tr('Все файлы')} (*)",
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
            links = self._extract_youtube_links(content)
            if not links:
                self._log.append(
                    f"⚠ {Path(path).name} — YouTube-ссылки не найдены"
                )
                return
            self._links.setPlainText("\n".join(links))
            self._log.append(
                f"📂 {Path(path).name} — {len(links)} ссылок"
            )
        except Exception as e:
            self._log.append(f"⚠ {tr('Ошибка чтения файла')}: {e}")

    # ── Drag & drop .txt / .m3u ────────────────────────────────────────────

    @staticmethod
    def _extract_youtube_links(text: str) -> list[str]:
        """Извлечь уникальные YouTube-ссылки из текста."""
        seen = set()
        result = []
        for m in _YOUTUBE_RE.finditer(text):
            url = m.group(0).rstrip('.,!?;:)\'"»')
            if url not in seen:
                seen.add(url)
                result.append(url)
        return result

    def _on_file_dropped(self, path: str):
        """Обработать сброшенный .txt/.m3u файл — извлечь YouTube-ссылки."""
        try:
            content = Path(path).read_text(encoding="utf-8")
            links = self._extract_youtube_links(content)
            if not links:
                self._log.append(
                    f"⚠ {os.path.basename(path)} — YouTube-ссылки не найдены"
                )
                return
            existing = self._links.toPlainText().strip()
            new_text = (existing + "\n" + "\n".join(links)).strip()
            self._links.setPlainText(new_text)
            self._log.append(
                f"📂 {os.path.basename(path)} — {len(links)} ссылок"
            )
        except Exception as e:
            self._log.append(f"⚠ Ошибка чтения {path}: {e}")

    # ── Download ────────────────────────────────────────────────────────────

    def _start(self):
        txt = self._links.toPlainText().strip()
        if not txt:
            QMessageBox.warning(self, "", "Вставьте ссылки YouTube.")
            return
        links = [l.strip() for l in txt.splitlines()
                 if l.strip() and not l.strip().startswith("#")]
        if not links:
            QMessageBox.warning(self, "", "Нет валидных ссылок.")
            return

        checked = self._qg.checkedButton()
        qm = {self._rb_360: "360p", self._rb_720: "720p",
              self._rb_1080: "1080p", self._rb_max: "max"}
        quality = qm.get(checked, "360p")

        self._busy(True); self._log.clear()
        self._bar.setValue(0); self._status.setText("Скачивание…")
        self._config["download_threads"] = self._threads_slider.value()

        self._thread = QThread(self)
        self._worker = DownloadWorker(
            links, quality, str(self._out), self._bin_dir,
            max_workers=self._threads_spin.value(),
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._status.setText)
        self._worker.status.connect(lambda m: self._log.append(m))
        self._worker.progress.connect(
            lambda p, fn, i, t: (
                self._bar.setValue(int(p)),
                self._status.setText(f"{fn} ({i}/{t})"),
            )
        )
        self._worker.file_done.connect(
            lambda fp: self._log.append(f"✅ {os.path.basename(fp)}")
        )
        self._worker.error.connect(lambda m: self._log.append(f"⚠ {m}"))
        self._worker.finished.connect(self._on_finish)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_finish(self, files):
        self._busy(False); self._bar.setValue(100)
        if files:
            self._status.setText(f"Готово: {len(files)} видео")
            self.downloads_finished.emit(files)
        else:
            self._status.setText("Ничего не скачано")

    def _busy(self, b):
        self._dl_btn.setEnabled(not b)
        self._links.setReadOnly(b)
        self._load_btn.setEnabled(not b)
        self._threads_slider.setEnabled(not b)
        for rb in (self._rb_360, self._rb_720, self._rb_1080, self._rb_max):
            rb.setEnabled(not b)
