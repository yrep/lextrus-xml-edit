import json

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QFormLayout, QComboBox, QLineEdit, QHBoxLayout, \
    QPushButton, QFileDialog, QMessageBox
from PySide6.QtCore import Qt


class TabGroupActions(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.actions = []
        self.parent = parent

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.actions_list = QListWidget()
        layout.addWidget(self.actions_list)

        # Form for action configuration
        self.form_layout = QFormLayout()
        layout.addLayout(self.form_layout)

        self.action_select = QComboBox()
        self.action_select.addItems(["add_node_type", "remove_node_by_condition", "modify_node_type"])
        self.form_layout.addRow("Select action:", self.action_select)

        self.action_select.currentIndexChanged.connect(self.on_action_select_index_changed)

        self.parent_node = QComboBox()
        # self.parent_node.addItems(list(self.tree_window.tree_widget.node_types_array))
        self.parent_node.addItems(["property"])
        self.form_layout.addRow("Parent node:", self.parent_node)

        self.child_node = QLineEdit()
        if self.action_select.currentIndex() == 0:
            self.child_node.setPlaceholderText("Enter new node name")
        self.form_layout.addRow("Child node:", self.child_node)

        self.condition = QComboBox()
        self.condition.addItems(["", "equal", "contains", "does not contain"])
        self.form_layout.addRow("Value comparison condition:", self.condition)

        self.node_value = QLineEdit()
        self.node_value.setPlaceholderText("Enter value")
        self.form_layout.addRow("Node value:", self.node_value)

        self.new_value = QLineEdit()
        self.new_value.setPlaceholderText("Enter new value")
        self.form_layout.addRow("New value:", self.new_value)


        # Buttons

        all_buttons_layout = QVBoxLayout()
        layout.addLayout(all_buttons_layout)

        button_layout = QHBoxLayout()
        all_buttons_layout.addLayout(button_layout)

        self.add_action_button = QPushButton("Add Action")
        self.add_action_button.setCursor(Qt.PointingHandCursor)
        self.add_action_button.clicked.connect(self.add_action_to_list)
        button_layout.addWidget(self.add_action_button)

        self.remove_action_button = QPushButton("Remove Selected Action")
        self.remove_action_button.setCursor(Qt.PointingHandCursor)
        self.remove_action_button.clicked.connect(self.remove_action_from_list)
        button_layout.addWidget(self.remove_action_button)

        self.execute_actions_button = QPushButton("Execute Actions")
        self.execute_actions_button.setCursor(Qt.PointingHandCursor)
        self.execute_actions_button.clicked.connect(self.execute_actions)
        self.execute_actions_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        border: none; /* No border */
                        color: white; /* White text */
                        padding: 5px 8px; /* Padding around text */
                        text-align: center; /* Center text */
                        text-decoration: none; /* No underline */
                        font-size: 16px; /* Font size */
                        margin: 2px 1px; /* Margin around button */
                        border-radius: 6px; /* Rounded corners */
                    }
                    QPushButton:hover {
                        background-color: #45a049; /* Darker green on hover */
                    }
                """)
        button_layout.addWidget(self.execute_actions_button)

        load_save_buttons_layout = QHBoxLayout()
        all_buttons_layout.addLayout(load_save_buttons_layout)

        self.save_actions_button = QPushButton("Save Actions")
        self.save_actions_button.setCursor(Qt.PointingHandCursor)
        self.save_actions_button.clicked.connect(self.save_actions)
        load_save_buttons_layout.addWidget(self.save_actions_button)

        self.load_actions_button = QPushButton("Load Actions")
        self.load_actions_button.setCursor(Qt.PointingHandCursor)
        self.load_actions_button.setStyleSheet("""
                                        QPushButton {
                                            background-color: #f9bf3b;
                                            border: none; /* No border */
                                            color: white; /* White text */
                                            padding: 5px 8px; /* Padding around text */
                                            text-align: center; /* Center text */
                                            text-decoration: none; /* No underline */
                                            font-size: 16px; /* Font size */
                                            margin: 2px 1px; /* Margin around button */
                                        }
                                        QPushButton:hover {
                                            background-color: #f39c12; /* Darker green on hover */
                                        }
                                    """)
        self.load_actions_button.clicked.connect(self.load_actions)
        load_save_buttons_layout.addWidget(self.load_actions_button)

        # self.action_select.currentIndexChanged.connect(self.update_node_type_list)

    def save_actions(self):
        if len(self.actions) > 0:
            options = QFileDialog.Option.DontUseNativeDialog
            file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "./config/", "JSON Files (*.json);;All Files (*)",
                                                       options=options)
            if file_name:
                try:
                    with open(file_name, 'w') as file:
                        for item in self.actions:
                            json.dump(item, file)
                            file.write('\n')
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"An error occurred while saving data: {e}")
        else:
            QMessageBox.information(self, "Error", "Nothing to save.")

    def load_actions(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "./config/", "JSON Files (*.json);;All Files (*)",
                                                   options=options)
        if file_name:
            try:
                with open(file_name, 'r') as file:
                    self.actions = [json.loads(line.strip()) for line in file]
                self.update_list_view()
                QMessageBox.information(self, "Success", "Data loaded successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred while loading data: {e}")

    def update_list_view(self):
        self.actions_list.clear()
        for item in self.actions:
            self.actions_list.addItem(
                f"{item["action"]} Parent: {item["parent"]}, Child: {item["child"]}, Value: {item["value"]}, Condition: {item["condition"]}, New value: {item["new_value"]}")

    def on_action_select_index_changed(self, index):
        # Get the text of the selected item
        if self.action_select.currentIndex() != 0:
            self.child_node.setPlaceholderText("Enter child node name")

        # METHODS
    def add_action_to_list(self):
        action = self.action_select.currentText()
        parent_node = self.parent_node.currentText()
        child_node = self.child_node.text()
        node_value = self.node_value.text()
        condition = self.condition.currentText()
        new_value = self.new_value.text()

        action_item = {
            "action": action,
            "parent": parent_node,
            "child": child_node,
            "value": node_value,
            "condition": condition,
            "new_value": new_value
        }

        self.actions.append(action_item)
        self.actions_list.addItem(
            f"{action.capitalize()} Parent: {parent_node}, Child: {child_node}, Value: {node_value}, Condition: {condition}, New value: {new_value}")
        #

    def remove_action_from_list(self):
        selected_items = self.actions_list.selectedItems()
        for item in selected_items:
            index = self.actions_list.row(item)
            self.actions.pop(index)
            self.actions_list.takeItem(index)

    def execute_actions(self):
        if len(self.actions) > 0:
            self.parent.start_actions(self.actions)
        else:
            QMessageBox.information(self, "Error", "Nothing to execute.")





