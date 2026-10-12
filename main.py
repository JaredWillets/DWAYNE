import sys
import psutil
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QLineEdit, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from widgets import *

class DWAYNE(QWidget):
    def __init__(self):
        super().__init__()

        # Make window frameless, transparent, and attempt to keep it on bottom
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

        # Position window (x=20, y=20) and size
        self.move(20,20)
        # self.setGeometry(20, 20, 250, 100)
        #
        self.setStyleSheet("background-color: transparent;")

        self.v_layout = QVBoxLayout(self)

        self.githubGrid = GitHubWidget(self)
        self.v_layout.addWidget(self.githubGrid)

        # Add PayClockWidget
        self.payclock = PayClockWidget(self)
        self.v_layout.addWidget(self.payclock)

        self.labels = {
            "stats":QLabel(self),
            "workforce":QLabel(self)
        }

        for label in self.labels.values():
            self.v_layout.addWidget(label)

        self.labels["stats"].setFont(QFont("Courier", 11))
        self.labels["stats"].setStyleSheet("color: white; background: transparent;")
        self.update_loop()


        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(1000)

    def update_loop(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        net = psutil.net_io_counters()
        self.labels["stats"].setText(
            f"CPU: {cpu:.1f}%\nMem: {mem:.1f}%\n↑ {net.bytes_sent // 1024} KB\n↓ {net.bytes_recv // 1024} KB"
        )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()
        QApplication.quit()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    widget = DWAYNE()
    widget.show()

    # --- X11: Set window below all others (requires python-xlib) ---
    try:
        from Xlib import display, X, protocol
        from PyQt5.QtGui import QWindow
        # Get the X11 window id
        win_id = int(widget.winId())
        d = display.Display()
        root = d.screen().root
        NET_WM_STATE = d.intern_atom('_NET_WM_STATE')
        NET_WM_STATE_BELOW = d.intern_atom('_NET_WM_STATE_BELOW')
        ev = protocol.event.ClientMessage(
            window=win_id,
            client_type=NET_WM_STATE,
            data=(32, [1, NET_WM_STATE_BELOW, 0, 0, 0])
        )
        root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
        d.flush()
    except Exception as e:
        print(f"Could not set window below: {e}")
    # -------------------------------------------------------------

    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        sys.exit(0)
