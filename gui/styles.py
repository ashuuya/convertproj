"""
styles.py — Complete frosted-glass QSS for ConvertProj.
Typography: Inter / JetBrains Mono (tech feel).
Custom title bar with macOS traffic-light buttons.
"""

# Shared base
BASE = """
/* ── Font ── */
QMainWindow, QDialog, QWidget, QLabel, QPushButton, QComboBox,
QLineEdit, QTextEdit, QListWidget, QSpinBox, QCheckBox, QRadioButton,
QGroupBox, QProgressBar, QTabWidget, QTabBar, QScrollBar {
    font-family: "Inter", "SF Pro Display", "Segoe UI Variable", "Segoe UI", sans-serif;
    font-size: 13px;
}

QLabel#tbTitle, QLabel#titleLabel {
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", monospace;
}

QTextEdit#logArea, QLabel#monoLabel {
    font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 12px;
}

/* ── Glass card ── */
QFrame#glassCard {
    border-radius: 12px;
    padding: 16px;
}

/* ── Title bar ── */
QWidget#titleBar {
    min-height: 42px;
    max-height: 42px;
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    border-bottom: 1px solid;
}

QLabel#tbTitle {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Traffic light buttons */
QPushButton#tbClose, QPushButton#tbMin, QPushButton#tbMax {
    border: none;
    border-radius: 7px;
    min-width: 13px;
    max-width: 13px;
    min-height: 13px;
    max-height: 13px;
    padding: 0;
}

QPushButton#tbClose {
    background: #FF5F57;
    border: 0.5px solid #E04840;
}
QPushButton#tbClose:hover {
    background: #FF8078;
}

QPushButton#tbMin {
    background: #FEBC2E;
    border: 0.5px solid #D9A026;
}
QPushButton#tbMin:hover {
    background: #FFD060;
}

QPushButton#tbMax {
    background: #28C840;
    border: 0.5px solid #1DA836;
}
QPushButton#tbMax:hover {
    background: #40E058;
}

QPushButton#tbClose:pressed { background: #BF443D; }
QPushButton#tbMin:pressed { background: #BF9420; }
QPushButton#tbMax:pressed { background: #1EA030; }

/* ── Pill tab container ── */
QWidget#pillContainer {
    border-radius: 12px;
}

QPushButton#pillTab {
    border: none;
    border-radius: 19px;
    padding: 6px 24px;
    font-size: 13px;
    font-weight: 500;
    min-height: 36px;
}

/* ── Pill slider (underline) ── */
QWidget#pillSlider {
    background: #007AFF;
    border-radius: 2px;
}

/* ── Buttons ── */
QPushButton {
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid;
}

QPushButton#primaryBtn {
    border: none;
    font-weight: 600;
    padding: 8px 20px;
}

QPushButton#iconBtn {
    border: none;
    border-radius: 7px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    padding: 0;
    font-size: 15px;
}

/* ── Button hint labels ── */
QLabel#btnHintLabel {
    font-size: 10px;
    color: rgba(0,0,0,0.30);
    padding: 0;
    margin: 0;
    min-height: 14px;
}

/* ── ComboBox ── */
QComboBox {
    border-radius: 7px;
    padding: 5px 10px;
    min-height: 24px;
    min-width: 80px;
}

QComboBox::drop-down {
    border: none;
    width: 18px;
}

QComboBox QAbstractItemView {
    border-radius: 7px;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    min-height: 26px;
    padding: 3px 8px;
    border-radius: 5px;
}

/* ── Line / Text Edit ── */
QLineEdit, QTextEdit, QPlainTextEdit {
    border-radius: 8px;
    padding: 7px 12px;
}

QTextEdit#logArea {
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
}

/* ── List ── */
QListWidget {
    border-radius: 8px;
    padding: 3px;
    outline: none;
}

QListWidget::item {
    border-radius: 6px;
    padding: 5px 8px;
}

/* ── Progress bar ── */
QProgressBar {
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}

QProgressBar::chunk {
    border-radius: 4px;
}

/* ── Check / Radio ── */
QCheckBox, QRadioButton { spacing: 6px; }

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
}
QRadioButton::indicator { border-radius: 8px; }

/* ── Scrollbar ── */
QScrollBar:vertical {
    background: transparent;
    width: 5px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ── SpinBox ── */
QSpinBox {
    border-radius: 7px;
    padding: 4px 8px;
    min-height: 24px;
}

QSpinBox::up-button, QSpinBox::down-button {
    border: none;
    border-radius: 4px;
    width: 18px;
    margin: 2px;
}

QSpinBox::up-button {
    border-bottom: none;
}

QSpinBox::up-arrow {
    width: 8px;
    height: 8px;
}

QSpinBox::down-arrow {
    width: 8px;
    height: 8px;
}

/* ── GroupBox ── */
QGroupBox {
    border-radius: 12px;
    padding: 16px 14px 12px;
    margin-top: 4px;
    font-weight: 500;
}
QGroupBox::title {
    subcontrol-origin: padding;
    left: 12px;
    padding: 0 5px;
}
"""

