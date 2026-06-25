#!/usr/bin/env python3
"""
Generador de Etiquetas de Ubicación v2.0
Tamaño: 51.20 × 25.00 mm (EVA58)
Requiere: PyQt6, reportlab
"""

import sys
import os
import json
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QSpinBox,
    QRadioButton, QButtonGroup, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QFrame, QGroupBox, QSizePolicy, QScrollArea,
    QStatusBar, QSplitter,
)
from PyQt6.QtCore import Qt, QRectF, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QFontMetrics, QPalette,
)

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QFontMetrics, QPalette, QIcon
)

# ── Constantes ────────────────────────────────────────────────────────────────
LABEL_W_MM = 51.20
LABEL_H_MM = 25.00
LABEL_W = LABEL_W_MM * mm
LABEL_H = LABEL_H_MM * mm

CONFIG_PATH = Path(__file__).parent / "config.json"

FUENTES_PDF = {
    "Helvetica": ("Helvetica-Bold", "Helvetica"),
    "Arial":     ("Helvetica-Bold", "Helvetica"),   # fallback ReportLab
    "Times":     ("Times-Bold",     "Times-Roman"),
    "Courier":   ("Courier-Bold",   "Courier"),
}


# ── Estilos (Tema Naranja) ────────────────────────────────────────────────────
STYLE = """
QMainWindow, QWidget#root {
    background: #F7F8FA;
}
QGroupBox {
    font-size: 11px;
    font-weight: 600;
    color: #444;
    border: 1.5px solid #DDE1E8;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    background: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    left: 10px;
}
QLabel {
    color: #333;
    font-size: 12px;
}
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background: #FFFFFF;
    border: 1.5px solid #DDE1E8;
    border-radius: 5px;
    padding: 4px 8px;
    font-size: 12px;
    color: #222;
    selection-background-color: #F29C2E; /* Naranja suave para selección */
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #F08800; /* Naranja principal */
}
QComboBox::drop-down { border: none; }
QComboBox::down-arrow { image: none; width: 0; }
QPushButton#primary {
    background: #F08800; /* Naranja principal */
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
    padding: 9px 24px;
}
QPushButton#primary:hover { background: #D97A00; } /* Naranja hover */
QPushButton#primary:pressed { background: #B36500; } /* Naranja pressed */
QPushButton#secondary {
    background: #EAECF2;
    color: #444;
    border: none;
    border-radius: 6px;
    font-size: 12px;
    padding: 9px 18px;
}
QPushButton#secondary:hover { background: #D5D9E4; }
QPushButton#danger {
    background: #FEF4E6; /* Naranja pálido */
    color: #B36500; /* Texto naranja oscuro */
    border: 1.5px solid #F7C483; /* Borde naranja pastel */
    border-radius: 6px;
    font-size: 12px;
    padding: 9px 16px;
}
QPushButton#danger:hover { background: #FCE6CA; } /* Naranja pálido hover */
QRadioButton, QCheckBox {
    font-size: 12px;
    color: #333;
    spacing: 6px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 15px; height: 15px;
}
QStatusBar {
    background: #EAECF2;
    color: #666;
    font-size: 11px;
    border-top: 1px solid #DDE1E8;
}
"""

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_CFG = {
    "fuente": "Helvetica",
    "tam_linea1": 7,
    "tam_linea2": 14,
    "copias": 1,
    "abrir_pdf": True,
    "modo": "manual",
    "serie": {
        "pref": "A", "n2i": "1", "n2f": "1",
        "n3i": "1", "n3f": "6",
        "n4i": "1", "n4f": "5",
    },
}

