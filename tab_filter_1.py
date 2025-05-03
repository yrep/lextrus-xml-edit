from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QFormLayout, QLineEdit, QPushButton, QTreeWidgetItem
from PySide6.QtCore import Qt

class TabFilterById(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a new QTreeWidget for demonstration
        self.tree_widget = parent.tree
        self.tree_widget.setHeaderLabels(["ID", "Detail"])

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
        self.preserve_button = QPushButton("Preserve by Conditions")
        self.preserve_button.setCursor(Qt.PointingHandCursor)
        
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

        # Add widgets to layout
        layout.addWidget(self.tree_widget)
        layout.addLayout(form_layout)

        # Connect buttons to methods
        self.range_button.clicked.connect(self.add_range_condition)
        self.individual_button.clicked.connect(self.add_individual_ids_condition)
        self.remove_button.clicked.connect(self.remove_by_conditions)
        self.preserve_button.clicked.connect(self.preserve_by_conditions)

    def add_range_condition(self):
        start_id = self.range_start_input.text()
        end_id = self.range_end_input.text()
        if start_id.isdigit() and end_id.isdigit():
            condition = f"Range: {start_id} - {end_id}"
            self.condition_list.addItem(condition)

    def add_individual_ids_condition(self):
        ids = self.individual_ids_input.text()
        ids_list = ids.split(',')
        ids_list = [id.strip() for id in ids_list if id.strip().isdigit()]
        if ids_list:
            condition = f"IDs: {', '.join(ids_list)}"
            self.condition_list.addItem(condition)

    def remove_by_conditions(self):
        conditions = [self.condition_list.item(i).text() for i in range(self.condition_list.count())]
        ids_to_remove = set()

        for condition in conditions:
            if condition.startswith("Range:"):
                start_id, end_id = map(int, condition.split(':')[1].strip().split(' - '))
                ids_to_remove.update(range(start_id, end_id + 1))
            elif condition.startswith("IDs:"):
                ids = map(int, condition.split(':')[1].strip().split(','))
                ids_to_remove.update(ids)

        self.filter_tree(ids_to_remove, remove=True)

    def preserve_by_conditions(self):
        conditions = [self.condition_list.item(i).text() for i in range(self.condition_list.count())]
        ids_to_preserve = set()

        for condition in conditions:
            if condition.startswith("Range:"):
                start_id, end_id = map(int, condition.split(':')[1].strip().split(' - '))
                ids_to_preserve.update(range(start_id, end_id + 1))
            elif condition.startswith("IDs:"):
                ids = map(int, condition.split(':')[1].strip().split(','))
                ids_to_preserve.update(ids)

        self.filter_tree(ids_to_preserve, remove=False)

    def filter_tree(self, ids_set, remove):
        items_to_check = [self.tree_widget.topLevelItem(i) for i in range(self.tree_widget.topLevelItemCount())]
        for item in items_to_check:
            self.check_item(item, ids_set, remove)

    def check_item(self, item, ids_set, remove):
        if not item:
            return

        items_to_check = [item.child(i) for i in range(item.childCount())]
        for child_item in items_to_check:
            if child_item:
                # Assuming the ID is always in the second column (index 1)
                try:
                    item_id = int(child_item.text(1))
                    if (remove and item_id in ids_set) or (not remove and item_id not in ids_set):
                        item.removeChild(child_item)
                except ValueError:
                    # Handle any conversion errors gracefully
                    continue

        # Recursive check for child items
        for i in range(item.childCount()):
            self.check_item(item.child(i), ids_set, remove)
