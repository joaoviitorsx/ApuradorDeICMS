from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QGraphicsOpacityEffect
from PySide6.QtGui import QPixmap, QCursor, QFont, QColor, QIcon
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, QSize

class RoundedIconButton(QPushButton):
    def __init__(self, icon_path, color="#E53935", hover_color="#C62828", size=36, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(size // 2, size // 2))
        self.color = QColor(color)
        self.hover_color = QColor(hover_color)
        self._set_stylesheet(color, hover_color, size)

    def _set_stylesheet(self, color, hover_color, size):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border-radius: {size // 2}px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)

class AnimatedCard(QFrame):
    clicked = Signal()

    def __init__(self, icon_path, title, description_list, accent_color="#E53935", parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 280)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.accent_color = accent_color
        self._setup_ui(icon_path, title, description_list)
        self._setup_animations()

    def _setup_ui(self, icon_path, title, description_list):
        self.setStyleSheet(self._get_default_stylesheet())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 22, 25, 22)
        layout.setSpacing(15)

        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)

        icon_container = QFrame()
        icon_container.setFixedSize(80, 80)
        icon_container.setStyleSheet("background-color: #c7c7c7; border-radius: 40px;")
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title_label.setStyleSheet("color: white;")

        desc_label = QLabel(self._format_description(description_list))
        desc_label.setStyleSheet("font-size: 13px;")
        desc_label.setTextFormat(Qt.RichText)
        desc_label.setWordWrap(True)

        button = QPushButton("Acessar")
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(self._get_button_stylesheet())
        button.clicked.connect(self.clicked.emit)

        header_layout = QHBoxLayout()
        header_layout.addWidget(icon_container)
        header_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addStretch()
        layout.addWidget(button)

        self._icon_label = icon_label
        self._icon_container = icon_container
        self._title_label = title_label
        self._desc_label = desc_label
        self._button = button
        self._layout = layout

    def _setup_animations(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(600)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._hover_offset = 5
        self._is_hovered = False

    def _get_default_stylesheet(self):
        return f"""
            AnimatedCard {{
                background-color: #212121;
                border: 1px solid #2e2e2e;
                border-radius: 12px;
            }}
        """

    def _get_hover_stylesheet(self):
        return f"""
            AnimatedCard {{
                background-color: #212121;
                border: 1px solid {self.accent_color};
                border-radius: 12px;
            }}
        """

    def _get_button_stylesheet(self):
        return f"""
            QPushButton {{
                background-color: {self.accent_color};
                color: white;
                padding: 12px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(self.accent_color)};
            }}
        """

    def _format_description(self, description_list):
        desc_text = "<ul style='margin: 0; padding-left: 18px;'>"
        for item in description_list:
            desc_text += f"<li style='margin-bottom: 6px; color: #bbbbbb;'>{item}</li>"
        desc_text += "</ul>"
        return desc_text

    def _darken_color(self, color_hex):
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        color.setHsv(h, s, max(0, v - 20), a)
        return color.name()

    def enterEvent(self, event):
        if not self._is_hovered:
            self.setStyleSheet(self._get_hover_stylesheet())
            rect = self.geometry()
            self.hover_animation.stop()
            self.hover_animation.setStartValue(rect)
            self.hover_animation.setEndValue(QRect(rect.x(), rect.y() - self._hover_offset, rect.width(), rect.height()))
            self.hover_animation.start()
            self._is_hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._is_hovered:
            self.setStyleSheet(self._get_default_stylesheet())
            rect = self.geometry()
            self.hover_animation.stop()
            self.hover_animation.setStartValue(rect)
            self.hover_animation.setEndValue(QRect(rect.x(), rect.y() + self._hover_offset, rect.width(), rect.height()))
            self.hover_animation.start()
            self._is_hovered = False
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