# ── LIGHT ────────────────────────────────────────────────────────────────────

LIGHT = BASE + """
QMainWindow, QDialog, QWidget {
    color: #1C1C1E;
}
QMainWindow, QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #D1D1D6, stop:1 #E5E5EA);
}

QWidget#titleBar {
    background: rgba(220, 220, 225, 0.70);
    border-bottom-color: rgba(0,0,0,0.08);
}
QLabel#tbTitle { color: #1C1C1E; }

QWidget#pillContainer {
    background: rgba(200, 200, 205, 0.40);
    border: 1px solid rgba(180,180,185,0.30);
}
QPushButton#pillTab {
    background: transparent;
    color: rgba(0,0,0,0.35);
}
QPushButton#pillTab:hover {
    background: rgba(255,255,255,0.25);
    color: rgba(0,0,0,0.55);
}
QPushButton#pillTab[active="true"] {
    background: rgba(255,255,255,0.60);
    color: #1C1C1E;
}

QWidget#pillSlider {
    background: #007AFF;
    border-radius: 2px;
}

QFrame#glassCard {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(190,190,195,0.35);
}

QPushButton {
    background: rgba(255,255,255,0.55);
    border-color: rgba(190,190,195,0.35);
    color: #1C1C1E;
}
QPushButton:hover {
    background: rgba(255,255,255,0.75);
    border-color: rgba(180,180,185,0.50);
}
QPushButton:pressed { background: rgba(255,255,255,0.90); }
QPushButton:disabled {
    background: rgba(200,200,205,0.20);
    color: rgba(0,0,0,0.18);
    border-color: transparent;
}
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #007AFF, stop:1 #00A8FF);
    color: #fff;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0066D6, stop:1 #0090E6);
}
QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0055B3, stop:1 #007ACC);
}
QPushButton#primaryBtn:disabled {
    background: rgba(0,122,255,0.30);
    color: rgba(255,255,255,0.40);
}
QPushButton#iconBtn {
    background: rgba(220,220,225,0.30);
}
QPushButton#iconBtn:hover {
    background: rgba(220,220,225,0.55);
}
QPushButton#halfCpuBtn {
    background: rgba(220,220,225,0.30);
    border: 1px solid rgba(190,190,195,0.35);
    border-radius: 7px;
    padding: 5px 12px;
    font-size: 12px;
    color: #1C1C1E;
}
QPushButton#halfCpuBtn:hover {
    background: rgba(220,220,225,0.55);
}

QComboBox {
    background: rgba(255,255,255,0.50);
    border: 1px solid rgba(190,190,195,0.35);
    color: #1C1C1E;
}
QComboBox:hover { background: rgba(255,255,255,0.65); }
QComboBox QAbstractItemView {
    background: rgba(245,245,250,0.98);
    border: 1px solid rgba(0,0,0,0.06);
    color: #1C1C1E;
}
QComboBox QAbstractItemView::item {
    color: #1C1C1E;
    background: transparent;
    padding: 4px 8px;
    min-height: 22px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:selected { background: #007AFF; color: #fff; }
QComboBox QAbstractItemView::item:hover:!selected { background: rgba(0,122,255,0.08); }

QComboBox#profileCombo {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(190,190,195,0.35);
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 30px;
    font-weight: 500;
    color: #1C1C1E;
}
QComboBox#profileCombo:hover { background: rgba(255,255,255,0.75); }
QComboBox#profileCombo::drop-down {
    border: none;
    width: 24px;
}
QComboBox#profileCombo QAbstractItemView {
    background: rgba(245,245,250,0.98);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 8px;
    padding: 6px;
    color: #1C1C1E;
}
QComboBox#profileCombo QAbstractItemView::item {
    color: #1C1C1E;
    background: transparent;
    padding: 8px 12px;
    min-height: 30px;
    border-radius: 6px;
}
QComboBox#profileCombo QAbstractItemView::item:selected { background: #007AFF; color: #fff; }
QComboBox#profileCombo QAbstractItemView::item:hover:!selected { background: rgba(0,122,255,0.08); }

QLineEdit, QTextEdit, QPlainTextEdit {
    background: rgba(255,255,255,0.45);
    border: 1px solid rgba(190,190,195,0.35);
    color: #1C1C1E;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #007AFF;
    background: rgba(255,255,255,0.65);
}
QTextEdit#logArea {
    background: rgba(0,0,0,0.04);
    color: rgba(0,0,0,0.60);
}

QListWidget {
    background: rgba(255,255,255,0.30);
    border: 1px solid rgba(190,190,195,0.30);
    color: #1C1C1E;
}
QListWidget::item:selected { background: rgba(0,122,255,0.18); color: #1C1C1E; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.15); }

QProgressBar { background: rgba(200,200,205,0.25); }
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #007AFF, stop:1 #00C7FF);
}

QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid rgba(0,0,0,0.15);
    background: rgba(255,255,255,0.55);
}
QCheckBox::indicator:checked { background: #007AFF; border-color: #007AFF; }
QRadioButton::indicator:checked { background: #007AFF; border-color: #007AFF; }

QSpinBox {
    background: rgba(255,255,255,0.50);
    border: 1px solid rgba(190,190,195,0.35);
    color: #1C1C1E;
}
QSpinBox:focus {
    border-color: #007AFF;
    background: rgba(255,255,255,0.65);
}
QSpinBox::up-button, QSpinBox::down-button {
    background: rgba(220,220,225,0.40);
    border-radius: 4px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: rgba(200,200,205,0.60);
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background: rgba(180,180,185,0.75);
}
QSpinBox::up-arrow { image: url(none); }
QSpinBox::down-arrow { image: url(none); }

QGroupBox {
    background: rgba(255,255,255,0.30);
    border: 1px solid rgba(190,190,195,0.30);
    color: #1C1C1E;
}

QScrollBar::handle:vertical { background: rgba(0,0,0,0.08); }
QScrollBar::handle:vertical:hover { background: rgba(0,0,0,0.14); }
"""

