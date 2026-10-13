import os
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"
import sys
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from widgets import *

class DWAYNE(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        self.setFocusPolicy(Qt.StrongFocus)

        self.move(20,20)
        
        self.setStyleSheet("background-color: red;")

        self.v_layout = QVBoxLayout(self)

        self.githubGrid = GitHubWidget(self)
        self.v_layout.addWidget(self.githubGrid)


        self.labels = {
            "stats":QLabel(self),
            "workforce":QLabel(self)
        }

        for label in self.labels.values():
            self.v_layout.addWidget(label)

        self.labels["stats"].setFont(QFont("Courier", 11))
        self.labels["stats"].setStyleSheet("color: white; background: transparent;")


    def keyPressEvent(self, event):
        print(event)
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        print("DWAYNE received focus")
        super().focusInEvent(event)

    def mousePressEvent(self, event):
        print("Mouse pressed")
        self.activateWindow()
        self.setFocus(Qt.MouseFocusReason)
        super().mousePressEvent(event)

    def closeEvent(self, event):
        event.accept()
        QApplication.quit()

from Xlib import display, X, protocol

def set_window_below(widget):
    d = display.Display()

    window = d.create_resource_object(
        "window",
        int(widget.winId())
    )

    root = d.screen().root

    state = d.intern_atom("_NET_WM_STATE")
    below = d.intern_atom("_NET_WM_STATE_BELOW")

    event = protocol.event.ClientMessage(
        window=window,
        client_type=state,
        data=(32, [
            1,
            below,
            0,
            1,
            0
        ])
    )

    root.send_event(
        event,
        event_mask=(
            X.SubstructureRedirectMask |
            X.SubstructureNotifyMask
        )
    )

    d.flush()
    d.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DWAYNE()
    widget.show()
    set_window_below(widget)

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        sys.exit(0)
