from PySide6.QtWidgets import QStatusBar, QLabel, QProgressBar, QHBoxLayout, QWidget, QSizePolicy
from PySide6.QtCore import QTimer


class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create and configure the progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedWidth(200)  # Fixed width for the progress bar
        # self.progress_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.progress_bar.setVisible(False)

        # Create and configure the status message label
        self.label_properties_count = QLabel("Properties: 0")
        self.status_message = QLabel()
        # self.status_message.setSizePolicy(self.status_message.sizePolicy().expand(), self.status_message.sizePolicy().expand())
        self.status_message.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self.status_message.setStyleSheet("background-color: #4d9ee9;")

        # Add widgets to the status bar
        self.addWidget(self.label_properties_count)
        self.addWidget(self.progress_bar)
        self.addWidget(self.status_message)

        # Add a permanent widget to push other widgets to the left
        self.addPermanentWidget(QWidget())  # Spacer to push widgets to the left

        self.setStyleSheet("""
                        QStatusBar {
                            
                        }
                        QProgressBar {
                            border-radius: 7px;
                            background: #bbc9d5;
                            text-align: center;
                        }
                        QProgressBar::chunk {
                            background: #4daeff;
                        }
                    """)

    def update_property_count_label(self, value: int):
        self.label_properties_count.setText(f"Properties: {str(value)}")

    def show_message(self, message):
        self.status_message.setText(message)

    def show_message_timeout(self, message, timeout=2000):
        self.status_message.setText(message)
        QTimer.singleShot(timeout, lambda: self.status_message.clear())

    def start_progress(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

    def update_progress(self, value):
        new_value = self.progress_bar.value() + value
        if new_value >= 100:
            new_value = 100
        self.progress_bar.setValue(new_value)

    def stop_progress(self):
        self.progress_bar.setVisible(False)
        self.status_message.setText("Operation completed")

