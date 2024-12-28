import sys
import os
import psutil
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QTextEdit, QLineEdit, QTreeView, QFileSystemModel, QPushButton, QGridLayout
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeyEvent


class DraggableLineEdit(QLineEdit):
    def __init__(self, parent=None, system_monitor=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.system_monitor = system_monitor  # SystemMonitorへの参照

    def keyPressEvent(self, event):
        key_text = event.text().upper()
        if key_text.isalpha() and self.system_monitor:  # 英字キーのみ処理
            self.system_monitor.highlight_key(key_text)
        super().keyPressEvent(event)


class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Termy")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black; color: #ffa500;")
        self.current_path = os.getcwd()
        self.key_buttons = {}  # 仮想キーボードのボタンマッピング
        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左側: ターミナル
        left_layout = QVBoxLayout()
        self.sys_info_label = QLabel(self)
        self.sys_info_label.setStyleSheet("color: #ffa500; font-size: 18px;")
        self.sys_info_label.setAlignment(Qt.AlignLeft)
        left_layout.addWidget(self.sys_info_label)

        self.terminal_output = QTextEdit(self)
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("""
            background-color: black;
            color: #ffa500;
            font-family: 'Courier New';
            font-size: 14px;
            border: 1px solid #ffa500;
        """)
        left_layout.addWidget(self.terminal_output)

        # 入力エリア
        input_layout = QHBoxLayout()
        self.prompt_label = QLabel(f"{self.current_path} $", self)  # 現在のパスを表示
        self.prompt_label.setStyleSheet("color: #ffa500; font-family: 'Courier New'; font-size: 14px;")
        input_layout.addWidget(self.prompt_label)

        self.terminal_input = DraggableLineEdit(self, system_monitor=self)
        self.terminal_input.setStyleSheet("""
            background-color: black;
            color: #ffa500;
            font-family: 'Courier New';
            font-size: 14px;
            border: 1px solid #ffa500;
            padding: 5px;
        """)
        self.terminal_input.returnPressed.connect(self.handle_input)
        input_layout.addWidget(self.terminal_input)
        left_layout.addLayout(input_layout)

        main_layout.addLayout(left_layout, 2)

        # 右側: ファイルエクスプローラー + キーボード
        right_layout = QVBoxLayout()

        # ファイルエクスプローラー
        self.file_system_model = QFileSystemModel()
        self.file_system_model.setRootPath('')
        self.file_system_view = QTreeView(self)
        self.file_system_view.setModel(self.file_system_model)
        self.file_system_view.setRootIndex(self.file_system_model.index('PC'))
        self.file_system_view.setStyleSheet("""
            QTreeView {
                background-color: black;
                color: #ffa500;
                border: 1px solid #ffa500;
                font-family: 'Courier New';
                spacing: 10px;
            }
            QTreeView::item:selected {
                background-color: #ff6a00;
                color: black;
            }
        """)
        right_layout.addWidget(self.file_system_view, 3)

        # 仮想キーボード
        self.keyboard_layout = QGridLayout()
        self.add_virtual_keyboard()
        keyboard_widget = QWidget()
        keyboard_widget.setLayout(self.keyboard_layout)
        keyboard_widget.setStyleSheet("background-color: black;")
        right_layout.addWidget(keyboard_widget, 2)

        main_layout.addLayout(right_layout, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(1000)

    def add_virtual_keyboard(self):
        keys = [
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        for row_idx, row in enumerate(keys):
            for col_idx, key in enumerate(row):
                button = QPushButton(key)
                button.setFixedSize(60, 60)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #333;
                        color: #ffa500;
                        border-radius: 10px;
                        border: 2px solid #ffa500;
                        font-family: 'Courier New';
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)
                self.keyboard_layout.addWidget(button, row_idx, col_idx)
                self.key_buttons[key] = button

    def highlight_key(self, key):
        if key in self.key_buttons:
            button = self.key_buttons[key]
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ff6a00;
                    color: black;
                    border-radius: 10px;
                    border: 2px solid #ffa500;
                    font-family: 'Courier New';
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
            QTimer.singleShot(200, lambda: button.setStyleSheet("""
                QPushButton {
                    background-color: #333;
                    color: #ffa500;
                    border-radius: 10px;
                    border: 2px solid #ffa500;
                    font-family: 'Courier New';
                    font-size: 18px;
                    font-weight: bold;
                }
            """))

    def update_system_info(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        info_text = (
            f"CPU Usage: {cpu_usage}% | "
            f"Memory: {memory.used / (1024 ** 3):.2f}GB/{memory.total / (1024 ** 3):.2f}GB"
        )
        self.sys_info_label.setText(info_text)

    def handle_input(self):
        command = self.terminal_input.text()
        self.terminal_input.clear()
        if command.strip():
            self.log_message(f"$ {command}")
            self.execute_command(command)

    def execute_command(self, command):
        if command.startswith("cd "):
            new_dir = command[3:].strip()
            if os.path.isdir(new_dir):
                self.current_path = new_dir
                os.chdir(new_dir)
                self.prompt_label.setText(f"{self.current_path} $")
            else:
                self.log_message(f"Error: {new_dir} is not a valid directory.")
        else:
            try:
                result = subprocess.run(
                    command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                if result.stdout.strip():
                    self.log_message(result.stdout.strip())
                if result.stderr.strip():
                    self.log_message(f"Error: {result.stderr.strip()}")
            except Exception as e:
                self.log_message(f"Command failed: {str(e)}")

    def log_message(self, message):
        self.terminal_output.append(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())
