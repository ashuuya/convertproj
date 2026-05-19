"""
convert_tab.py — Вкладка конвертации с редактором профилей.
FilterComboBox для всех полей, кнопка нового профиля, половина ЦП.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QEvent, QStringListModel, QPoint
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QFormLayout,
    QListWidget, QListWidgetItem, QAbstractItemView,
    QProgressBar, QFrame, QFileDialog, QMessageBox,
    QDialog, QLineEdit,
)
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

from gui.worker import ConvertWorker
from gui.profile_manager import (
    load_profiles, add_profile, delete_profile, reset_to_factory,
)
from gui.translations import tr
from gui.title_bar import TitleBar
from gui.base_dialog import BaseDialog

# ── Списки опций ────────────────────────────────────────────────────────────

VIDEO_CODECS   = ["mpeg4","libx264","libx265","libvpx","libvpx-vp9",
                  "h264_nvenc","hevc_nvenc","h264_amf","h264_qsv","libaom-av1"]
AUDIO_CODECS   = ["aac","libmp3lame","libopus","libvorbis","ac3","flac"]
VIDEO_BITRATES = ["96k","128k","200k","300k","400k","500k","550k","600k",
                  "800k","1M","1.5M","2M","3M","4M","6M","8M","10M","16M","20M"]
AUDIO_BITRATES = ["32k","48k","64k","96k","112k","128k","160k","192k","224k","256k","320k"]
RESOLUTIONS    = ["128x96","160x128","176x144","192x144","320x240","352x288",
                  "480x320","640x360","640x480","720x480","720x576",
                  "800x480","854x480","960x540","1280x720","1920x1080"]
SAMPLE_RATES   = ["8000","11025","16000","22050","32000","44100","48000","88200","96000"]
CHANNELS       = ["1 (моно)","2 (стерео)"]
EXTENSIONS     = [".3gp",".mp4",".mkv",".avi",".mov",".webm"]
SCALE_ALGOS    = ["lanczos","bilinear","bicubic","neighbor","area",
                  "fast_bilinear","gauss","sinc"]
FPS_OPTS       = ["15","20","23.976","24","25","29.97","30","48","50","60"]
ENCODERS       = ["h264_nvenc","h264_amf","h264_qsv","libx264"]


# ── NewProfileDialog ─────────────────────────────────────────────────────────

class NewProfileDialog(BaseDialog):
    """Безрамочный диалог создания нового профиля конвертации."""

    def __init__(self, parent=None):
        super().__init__(tr("Новый профиль"), 400, 200, parent)
        self._setup_content()

    def _setup_content(self):
        lo = self.content_layout()
        lo.addWidget(QLabel(
            tr("Новый профиль будет создан на основе текущих настроек."),
            objectName="subtitleLabel", wordWrap=True,
        ))

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(tr("Введите имя профиля…"))
        lo.addWidget(self._name_input)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton(tr("Отмена"))
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton(tr("Создать"))
        ok_btn.setObjectName("primaryBtn")
        ok_btn.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        lo.addLayout(btn_row)

    def profile_name(self) -> str:
        return self._name_input.text().strip()


# ── FilterComboBox ────────────────────────────────────────────────────────────

class FilterComboBox(QComboBox):
    """Non-editable combo: click opens popup, wheel disabled, consistent styling."""

    def __init__(self, items=None, default=""):
        super().__init__()
        self.setEditable(False)
        self.setDuplicatesEnabled(False)

        if items:
            self.addItems(items)
            if default:
                ix = self.findText(default)
                self.setCurrentIndex(ix) if ix >= 0 else self.setCurrentText(default)

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.showPopup()
                return True
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        event.ignore()  # no accidental scroll


def _fcb(items, default=""):
    """Shorthand for FilterComboBox creation."""
    return FilterComboBox(items, default)


# ── ConvertTab ───────────────────────────────────────────────────────────────

HALF_CORES = max(1, os.cpu_count() // 2)


class ConvertTab(QWidget):
    """Вкладка конвертации: очередь файлов + редактор профилей."""

    def __init__(self, app_dir: Path, bin_dir: Path, config: dict):
        super().__init__()
        self._app_dir = app_dir
        self._bin_dir = bin_dir
        self._config = config
        self._in_dir = app_dir / "Downloads" / "Recode"
        self._out_dir = app_dir / "Downloads" / "Recoded"
        self._profiles: dict = {}
        self._current = ""
        self._fields: dict = {}
        self._field_labels: dict = {}
        self._worker = None
        self._thread = None
        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        self.setLayout(QVBoxLayout())
        lo = self.layout()
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(12)

        cols = QHBoxLayout()
        cols.setSpacing(12)

        # ── СЛЕВА: Очередь файлов ──
        lc = QFrame(); lc.setObjectName("glassCard")
        lcl = QVBoxLayout(lc); lcl.setSpacing(6)
        self._lbl_files = QLabel("📁 Файлы", objectName="subtitleLabel")
        lcl.addWidget(self._lbl_files)

        self._file_list = QListWidget()
        self._file_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._file_list.setAcceptDrops(True)
        self._file_list.setDragDropMode(QAbstractItemView.DragDropMode.DropOnly)
        self._file_list.setToolTip("Перетащите файлы сюда")
        lcl.addWidget(self._file_list)

        fhb = QHBoxLayout(); fhb.setSpacing(4)
        self._add_btn = QPushButton("+ Добавить")
        self._add_btn.clicked.connect(self._add_dialog)
        fhb.addWidget(self._add_btn)
        self._del_btn = QPushButton("🗑"); self._del_btn.setObjectName("iconBtn")
        self._del_btn.clicked.connect(self._remove_sel)
        fhb.addWidget(self._del_btn)
        self._clr_btn = QPushButton("✕"); self._clr_btn.setObjectName("iconBtn")
        self._clr_btn.clicked.connect(self._file_list.clear)
        fhb.addWidget(self._clr_btn)
        fhb.addStretch()

        # Подписи под кнопками
        btn_labels = QHBoxLayout(); btn_labels.setSpacing(4)
        for text in ("", "Удалить", "Очистить"):
            lbl = QLabel(text, objectName="btnHintLabel")
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft if text else Qt.AlignmentFlag.AlignCenter)
            btn_labels.addWidget(lbl)
        btn_labels.addStretch()

        lcl.addLayout(fhb)
        lcl.addLayout(btn_labels)
        cols.addWidget(lc, stretch=2)

        # ── СПРАВА: Редактор профиля ──
        rc = QFrame(); rc.setObjectName("glassCard")
        rcl = QVBoxLayout(rc); rcl.setSpacing(8)

        phr = QHBoxLayout()
        self._lbl_profile = QLabel("⚙️ Профиль", objectName="subtitleLabel")
        phr.addWidget(self._lbl_profile)
        phr.addStretch()
        self._reset_btn = QPushButton("🔄"); self._reset_btn.setObjectName("iconBtn")
        self._reset_btn.setToolTip("Сбросить до заводских")
        self._reset_btn.clicked.connect(self._reset_profiles)
        phr.addWidget(self._reset_btn)
        rcl.addLayout(phr)

        shr = QHBoxLayout()
        # Кнопка нового профиля СЛЕВА от комбобокса
        self._newp_btn = QPushButton("➕")
        self._newp_btn.setObjectName("iconBtn")
        self._newp_btn.setToolTip("Новый профиль")
        self._newp_btn.clicked.connect(self._new_profile)
        shr.addWidget(self._newp_btn)

        self._profile_cb = FilterComboBox()
        self._profile_cb.setObjectName("profileCombo")
        self._profile_cb.currentTextChanged.connect(self._on_profile)
        shr.addWidget(self._profile_cb, stretch=1)

        self._save_btn = QPushButton("💾 Сохранить")
        self._save_btn.clicked.connect(self._save_profile)
        shr.addWidget(self._save_btn)

        self._delp_btn = QPushButton("🗑"); self._delp_btn.setObjectName("iconBtn")
        self._delp_btn.clicked.connect(self._delete_profile)
        shr.addWidget(self._delp_btn)
        rcl.addLayout(shr)

        # ── Поля (QFormLayout → FilterComboBox) ──
        fl = QFormLayout()
        fl.setSpacing(6)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        fl.setContentsMargins(0, 4, 0, 0)
        fl.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)

        self._add_f(fl, "output_extension",      "Формат",           _fcb(EXTENSIONS, ".3gp"))
        self._add_f(fl, "final_codec_video",      "Видео кодек",      _fcb(VIDEO_CODECS, "mpeg4"))
        self._add_f(fl, "final_bitrate_video",    "Битрейт видео",    _fcb(VIDEO_BITRATES, "200k"))
        self._add_f(fl, "final_resolution",       "Разрешение",       _fcb(RESOLUTIONS, "160x128"))
        self._add_f(fl, "scaling_algorithm",      "Масштабирование",  _fcb(SCALE_ALGOS, "lanczos"))
        self._add_f(fl, "final_codec_audio",      "Аудио кодек",      _fcb(AUDIO_CODECS, "aac"))
        self._add_f(fl, "final_bitrate_audio",    "Битрейт аудио",    _fcb(AUDIO_BITRATES, "96k"))
        self._add_f(fl, "final_samplerate_audio", "Частота (Гц)",     _fcb(SAMPLE_RATES, "44100"))
        self._add_f(fl, "final_channels_audio",   "Каналы",           _fcb(CHANNELS, "2 (стерео)"))
        self._add_f(fl, "normalize_fps",          "FPS",              _fcb(FPS_OPTS, "30"))

        rcl.addLayout(fl)

        # ── Кодировщик / CPU ──
        al = QFormLayout()
        al.setSpacing(6)
        al.setContentsMargins(0, 6, 0, 0)

        self._encoder_cb = _fcb(ENCODERS, self._config.get("hardware_encoder", "h264_nvenc"))
        self._lbl_encoder = QLabel("Кодировщик", objectName="subtitleLabel")
        al.addRow(self._lbl_encoder, self._encoder_cb)

        # CPU spin — с кнопкой "Половина"
        self._core_spin = QSpinBox()
        self._core_spin.setRange(1, os.cpu_count() or 64)
        saved = self._config.get("cpu_cores", 0)
        self._core_spin.setValue(saved if saved > 0 else HALF_CORES)
        cpu_row = QHBoxLayout(); cpu_row.setSpacing(6)
        cpu_row.addWidget(self._core_spin)
        self._half_btn = QPushButton("Половина ядер")
        self._half_btn.setObjectName("halfCpuBtn")
        self._half_btn.setToolTip(f"Установить количество ядер: {HALF_CORES}")
        self._half_btn.clicked.connect(lambda: self._core_spin.setValue(HALF_CORES))
        cpu_row.addWidget(self._half_btn)
        cpu_row.addStretch()
        self._lbl_cores = QLabel("Ядер CPU", objectName="subtitleLabel")
        al.addRow(self._lbl_cores, cpu_row)

        rcl.addLayout(al)
        rcl.addStretch()
        cols.addWidget(rc, stretch=3)
        lo.addLayout(cols)

        # ── Нижняя панель ──
        ac = QFrame(); ac.setObjectName("glassCard")
        abl = QVBoxLayout(ac); abl.setSpacing(5)
        abh = QHBoxLayout(); abh.setSpacing(10)

        self._conv_btn = QPushButton("▶ Конвертировать")
        self._conv_btn.setObjectName("primaryBtn")
        self._conv_btn.clicked.connect(self._start_conv)
        abh.addWidget(self._conv_btn)

        self._out_btn = QPushButton("📂 Результат")
        self._out_btn.clicked.connect(self._open_output)
        abh.addWidget(self._out_btn)
        abh.addStretch()
        abl.addLayout(abh)

        self._bar = QProgressBar(); self._bar.setValue(0)
        abl.addWidget(self._bar)
        self._status_cv = QLabel("Готов", objectName="subtitleLabel")
        abl.addWidget(self._status_cv)
        lo.addWidget(ac)

    def _add_f(self, fl: QFormLayout, key: str, label: str, combo: FilterComboBox):
        lbl = QLabel(label, objectName="subtitleLabel")
        fl.addRow(lbl, combo)
        self._fields[key] = combo
        self._field_labels[key] = lbl

    def retranslate_ui(self):
        """Обновить все тексты UI для текущего языка (мгновенное переключение)."""
        self._lbl_files.setText(f"📁 {tr('Файлы')}")
        self._add_btn.setText(f"+ {tr('Добавить')}")
        self._del_btn.setToolTip(tr("Удалить"))
        self._clr_btn.setToolTip(tr("Очистить"))
        self._lbl_profile.setText(f"⚙️ {tr('Профиль')}")
        self._save_btn.setText(f"💾 {tr('Сохранить')}")
        self._delp_btn.setToolTip(tr("Удалить профиль"))
        self._newp_btn.setToolTip(tr("Новый профиль"))
        self._reset_btn.setToolTip(tr("Сбросить до заводских"))
        self._field_labels["output_extension"].setText(tr("Формат"))
        self._field_labels["final_codec_video"].setText(f"{tr('Видео кодек')}")
        self._field_labels["final_bitrate_video"].setText(f"{tr('Битрейт видео')}")
        self._field_labels["final_resolution"].setText(tr("Разрешение"))
        self._field_labels["scaling_algorithm"].setText(tr("Масштабирование"))
        self._field_labels["final_codec_audio"].setText(f"{tr('Аудио кодек')}")
        self._field_labels["final_bitrate_audio"].setText(f"{tr('Битрейт аудио')}")
        self._field_labels["final_samplerate_audio"].setText(f"{tr('Частота (Гц)')}")
        self._field_labels["final_channels_audio"].setText(tr("Каналы"))
        self._field_labels["normalize_fps"].setText(tr("FPS"))
        self._lbl_encoder.setText(tr("Кодировщик"))
        self._lbl_cores.setText(tr("Ядер CPU"))
        self._half_btn.setToolTip(f"{tr('Использовать половину доступных ядер')} ({HALF_CORES})")
        self._conv_btn.setText(f"▶ {tr('Конвертировать')}")
        self._out_btn.setText(f"📂 {tr('Результат')}")
        self._status_cv.setText(tr("Готов"))

    def _open_output(self):
        """Открыть папку результата, создав её при необходимости."""
        self._out_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(self._out_dir))

    # ── Профили ────────────────────────────────────────────────────────────

    def _load_profiles(self):
        self._profiles = load_profiles(self._app_dir)
        self._profile_cb.blockSignals(True)
        self._profile_cb.clear()
        self._profile_cb.addItems(sorted(self._profiles.keys()))
        self._profile_cb.blockSignals(False)

        last = self._config.get("last_profile", "")
        if last in self._profiles:
            self._profile_cb.setCurrentText(last)
        elif self._profile_cb.count():
            self._profile_cb.setCurrentIndex(0)
        self._on_profile(self._profile_cb.currentText())

    def _on_profile(self, name: str):
        if not name or name not in self._profiles:
            return
        self._current = name
        prof = self._profiles[name]
        for k, w in self._fields.items():
            v = prof.get(k, "")
            ix = w.findText(str(v))
            w.setCurrentIndex(ix) if ix >= 0 else w.setCurrentText(str(v))
        self._delp_btn.setEnabled(not prof.get("builtin", False))

    def _read_fields(self) -> dict:
        d = {k: w.currentText() for k, w in self._fields.items()}
        old = self._profiles.get(self._current, {})
        d["description"] = old.get("description", self._current)
        d["builtin"] = old.get("builtin", False)
        return d

    def _save_profile(self):
        name = self._profile_cb.currentText()
        if not name:
            return
        self._profiles = add_profile(self._app_dir, self._profiles, name, self._read_fields())
        self._status_cv.setText("Сохранено")

    def _new_profile(self):
        """Создать новый профиль из текущих значений полей через безрамочный диалог."""
        dlg = NewProfileDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = dlg.profile_name()
        if not name:
            return
        if name in self._profiles:
            QMessageBox.information(self, "", f"Профиль «{name}» уже существует.")
            return
        settings = self._read_fields()
        settings["builtin"] = False
        self._profiles = add_profile(self._app_dir, self._profiles, name, settings)
        self._profile_cb.addItem(name)
        self._profile_cb.setCurrentText(name)
        self._status_cv.setText(f"Профиль «{name}» создан")

    def _delete_profile(self):
        if self._profiles.get(self._profile_cb.currentText(), {}).get("builtin"):
            QMessageBox.information(self, "", "Встроенные профили нельзя удалить.")
            return
        if QMessageBox.question(self, "", "Удалить профиль?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                == QMessageBox.StandardButton.Yes:
            self._profiles = delete_profile(self._app_dir, self._profiles,
                                            self._profile_cb.currentText())
            self._load_profiles()

    def _reset_profiles(self):
        if QMessageBox.question(self, "", "Сбросить профили до заводских?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) \
                == QMessageBox.StandardButton.Yes:
            self._profiles = reset_to_factory(self._app_dir)
            self._load_profiles()
            self._status_cv.setText("Профили сброшены")

    # ── Очередь файлов ─────────────────────────────────────────────────────

    def add_files(self, paths: list):
        exist = {self._file_list.item(i).toolTip() for i in range(self._file_list.count())}
        for p in paths:
            if p not in exist:
                it = QListWidgetItem(os.path.basename(p))
                it.setToolTip(p)
                self._file_list.addItem(it)
                exist.add(p)

    def _add_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите видео", str(self._in_dir),
            "Видео (*.mp4 *.mkv *.avi *.mov *.flv *.webm);;Все (*)",
        )
        if files:
            self.add_files(files)

    def _remove_sel(self):
        for it in self._file_list.selectedItems():
            self._file_list.takeItem(self._file_list.row(it))

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e: QDropEvent):
        paths = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p.lower().endswith(('.mp4','.mkv','.avi','.mov','.flv','.webm')):
                paths.append(p)
        if paths:
            self.add_files(paths)
        e.acceptProposedAction()

    # ── Conversion ──────────────────────────────────────────────────────────

    def _start_conv(self):
        if not self._file_list.count():
            QMessageBox.warning(self, "", "Добавьте файлы в очередь.")
            return
        name = self._profile_cb.currentText()
        if not name or name not in self._profiles:
            QMessageBox.warning(self, "", "Выберите профиль.")
            return

        prof = dict(self._profiles[name])
        prof['_profile_name'] = name
        files = [self._file_list.item(i).toolTip() for i in range(self._file_list.count())]

        if any(not os.path.isfile(p) for p in files):
            QMessageBox.warning(self, "", "Некоторые файлы не найдены.")
            return

        encoder = self._encoder_cb.currentText()
        cores = self._core_spin.value()
        fps_w = self._fields.get("normalize_fps")
        fps = int(fps_w.currentText() if fps_w else "30")

        self._busy(True)
        self._bar.setValue(0)
        self._status_cv.setText("Конвертация…")

        self._thread = QThread(self)
        self._worker = ConvertWorker(
            files, prof, str(self._in_dir), str(self._out_dir),
            self._bin_dir, fps, encoder, cores,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._status_cv.setText)
        self._worker.progress.connect(
            lambda p, fn, i, t: (
                self._bar.setValue(int(p)),
                self._status_cv.setText(f"{fn} ({i}/{t})"),
            )
        )
        self._worker.error.connect(lambda m: self._status_cv.setText("Ошибка"))
        self._worker.finished.connect(self._on_conv_finish)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_conv_finish(self, files):
        self._busy(False)
        if files:
            self._bar.setValue(100)
            self._status_cv.setText(f"Готово: {len(files)} файлов")
        else:
            self._status_cv.setText("Не удалось")

    def _busy(self, b):
        for w in (self._conv_btn, self._add_btn, self._del_btn, self._clr_btn,
                  self._profile_cb, self._save_btn, self._delp_btn, self._reset_btn,
                  self._newp_btn):
            w.setEnabled(not b)
        self._file_list.setAcceptDrops(not b)