def resolver_ruta(ruta_relativa):
    """ Devuelve la ruta absoluta de los recursos, compatible con PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

def cargar_cfg():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            # Merge con defaults por si faltan claves
            for k, v in DEFAULT_CFG.items():
                cfg.setdefault(k, v)
            return cfg
        except Exception:
            pass
    return DEFAULT_CFG.copy()

def guardar_cfg(cfg: dict):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


# ── PDF ───────────────────────────────────────────────────────────────────────
def generar_pdf(etiquetas, ruta, copies=1, fuente="Helvetica",
                tam1=7, tam2=14):
    bold, normal = FUENTES_PDF.get(fuente, ("Helvetica-Bold", "Helvetica"))
    c = rl_canvas.Canvas(ruta, pagesize=(LABEL_W, LABEL_H))
    for et in etiquetas:
        for _ in range(copies):
            _dibujar(c, et, bold, normal, tam1, tam2)
            c.showPage()
    c.save()


def _dibujar(c, texto, bold, normal, tam1, tam2):
    partes = texto.strip().split(".")
    cx = LABEL_W / 2
    cy = LABEL_H / 2
    if len(partes) >= 2:
        c.setFont(normal, tam1)
        c.drawCentredString(cx, cy + 4.5 * mm, partes[0])
        c.setFont(bold, tam2)
        c.drawCentredString(cx, cy - 3.5 * mm, ".".join(partes[1:]))
    else:
        c.setFont(bold, tam2)
        c.drawCentredString(cx, cy - 2 * mm, texto)


def imprimir_pdf_windows(ruta: str):
    """Envía el PDF a la impresora predeterminada en Windows via ShellExecute."""
    import ctypes
    SW_HIDE = 0
    ctypes.windll.shell32.ShellExecuteW(
        None, "print", ruta, None, None, SW_HIDE
    )


def abrir_pdf(ruta: str):
    os.startfile(ruta)


# ── Vista previa de etiqueta ──────────────────────────────────────────────────
class EtiquetaPreview(QWidget):
    """Dibuja una etiqueta a escala en Qt."""

    SCALE = 4.0   # px por mm

    def __init__(self, parent=None):
        super().__init__(parent)
        pw = int(LABEL_W_MM * self.SCALE)
        ph = int(LABEL_H_MM * self.SCALE)
        self.setFixedSize(pw + 20, ph + 20)
        self._texto = ""
        self._fuente = "Arial"
        self._tam1 = 7
        self._tam2 = 14

    def set_data(self, texto, fuente, tam1, tam2):
        self._texto = texto
        self._fuente = fuente
        self._tam1 = tam1
        self._tam2 = tam2
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pw = int(LABEL_W_MM * self.SCALE)
        ph = int(LABEL_H_MM * self.SCALE)
        ox, oy = 10, 10

        # Sombra suave
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#D0D4DC")))
        p.drawRoundedRect(ox + 3, oy + 3, pw, ph, 4, 4)

        # Fondo etiqueta
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(QPen(QColor("#BBCCE8"), 1.5))
        p.drawRoundedRect(ox, oy, pw, ph, 4, 4)

        if not self._texto:
            p.end()
            return

        partes = self._texto.strip().split(".")
        cx = ox + pw / 2
        cy = oy + ph / 2

        # Mapeo fuente Qt
        font_family = self._fuente if self._fuente in ("Arial", "Times New Roman", "Courier New") else "Arial"
        if self._fuente == "Helvetica":
            font_family = "Arial"
        elif self._fuente == "Times":
            font_family = "Times New Roman"
        elif self._fuente == "Courier":
            font_family = "Courier New"

        if len(partes) >= 2:
            # línea superior pequeña
            f1 = QFont(font_family, int(self._tam1 * self.SCALE * 0.35))
            p.setFont(f1)
            p.setPen(QColor("#555"))
            fm1 = QFontMetrics(f1)
            t1 = partes[0]
            p.drawText(int(cx - fm1.horizontalAdvance(t1) / 2),
                       int(cy - ph * 0.05),
                       t1)
            # línea inferior grande bold
            f2 = QFont(font_family, int(self._tam2 * self.SCALE * 0.35), QFont.Weight.Bold)
            p.setFont(f2)
            p.setPen(QColor("#111"))
            fm2 = QFontMetrics(f2)
            t2 = ".".join(partes[1:])
            p.drawText(int(cx - fm2.horizontalAdvance(t2) / 2),
                       int(cy + ph * 0.30),
                       t2)
        else:
            f = QFont(font_family, int(self._tam2 * self.SCALE * 0.35), QFont.Weight.Bold)
            p.setFont(f)
            p.setPen(QColor("#111"))
            fm = QFontMetrics(f)
            p.drawText(int(cx - fm.horizontalAdvance(self._texto) / 2),
                       int(cy + ph * 0.12),
                       self._texto)
        p.end()


# ── Ventana principal ─────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cfg = cargar_cfg()
        self.setWindowTitle("Generador Etiquetas GA")
        self.setWindowIcon(QIcon(resolver_ruta("icono.ico"))) # <-- NUEVO
        self.setMinimumSize(820, 620)
        self.setObjectName("root")
        self._build_ui()
        self._cargar_cfg_ui()
        self._actualizar_preview()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(14, 12, 14, 10)

        # Header
        root.addWidget(self._header())

        # Cuerpo principal (splitter izq / der)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)

        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setSpacing(10)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.addWidget(self._modo_group())
        lv.addWidget(self._input_group(), 1)
        lv.addWidget(self._serie_group())
        lv.addWidget(self._opciones_group())
        lv.addWidget(self._botones_frame())

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setSpacing(10)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.addWidget(self._preview_group())

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([520, 280])
        root.addWidget(splitter, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo.")

    def _header(self):
        frm = QFrame()
        frm.setStyleSheet(
            "background: #F6A23B; border-radius: 7px;"
        )
        hl = QHBoxLayout(frm)
        hl.setContentsMargins(16, 10, 16, 10)
        title = QLabel("GRAN ALMACÉN ETIQUETAS                   by Lacho")
        title.setStyleSheet("color:#fff; font-size:15px; font-weight:700; background:transparent;")
        size_lbl = QLabel("51.20 × 25.00 mm  |  EVA58")
        size_lbl.setStyleSheet("color:#FFFFFF; font-size:11px; background:transparent;")
        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(size_lbl)
        return frm

    def _modo_group(self):
        grp = QGroupBox("Modo de entrada")
        hl = QHBoxLayout(grp)
        hl.setSpacing(20)
        self.rb_manual = QRadioButton("Etiquetas Manuales (Una por linea)")
        self.rb_serie  = QRadioButton("Serie automática")
        self.btn_grp   = QButtonGroup()
        self.btn_grp.addButton(self.rb_manual, 0)
        self.btn_grp.addButton(self.rb_serie, 1)
        self.rb_manual.setChecked(True)
        self.rb_manual.toggled.connect(self._on_modo)
        hl.addWidget(self.rb_manual)
        hl.addWidget(self.rb_serie)
        hl.addStretch()
        return grp

    def _input_group(self):
        self.grp_manual = QGroupBox("Etiquetas  (una por línea)")
        vl = QVBoxLayout(self.grp_manual)
        self.txt_etiquetas = QTextEdit()
        self.txt_etiquetas.setFont(QFont("Courier New", 11))
        self.txt_etiquetas.setPlaceholderText("A.1.2.1\nA.1.2.2\n…")
        self.txt_etiquetas.textChanged.connect(self._actualizar_preview)
        vl.addWidget(self.txt_etiquetas)
        return self.grp_manual

    def _serie_group(self):
        self.grp_serie = QGroupBox("Parámetros de serie")
        grid = QGridLayout(self.grp_serie)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)

        campos = [
            ("Prefijo:", "pref", 0, 0),
            ("N2 inicio:", "n2i", 0, 2), ("N2 fin:", "n2f", 0, 4),
            ("N3 inicio:", "n3i", 1, 0), ("N3 fin:", "n3f", 1, 2),
            ("N4 inicio:", "n4i", 1, 4), ("N4 fin:", "n4f", 1, 6),
        ]
        self._serie_vars = {}
        for lbl_txt, key, row, col in campos:
            grid.addWidget(QLabel(lbl_txt), row, col)
            le = QLineEdit()
            le.setFixedWidth(50)
            le.textChanged.connect(self._actualizar_preview)
            self._serie_vars[key] = le
            grid.addWidget(le, row, col + 1)

        btn_regen = QPushButton("↻  Regenerar lista")
        btn_regen.setObjectName("secondary")
        btn_regen.clicked.connect(self._generar_serie)
        grid.addWidget(btn_regen, 2, 0, 1, 4)
        self.grp_serie.hide()
        return self.grp_serie

    def _opciones_group(self):
        grp = QGroupBox("Opciones")
        gl = QGridLayout(grp)
        gl.setHorizontalSpacing(12)
        gl.setVerticalSpacing(6)

        gl.addWidget(QLabel("Fuente:"), 0, 0)
        self.cb_fuente = QComboBox()
        self.cb_fuente.addItems(["Helvetica", "Arial", "Times", "Courier"])
        self.cb_fuente.currentTextChanged.connect(self._actualizar_preview)
        gl.addWidget(self.cb_fuente, 0, 1)

        gl.addWidget(QLabel("Tamaño línea 1:"), 0, 2)
        self.sb_tam1 = QSpinBox()
        self.sb_tam1.setRange(5, 20); self.sb_tam1.setValue(7)
        self.sb_tam1.valueChanged.connect(self._actualizar_preview)
        gl.addWidget(self.sb_tam1, 0, 3)

        gl.addWidget(QLabel("Tamaño línea 2:"), 0, 4)
        self.sb_tam2 = QSpinBox()
        self.sb_tam2.setRange(6, 36); self.sb_tam2.setValue(14)
        self.sb_tam2.valueChanged.connect(self._actualizar_preview)
        gl.addWidget(self.sb_tam2, 0, 5)

        gl.addWidget(QLabel("Copias/etiqueta:"), 1, 0)
        self.sb_copias = QSpinBox()
        self.sb_copias.setRange(1, 99); self.sb_copias.setValue(1)
        self.sb_copias.valueChanged.connect(self._actualizar_preview)
        gl.addWidget(self.sb_copias, 1, 1)

        self.chk_abrir = QCheckBox("Abrir PDF al generar")
        self.chk_abrir.setChecked(True)
        gl.addWidget(self.chk_abrir, 1, 2, 1, 2)

        return grp

    def _botones_frame(self):
        frm = QFrame()
        hl = QHBoxLayout(frm)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color:#888; font-size:11px;")

        btn_pdf = QPushButton("Guardar PDF")
        btn_pdf.setObjectName("primary")
        btn_pdf.clicked.connect(self._accion_pdf)

        btn_print = QPushButton("Imprimir")
        btn_print.setObjectName("primary")
        btn_print.setStyleSheet(
            "QPushButton { background:#28A745; color:#fff; border:none; "
            "border-radius:6px; font-size:13px; font-weight:700; padding:9px 20px; }"
            "QPushButton:hover { background:#1E8035; }"
        )
        btn_print.clicked.connect(self._accion_imprimir)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("danger")
        btn_limpiar.clicked.connect(self._limpiar)

        hl.addWidget(btn_pdf)
        hl.addWidget(btn_print)
        hl.addWidget(btn_limpiar)
        hl.addStretch()
        hl.addWidget(self.lbl_count)
        return frm

    def _preview_group(self):
        grp = QGroupBox("Vista previa")
        vl = QVBoxLayout(grp)
        vl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        lbl = QLabel("Primera etiqueta de la lista:")
        lbl.setStyleSheet("color:#888; font-size:11px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(lbl)

        self.preview_widget = EtiquetaPreview()
        vl.addWidget(self.preview_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self.lbl_preview_txt = QLabel("")
        self.lbl_preview_txt.setWordWrap(True)
        self.lbl_preview_txt.setStyleSheet(
            "background:#F0F4FF; border:1px solid #C8D8F8; border-radius:5px; "
            "padding:6px; font-size:11px; color:#333;"
        )
        self.lbl_preview_txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(self.lbl_preview_txt)
        vl.addStretch()
        return grp

    # ── Lógica ────────────────────────────────────────────────────────────────
    def _on_modo(self):
        if self.rb_manual.isChecked():
            self.grp_serie.hide()
            self.grp_manual.show()
        else:
            self.grp_manual.hide()
            self.grp_serie.show()
        self._actualizar_preview()

    def _get_etiquetas(self):
        if self.rb_manual.isChecked():
            raw = self.txt_etiquetas.toPlainText().strip()
            return [l.strip() for l in raw.splitlines() if l.strip()]
        return self._calcular_serie()

    def _calcular_serie(self):
        try:
            pref = self._serie_vars["pref"].text().strip() or "A"
            n2i  = int(self._serie_vars["n2i"].text())
            n2f  = int(self._serie_vars["n2f"].text())
            n3i  = int(self._serie_vars["n3i"].text())
            n3f  = int(self._serie_vars["n3f"].text())
            n4i  = int(self._serie_vars["n4i"].text())
            n4f  = int(self._serie_vars["n4f"].text())
        except ValueError:
            return []
        return [
            f"{pref}.{n2}.{n3}.{n4}"
            for n2 in range(n2i, n2f + 1)
            for n3 in range(n3i, n3f + 1)
            for n4 in range(n4i, n4f + 1)
        ]

    def _generar_serie(self):
        lista = self._calcular_serie()
        self.txt_etiquetas.setPlainText("\n".join(lista))
        self._actualizar_preview()

    def _actualizar_preview(self):
        etiquetas = self._get_etiquetas()
        n = len(etiquetas)
        copias = self.sb_copias.value() if hasattr(self, "sb_copias") else 1
        fuente = self.cb_fuente.currentText() if hasattr(self, "cb_fuente") else "Arial"
        tam1 = self.sb_tam1.value() if hasattr(self, "sb_tam1") else 7
        tam2 = self.sb_tam2.value() if hasattr(self, "sb_tam2") else 14

        if n == 0:
            self.preview_widget.set_data("", fuente, tam1, tam2)
            self.lbl_preview_txt.setText("Sin etiquetas")
            self.lbl_count.setText("")
            return

        self.preview_widget.set_data(etiquetas[0], fuente, tam1, tam2)

        muestra = "  ·  ".join(etiquetas[:6])
        if n > 6:
            muestra += f"  … +{n-6} más"
        self.lbl_preview_txt.setText(muestra)

        total = n * copias
        self.lbl_count.setText(
            f"{n} etiqueta{'s' if n!=1 else ''}  ×  {copias} copia{'s' if copias!=1 else ''}  =  {total} páginas"
        )

    def _limpiar(self):
        self.txt_etiquetas.clear()
        self._actualizar_preview()

    def _datos_validos(self):
        et = self._get_etiquetas()
        if not et:
            QMessageBox.warning(self, "Sin datos", "No hay etiquetas para generar.")
            return None
        return et

    def _accion_pdf(self):
        etiquetas = self._datos_validos()
        if etiquetas is None:
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF", "etiquetas_ubicacion.pdf", "PDF (*.pdf)"
        )
        if not ruta:
            return
        self._generar_y_guardar(etiquetas, ruta, abrir=self.chk_abrir.isChecked())

    def _accion_imprimir(self):
        etiquetas = self._datos_validos()
        if etiquetas is None:
            return
        import tempfile
        tmp = tempfile.mktemp(suffix=".pdf")
        ok = self._generar_y_guardar(etiquetas, tmp, abrir=False, silencioso=True)
        if ok:
            try:
                imprimir_pdf_windows(tmp)
                self.status_bar.showMessage(
                    f"✔  Enviado a impresora: {len(etiquetas) * self.sb_copias.value()} páginas"
                )
            except Exception as ex:
                QMessageBox.critical(self, "Error de impresión", str(ex))

    def _generar_y_guardar(self, etiquetas, ruta, abrir=False, silencioso=False):
        copias = self.sb_copias.value()
        fuente = self.cb_fuente.currentText()
        tam1   = self.sb_tam1.value()
        tam2   = self.sb_tam2.value()
        total  = len(etiquetas) * copias
        try:
            self.status_bar.showMessage(f"Generando {total} páginas…")
            QApplication.processEvents()
            generar_pdf(etiquetas, ruta, copies=copias,
                        fuente=fuente, tam1=tam1, tam2=tam2)
            self._guardar_cfg()
            self.status_bar.showMessage(
                f"✔  PDF guardado: {os.path.basename(ruta)}  ({total} páginas)"
            )
            if not silencioso:
                QMessageBox.information(
                    self, "PDF generado",
                    f"Etiquetas: {len(etiquetas)}\n"
                    f"Copias c/u: {copias}\n"
                    f"Total páginas: {total}\n\n{ruta}"
                )
            if abrir:
                abrir_pdf(ruta)
            return True
        except Exception as ex:
            self.status_bar.showMessage("Error al generar el PDF.")
            QMessageBox.critical(self, "Error", str(ex))
            return False

    # ── Config ────────────────────────────────────────────────────────────────
    def _cargar_cfg_ui(self):
        cfg = self.cfg
        # Modo
        if cfg.get("modo") == "serie":
            self.rb_serie.setChecked(True)
            self._on_modo()
        else:
            self.rb_manual.setChecked(True)

        # Fuente
        idx = self.cb_fuente.findText(cfg.get("fuente", "Helvetica"))
        if idx >= 0:
            self.cb_fuente.setCurrentIndex(idx)

        self.sb_tam1.setValue(cfg.get("tam_linea1", 7))
        self.sb_tam2.setValue(cfg.get("tam_linea2", 14))
        self.sb_copias.setValue(cfg.get("copias", 1))
        self.chk_abrir.setChecked(cfg.get("abrir_pdf", True))

        # Serie
        for key, le in self._serie_vars.items():
            le.setText(cfg.get("serie", {}).get(key, DEFAULT_CFG["serie"][key]))

    def _guardar_cfg(self):
        cfg = {
            "fuente": self.cb_fuente.currentText(),
            "tam_linea1": self.sb_tam1.value(),
            "tam_linea2": self.sb_tam2.value(),
            "copias": self.sb_copias.value(),
            "abrir_pdf": self.chk_abrir.isChecked(),
            "modo": "serie" if self.rb_serie.isChecked() else "manual",
            "serie": {k: v.text() for k, v in self._serie_vars.items()},
        }
        guardar_cfg(cfg)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setWindowIcon(QIcon(resolver_ruta("icono.ico")))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())