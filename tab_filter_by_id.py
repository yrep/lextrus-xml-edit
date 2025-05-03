
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QFormLayout, QComboBox, QLineEdit, QHBoxLayout, \
    QPushButton, QFileDialog, QMessageBox, QInputDialog
from PySide6.QtCore import Qt


class TabFilterById(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create widgets for conditions
        self.condition_list = QListWidget()
        self.range_start_input = QLineEdit()
        self.range_end_input = QLineEdit()
        self.individual_ids_input = QLineEdit()
        self.range_button = QPushButton("Add Range Condition")
        self.range_button.setCursor(Qt.PointingHandCursor)
        self.individual_button = QPushButton("Add Individual IDs")
        self.individual_button.setCursor(Qt.PointingHandCursor)
        self.remove_button = QPushButton("Remove by Conditions")
        self.remove_button.setCursor(Qt.PointingHandCursor)
        self.remove_button.setStyleSheet("""
                                    QPushButton {
                                        background-color: #ff4c30;
                                        border: none; /* No border */
                                        color: white; /* White text */
                                        padding: 5px 8px; /* Padding around text */
                                        text-align: center; /* Center text */
                                        text-decoration: none; /* No underline */
                                        font-size: 16px; /* Font size */
                                        margin: 2px 1px; /* Margin around button */
                                    }
                                    QPushButton:hover {
                                        background-color: #96281b; /* Darker green on hover */
                                    }
                                """)
        self.preserve_button = QPushButton("Preserve by Conditions")
        self.preserve_button.setCursor(Qt.PointingHandCursor)
        self.preserve_button.setStyleSheet("""
                            QPushButton {
                                background-color: #4CAF50;
                                border: none; /* No border */
                                color: white; /* White text */
                                padding: 5px 8px; /* Padding around text */
                                text-align: center; /* Center text */
                                text-decoration: none; /* No underline */
                                font-size: 16px; /* Font size */
                                margin: 2px 1px; /* Margin around button */
                            }
                            QPushButton:hover {
                                background-color: #45a049; /* Darker green on hover */
                            }
                        """)
        self.clear_button = QPushButton("Clear Conditions")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.delete_button = QPushButton("Delete Condition")
        self.delete_button.setCursor(Qt.PointingHandCursor)

        # Layout for conditions
        form_layout = QFormLayout()
        form_layout.addRow("Range Start ID:", self.range_start_input)
        form_layout.addRow("Range End ID:", self.range_end_input)
        form_layout.addRow("Individual IDs (comma-separated):", self.individual_ids_input)
        form_layout.addRow("", self.range_button)
        form_layout.addRow("", self.individual_button)
        form_layout.addWidget(self.condition_list)
        form_layout.addRow("", self.remove_button)
        form_layout.addRow("", self.preserve_button)
        form_layout.addRow("", self.clear_button)
        form_layout.addRow("", self.delete_button)

        # Add widgets to layout
        layout.addLayout(form_layout)

        # Connect buttons to methods
        self.range_button.clicked.connect(self.add_range_condition)
        self.individual_button.clicked.connect(self.add_individual_ids_condition)
        self.remove_button.clicked.connect(self.remove_by_conditions)
        self.preserve_button.clicked.connect(self.preserve_by_conditions)
        self.clear_button.clicked.connect(self.clear_conditions)
        self.delete_button.clicked.connect(self.delete_condition)
        self.condition_list.itemDoubleClicked.connect(self.edit_condition)

        # Initialize conditions
        self.conditions = []

    def add_range_condition(self):
        start_id = self.range_start_input.text()
        end_id = self.range_end_input.text()
        if start_id and end_id:
            self.conditions.append(('range', int(start_id), int(end_id)))
            self.condition_list.addItem(f"Range: {start_id} - {end_id}")

    def add_individual_ids_condition(self):
        ids = self.individual_ids_input.text().split(',')
        ids = [int(id.strip()) for id in ids if id.strip().isdigit()]
        if ids:
            self.conditions.append(('individual', ids))
            self.condition_list.addItem(f"Individual IDs: {', '.join(map(str, ids))}")

    def filter_properties(self, preserve=False):
        root = self.parent.tree.topLevelItem(0)  # Get the root item
        ids_to_keep = set()

        # Determine IDs to keep based on conditions
        for condition in self.conditions:
            if condition[0] == 'range':
                start_id, end_id = condition[1], condition[2]
                ids_to_keep.update(range(start_id, end_id + 1))
            elif condition[0] == 'individual':
                ids_to_keep.update(condition[1])

        # Iterate over properties and remove or preserve them
        for i in range(root.childCount() - 1, -1, -1):  # Traverse in reverse order
            property_item = root.child(i)
            property_id = None

            # Find the 'id' child of the property
            for j in range(property_item.childCount()):
                child_item = property_item.child(j)
                if child_item.text(0) == 'id':
                    property_id = int(child_item.text(1))
                    break

            # Decide whether to keep or remove the property
            if preserve:
                if property_id not in ids_to_keep:
                    root.removeChild(property_item)
            else:
                if property_id in ids_to_keep:
                    root.removeChild(property_item)

            self.parent.state.set_property_count(self.parent.tree.count_properties())

    def remove_by_conditions(self):
        self.filter_properties(preserve=False)

    def preserve_by_conditions(self):
        self.filter_properties(preserve=True)

    def clear_conditions(self):
        self.conditions.clear()
        self.condition_list.clear()

    def delete_condition(self):
        current_row = self.condition_list.currentRow()
        if current_row >= 0:
            del self.conditions[current_row]
            self.condition_list.takeItem(current_row)

    def edit_condition(self, item):
        # Edit logic if needed
        pass