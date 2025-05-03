import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QLabel, QMenu, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSortFilterProxyModel
from lxml import etree
import csv
from collections import defaultdict, Counter

class XMLStatsApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('XML Stats Viewer')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Node", "Count"])
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree_widget)

        self.load_button = QPushButton("Load XML File")
        self.load_button.setCursor(Qt.PointingHandCursor)
        self.load_button.clicked.connect(self.load_xml_file)
        layout.addWidget(self.load_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.details_windows = []  # Keep references to details windows

        # Apply styles for a modern look
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTreeWidget, QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
            }
            QTreeWidget::item:selected, QTableWidget::item:selected {
                background-color: #0078d7;
                color: #ffffff;
            }
            QPushButton {
                background-color: #0078d7;
                color: #ffffff;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005ba1;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid #cccccc;
            }
            QLabel {
                padding: 5px;
            }
        """)

    def load_xml_file(self):
        options = QFileDialog.Option.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open XML File", "", "XML Files (*.xml);;All Files (*)", options=options
        )
        if file_path:
            self.progress_bar.setVisible(True)
            self.status_label.setText("Parsing XML file...")
            self.parse_thread = ParseXMLThread(file_path)
            self.parse_thread.progress.connect(self.update_progress)
            self.parse_thread.finished.connect(self.on_parse_finished)
            self.parse_thread.start()

    def update_progress(self, value, status):
        self.progress_bar.setValue(value)
        self.status_label.setText(status)

    def on_parse_finished(self, element_counts, root_tag):
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
        self.tree_widget.clear()
        self.build_tree(element_counts, root_tag)

    def build_tree(self, element_counts, root_tag):
        root_count = element_counts.get(root_tag, 0)
        root_item = QTreeWidgetItem([f"{root_tag} ({root_count})", str(root_count)])
        self.tree_widget.addTopLevelItem(root_item)
        self.add_children(root_item, root_tag, element_counts)

    def add_children(self, parent_item, parent_tag, element_counts):
        direct_children = defaultdict(int)
        
        # Calculate counts of direct children
        for tag in element_counts:
            if tag.startswith(f"{parent_tag}/"):
                parts = tag.split('/')
                if len(parts) > 1:
                    child_tag = parts[-1]
                    if tag.count('/') == parent_tag.count('/') + 1:
                        direct_children[child_tag] += element_counts[tag]

        for child_tag, count in direct_children.items():
            full_tag_path = f"{parent_tag}/{child_tag}"
            child_item = QTreeWidgetItem([f"{child_tag} ({count})", str(count)])
            parent_item.addChild(child_item)
            # Recursively add children of the current child
            self.add_children(child_item, full_tag_path, element_counts)

    def show_context_menu(self, position):
        selected_item = self.tree_widget.itemAt(position)
        if selected_item:
            node_tag = selected_item.text(0).split(' (')[0]
            menu = QMenu()
            details_action = menu.addAction("View Details")
            action = menu.exec(self.tree_widget.viewport().mapToGlobal(position))
            if action == details_action:
                self.show_details(node_tag)

    def show_details(self, node_tag):
        details_window = DetailsWindow(node_tag, self.parse_thread.all_values)
        self.details_windows.append(details_window)  # Keep a reference to the window
        details_window.show()


class ParseXMLThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object, str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.all_values = defaultdict(list)

    def run(self):
        tree = etree.parse(self.file_path)
        root = tree.getroot()
        element_counts = Counter()
        self.process_element(root, element_counts, "", 0, 100)
        self.finished.emit(element_counts, root.tag)

    def process_element(self, element, element_counts, path, current_progress, max_progress):
        path = f"{path}/{element.tag}" if path else element.tag
        element_counts[path] += 1
        if element.text and element.text.strip():
            self.all_values[element.tag].append(element.text.strip())
        step = max_progress // (len(element) + 1)
        for i, child in enumerate(element):
            self.process_element(child, element_counts, path, current_progress + step * (i + 1), max_progress)
        self.progress.emit(max_progress, f"Finished processing {element.tag}")


class DetailsWindow(QMainWindow):
    def __init__(self, node_name, all_values):
        super().__init__()
        self.setWindowTitle('Node Details')
        self.setGeometry(150, 150, 600, 400)
        self.node_name = node_name
        self.all_values = all_values

        layout = QVBoxLayout()
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Value", "Encountered Times"])
        self.table_widget.setSortingEnabled(True)
        layout.addWidget(self.table_widget)

        self.save_button = QPushButton("Save as CSV")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_as_csv)
        layout.addWidget(self.save_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.load_details()

    def load_details(self):
        values = self.all_values[self.node_name]
        unique_values = set(values)
        details = [{'id': i + 1, 'value': val, 'count': values.count(val)} for i, val in enumerate(unique_values)]

        self.table_widget.setRowCount(len(details))
        for i, detail in enumerate(details):
            self.table_widget.setItem(i, 0, QTableWidgetItem(str(detail['id'])))
            self.table_widget.setItem(i, 1, QTableWidgetItem(detail['value']))
            self.table_widget.setItem(i, 2, QTableWidgetItem(str(detail['count'])))

        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def save_as_csv(self):
        options = QFileDialog.Option.DontUseNativeDialog
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options
            )
            if file_path:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["ID", "Value", "Encountered Times"])
                    for row in range(self.table_widget.rowCount()):
                        writer.writerow([
                            self.table_widget.item(row, 0).text(),
                            self.table_widget.item(row, 1).text(),
                            self.table_widget.item(row, 2).text()
                        ])
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = XMLStatsApp()
    main_win.show()
    sys.exit(app.exec())