# ── DARK ─────────────────────────────────────────────────────────────────────

DARK = BASE + """
QMainWindow, QDialog, QWidget {
    color: #F0F0F4;
}
QMainWindow, QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #1C1C20, stop:1 #2C2C30);
}

QWidget#titleBar {
    background: rgba(30,30,35,0.60);
    border-bottom-color: rgba(255,255,255,0.04);
}
QLabel#tbTitle { color: #F0F0F4; }

QWidget#pillContainer {
    background: rgba(40,40,45,0.25);
    border: 1px solid rgba(255,255,255,0.05);
}
QPushButton#pillTab {
    background: transparent;
    color: rgba(255,255,255,0.30);
}
QPushButton#pillTab:hover {
    background: rgba(255,255,255,0.06);
    color: rgba(255,255,255,0.50);
}
QPushButton#pillTab[active="true"] {
    background: rgba(55,55,60,0.50);
    color: #F0F0F4;
}

QWidget#pillSlider {
    background: #0A84FF;
    border-radius: 2px;
}

QLabel#btnHintLabel {
    font-size: 10px;
    color: rgba(255,255,255,0.25);
    padding: 0;
    margin: 0;
    min-height: 14px;
}

QFrame#glassCard {
    background: rgba(38,38,42,0.50);
    border: 1px solid rgba(255,255,255,0.05);
}

QPushButton {
    background: rgba(50,50,55,0.40);
    border-color: rgba(255,255,255,0.07);
    color: #F0F0F4;
}
QPushButton:hover {
    background: rgba(65,65,70,0.55);
}
QPushButton:pressed { background: rgba(80,80,85,0.65); }
QPushButton:disabled {
    background: rgba(40,40,45,0.25);
    color: rgba(255,255,255,0.18);
    border-color: transparent;
}
QPushButton#primaryBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0A84FF, stop:1 #5E5CE6);
    color: #fff;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0066D6, stop:1 #4B48D6);
}
QPushButton#primaryBtn:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                stop:0 #0052B8, stop:1 #3C39C4);
}
QPushButton#primaryBtn:disabled {
    background: rgba(10,132,255,0.25);
    color: rgba(255,255,255,0.35);
}
QPushButton#iconBtn {
    background: rgba(255,255,255,0.04);
}
QPushButton#iconBtn:hover {
    background: rgba(255,255,255,0.10);
}
QPushButton#halfCpuBtn {
    background: rgba(60,60,65,0.40);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 7px;
    padding: 5px 12px;
    font-size: 12px;
    color: #F0F0F4;
}
QPushButton#halfCpuBtn:hover {
    background: rgba(75,75,80,0.55);
}

QComboBox {
    background: rgba(50,50,55,0.40);
    border: 1px solid rgba(255,255,255,0.07);
    color: #F0F0F4;
}
QComboBox:hover { background: rgba(65,65,70,0.55); }
QComboBox QAbstractItemView {
    background: rgba(32,32,36,0.98);
    border: 1px solid rgba(255,255,255,0.06);
    color: #F0F0F4;
}
QComboBox QAbstractItemView::item:selected { background: #0A84FF; color: #fff; }
QComboBox QAbstractItemView::item:hover:!selected { background: rgba(10,132,255,0.12); }

QComboBox#profileCombo {
    background: rgba(55,55,60,0.45);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 30px;
    font-weight: 500;
    color: #F0F0F4;
}
QComboBox#profileCombo:hover { background: rgba(70,70,75,0.55); }
QComboBox#profileCombo::drop-down {
    border: none;
    width: 24px;
}
QComboBox#profileCombo QAbstractItemView {
    background: rgba(32,32,36,0.98);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 6px;
    color: #F0F0F4;
}
QComboBox#profileCombo QAbstractItemView::item {
    padding: 8px 12px;
    min-height: 30px;
    border-radius: 6px;
}
QComboBox#profileCombo QAbstractItemView::item:selected { background: #0A84FF; color: #fff; }
QComboBox#profileCombo QAbstractItemView::item:hover:!selected { background: rgba(10,132,255,0.12); }

QLineEdit, QTextEdit, QPlainTextEdit {
    background: rgba(50,50,55,0.35);
    border: 1px solid rgba(255,255,255,0.07);
    color: #F0F0F4;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #0A84FF;
    background: rgba(55,55,60,0.50);
}
QTextEdit#logArea {
    background: rgba(0,0,0,0.15);
    color: rgba(255,255,255,0.55);
}

QListWidget {
    background: rgba(38,38,42,0.25);
    border: 1px solid rgba(255,255,255,0.05);
    color: #F0F0F4;
}
QListWidget::item:selected { background: rgba(10,132,255,0.22); color: #F0F0F4; }
QListWidget::item:hover:!selected { background: rgba(255,255,255,0.04); }

QProgressBar { background: rgba(50,50,55,0.35); }
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #0A84FF, stop:1 #5E5CE6);
}

QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(50,50,55,0.40);
}
QCheckBox::indicator:checked { background: #0A84FF; border-color: #0A84FF; }
QRadioButton::indicator:checked { background: #0A84FF; border-color: #0A84FF; }

QSpinBox {
    background: rgba(50,50,55,0.40);
    border: 1px solid rgba(255,255,255,0.07);
    color: #F0F0F4;
}
QSpinBox:focus {
    border-color: #0A84FF;
    background: rgba(55,55,60,0.50);
}
QSpinBox::up-button, QSpinBox::down-button {
    background: rgba(60,60,65,0.40);
    border-radius: 4px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: rgba(75,75,80,0.55);
}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {
    background: rgba(90,90,95,0.65);
}
QSpinBox::up-arrow { image: url(none); }
QSpinBox::down-arrow { image: url(none); }

QGroupBox {
    background: rgba(38,38,42,0.35);
    border: 1px solid rgba(255,255,255,0.05);
    color: #F0F0F4;
}

QScrollBar::handle:vertical { background: rgba(255,255,255,0.10); }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.18); }
"""


THEMES = {"light": LIGHT, "dark": DARK}
