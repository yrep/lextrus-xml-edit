from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QPushButton, QDialogButtonBox
from PySide6.QtCore import Qt


class TrimTreeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Trim Properties Tree")

        # Layout for the dialog
        layout = QVBoxLayout(self)

        # Number of items input
        self.number_label = QLabel("Number of properties:")
        self.number_input = QLineEdit()
        layout.addWidget(self.number_label)
        layout.addWidget(self.number_input)

        # Radio buttons for "Start" or "End"
        self.start_radio = QRadioButton("Start")
        self.end_radio = QRadioButton("End")
        self.start_radio.setChecked(True)  # Default to "Start"

        radio_layout = QHBoxLayout()
        radio_layout.addWidget(self.start_radio)
        radio_layout.addWidget(self.end_radio)

        layout.addWidget(QLabel("Select position:"))
        layout.addLayout(radio_layout)

        # Action buttons for Remove, Preserve, and Cancel
        self.remove_button = QPushButton("Remove")
        self.preserve_button = QPushButton("Preserve")
        self.cancel_button = QPushButton("Cancel")

        # Button Layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.preserve_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect buttons to respective actions
        self.remove_button.clicked.connect(self.remove_action)
        self.preserve_button.clicked.connect(self.preserve_action)
        self.cancel_button.clicked.connect(self.reject)  # Cancel button closes the dialog

        self.action = None  # Default action, will be set based on user's choice
        self.trim_position = "start"  # Default to "start"

    def remove_action(self):
        self.action = "remove"
        self.accept()

    def preserve_action(self):
        self.action = "preserve"
        self.accept()

    def get_inputs(self):
        number = 0
        try:
            number = int(self.number_input.text())
            if number <= 0:
                raise ValueError("Enter a positive number.")
        except ValueError:
            self.number_input.setText("Invalid input")
            return None, None, None  # Invalid input case

        # Get the position (start or end)
        trim_position = "start" if self.start_radio.isChecked() else "end"
        return number, self.action, trim_position
