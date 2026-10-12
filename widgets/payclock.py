import yaml
import os
import time
import csv
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QDialog, QDialogButtonBox, QTimeEdit
from PyQt5.QtCore import QTimer, QTime, QDate

SESSION_FILE = 'payclock_sessions.csv'

class TimeSelectDialog(QDialog):
    def __init__(self, label, default_time=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(label)
        layout = QVBoxLayout(self)
        self.time_edit = QTimeEdit(self)
        self.time_edit.setDisplayFormat('HH:mm:ss')
        if default_time:
            self.time_edit.setTime(default_time)
        else:
            self.time_edit.setTime(QTime.currentTime())
        layout.addWidget(self.time_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    def get_time(self):
        return self.time_edit.time()

class PayClockWidget(QWidget):
    def __init__(self, parent=None, config_path='config.yaml'):
        super().__init__(parent)
        self.config = self.load_config(config_path)
        self.pay_rate = self.config.get('pay_rate', 20.0)
        self.tax_factor = self.config.get('tax_factor', 1.0)
        self.is_clocked_in = False
        self.is_on_break = False
        self.current_session_start = None
        self.sessions = []  # List of (start, end) tuples for today
        self.current_day = QDate.currentDate().toString('yyyy-MM-dd')
        self.load_sessions_for_today()

        self.layout = QVBoxLayout(self)
        self.status_label = QLabel("Not clocked in.")
        self.money_label = QLabel("")
        self.button = QPushButton("Clock In")
        self.button.clicked.connect(self.toggle_clock)
        self.break_button = QPushButton("Start Break")
        self.break_button.clicked.connect(self.toggle_break)
        self.break_button.setEnabled(False)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.money_label)
        self.layout.addWidget(self.button)
        self.layout.addWidget(self.break_button)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_money)
        self.timer.start(100)

    def load_config(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}

    def session_file_path(self):
        # Save in the same directory as config if possible
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', SESSION_FILE)

    def save_clock_event(self, event_type, timestamp):
        path = self.session_file_path()
        with open(path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self.current_day, event_type, int(timestamp)])

    def save_session(self, start, end):
        path = self.session_file_path()
        with open(path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self.current_day, int(start), int(end)])

    def load_sessions_for_today(self):
        self.sessions = []
        path = self.session_file_path()
        if not os.path.exists(path):
            return
        today = QDate.currentDate().toString('yyyy-MM-dd')
        with open(path, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 3 and row[0] == today:
                    # Support both old (start, end) and new (type, timestamp) formats
                    if row[1] in ('in', 'out'):
                        continue  # Don't add to sessions, but could be used for audit
                    try:
                        start = float(row[1])
                        end = float(row[2])
                        self.sessions.append((start, end))
                    except Exception:
                        continue

    def select_time(self, label, default_time=None):
        dialog = TimeSelectDialog(label, default_time, self)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_time()
        return None

    def reset_if_new_day(self):
        today = QDate.currentDate().toString('yyyy-MM-dd')
        if today != self.current_day:
            self.sessions = []
            self.current_day = today
            self.load_sessions_for_today()

    def toggle_clock(self):
        self.reset_if_new_day()
        if not self.is_clocked_in:
            # Clocking in: ask for start time
            now = QTime.currentTime()
            selected_time = self.select_time("Select clock-in time", now)
            if selected_time is None:
                return  # Cancelled
            t = time.localtime()
            start_struct = time.struct_time((t.tm_year, t.tm_mon, t.tm_mday,
                                             selected_time.hour(), selected_time.minute(), selected_time.second(),
                                             t.tm_wday, t.tm_yday, t.tm_isdst))
            self.current_session_start = time.mktime(start_struct)
            self.save_clock_event('in', self.current_session_start)
            self.is_clocked_in = True
            self.is_on_break = False
            self.status_label.setText(f"Clocked in at {selected_time.toString('HH:mm:ss')}")
            self.button.setText("Clock Out")
            self.break_button.setEnabled(True)
        else:
            # Clocking out: ask for end time
            now = QTime.currentTime()
            selected_time = self.select_time("Select clock-out time", now)
            if selected_time is None:
                return  # Cancelled
            t = time.localtime()
            end_struct = time.struct_time((t.tm_year, t.tm_mon, t.tm_mday,
                                           selected_time.hour(), selected_time.minute(), selected_time.second(),
                                           t.tm_wday, t.tm_yday, t.tm_isdst))
            end_time = time.mktime(end_struct)
            if self.current_session_start:
                self.sessions.append((self.current_session_start, end_time))
                self.save_session(self.current_session_start, end_time)
                self.save_clock_event('out', end_time)
            self.current_session_start = None
            self.is_clocked_in = False
            self.is_on_break = False
            self.status_label.setText(f"Clocked out at {selected_time.toString('HH:mm:ss')}")
            self.button.setText("Clock In")
            self.break_button.setEnabled(False)

    def toggle_break(self):
        if not self.is_clocked_in:
            return
        if not self.is_on_break:
            # Start break
            now = QTime.currentTime()
            selected_time = self.select_time("Select break start time", now)
            if selected_time is None:
                return  # Cancelled
            t = time.localtime()
            break_start_struct = time.struct_time((t.tm_year, t.tm_mon, t.tm_mday,
                                                   selected_time.hour(), selected_time.minute(), selected_time.second(),
                                                   t.tm_wday, t.tm_yday, t.tm_isdst))
            break_start_time = time.mktime(break_start_struct)
            if self.current_session_start:
                self.sessions.append((self.current_session_start, break_start_time))
                self.save_session(self.current_session_start, break_start_time)
                self.save_clock_event('out', break_start_time)
            self.current_session_start = None
            self.is_on_break = True
            self.status_label.setText(f"On break since {selected_time.toString('HH:mm:ss')}")
            self.break_button.setText("End Break")
            self.button.setEnabled(False)
        else:
            # End break
            now = QTime.currentTime()
            selected_time = self.select_time("Select break end time", now)
            if selected_time is None:
                return  # Cancelled
            t = time.localtime()
            break_end_struct = time.struct_time((t.tm_year, t.tm_mon, t.tm_mday,
                                                 selected_time.hour(), selected_time.minute(), selected_time.second(),
                                                 t.tm_wday, t.tm_yday, t.tm_isdst))
            break_end_time = time.mktime(break_end_struct)
            self.save_clock_event('in', break_end_time)
            self.current_session_start = break_end_time
            self.is_on_break = False
            self.status_label.setText(f"Back from break at {selected_time.toString('HH:mm:ss')}")
            self.break_button.setText("Start Break")
            self.button.setEnabled(True)

    def get_today_seconds(self):
        total = 0.0
        for start, end in self.sessions:
            total += max(0, end - start)
        if self.is_clocked_in and self.current_session_start and not self.is_on_break:
            total += time.time() - self.current_session_start
        return total

    def update_money(self):
        self.reset_if_new_day()
        total_seconds = self.get_today_seconds()
        hours = total_seconds / 3600
        gross = hours * self.pay_rate
        net = gross * self.tax_factor if self.tax_factor else gross
        self.money_label.setText(f"Today's Hours: {hours:.2f}\nGross: ${gross:.2f}\nNet: ${net:.2f}") 