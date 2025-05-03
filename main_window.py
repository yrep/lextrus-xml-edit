from datetime import datetime
import json
import os
import sys
import time
from configparser import ConfigParser

import requests
from PySide6.QtCore import Qt, QThread, Slot, Signal, QTimer
from PySide6.QtWidgets import QMainWindow, QFileDialog, QHBoxLayout, QWidget, QMessageBox, QTabWidget, QSplitter, \
    QInputDialog, QTreeWidgetItem, QProgressDialog, QLabel, QVBoxLayout, QDialog
from PySide6.QtGui import QIcon, QAction, QPainter, QColor

from app_state import AppState
from main_menu import MainMenu
from sidebar import Sidebar
from statusbar import StatusBar
from tab_check_media_links import TabCheckMediaLinks
from tab_filter_by_id import TabFilterById
from tab_group_actions import TabGroupActions
from tab_scraping import TabScraping
from tree import TreeWidget
from trim_dialog import TrimTreeDialog
from worker import Worker


class LoadingAnimation(QLabel):
    def __init__(self):
        super().__init__()
        self.circles = [0, 0, 0]  # Sizes of the circles
        self.current_circle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.setFixedSize(100, 50)  # Smaller fixed size for the animation

        self.circle_size = 15  # Maximum size of the circles
        self.gap = 10  # Gap between circles
        self.side_padding = 20  # Padding on the sides

    def start_animation(self):
        self.timer.start(100)  # Update every 100 ms
        self.show()  # Ensure the label is visible

    def stop_animation(self):
        self.timer.stop()  # Stop the timer
        self.circles = [0, 0, 0]  # Reset circle sizes
        self.update()  # Trigger a repaint
        self.hide()  # Hide the animation when done

    def update_animation(self):
        if self.circles[self.current_circle] < 20:  # Smaller max size
            self.circles[self.current_circle] += 2  # Increase size
        else:
            self.circles[self.current_circle] = 0  # Reset current circle
            self.current_circle = (self.current_circle + 1) % 3  # Move to the next circle

        self.update()  # Trigger a repaint

    def update_animation(self):
        if self.circles[self.current_circle] < self.circle_size:  # Use circle_size variable
            self.circles[self.current_circle] += 1  # Increase size more slowly
        else:
            self.circles[self.current_circle] = 0  # Reset current circle
            self.current_circle = (self.current_circle + 1) % 3  # Move to the next circle

        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing
        painter.setPen(Qt.transparent)  # Set pen to transparent

        for i in range(3):
            size = self.circles[i]
            x = self.side_padding + i * (self.gap + self.circle_size)  # Calculate x position with gap and padding
            y = (self.height() - size) / 2  # Center the circles vertically
            painter.setBrush(QColor(70, 130, 180, 180))  # Blue-gray color with 70% transparency
            painter.drawEllipse(x, y, size, size)  # Draw the circle

class DownloadWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, url, download_path):
        super().__init__()
        self.url = url
        self.download_path = download_path

    def run(self):
        response = requests.get(self.url, stream=True)
        response.raise_for_status()  # Raise an error for bad responses

        # Prepare the file name
        date_str = datetime.now().strftime("%Y%m%d")
        base_filename = f"{date_str}_downloaded.xml"
        file_name = os.path.join(self.download_path, base_filename)
        i = 0

        while os.path.exists(file_name):
            i += 1
            file_name = os.path.join(self.download_path, f"{date_str}_downloaded({i}).xml")

        try:# Save the XML content to a file
            with open(file_name, 'wb') as f:
                for data in response.iter_content(chunk_size=4096):
                    f.write(data)
        except (OSError, IOError) as e:
            self.error.emit(f"{e}")
            return

        self.finished.emit(file_name)

class LoadingOverlay(QDialog):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_TranslucentBackground)  # Make background transparent
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # Floating on top

        self.layout = QVBoxLayout(self)
        self.loading_animation = LoadingAnimation()  # Instance of your loading animation
        self.layout.addWidget(self.loading_animation, alignment=Qt.AlignCenter)
        self.setFixedSize(200, 100)  # Set the size of the overlay

    def start_animation(self):
        self.loading_animation.start_animation()
        self.resize(self.sizeHint())  # Resize to fit the content
        self.center_on_parent()  # Center it on the main window
        self.show()  # Show the overlay

    def center_on_parent(self):
        main_window_geometry = self.parent().geometry()  # Get the geometry of the main window
        self.setGeometry(
            main_window_geometry.x() + (main_window_geometry.width() - self.width()) // 2 - 50,
            main_window_geometry.y() + (main_window_geometry.height() - self.height()) // 2 - 100,
            self.width(), self.height()
        )

    def stop_animation(self):
        self.loading_animation.stop_animation()
        self.hide()  # Hide the overlay


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = AppState()

        if getattr(sys, 'frozen', False):
            # If running in a bundled environment
            self.state.path_to_app = sys._MEIPASS
        else:
            # If running in a development environment
            self.state.path_to_app = os.path.dirname(__file__)

        self.lextrus_xml_url = None
        self.xml_download_path = None

        # Load settings from the INI file
        self.load_settings()

        self.state.icons_path = os.path.join(self.state.path_to_app, 'icons/')

        self.setWindowTitle("Lextrus XML Edit")
        self.setGeometry(50, 50, 1200, 800)
        self.setStyleSheet(self.get_stylesheet())
        self.setWindowIcon(QIcon(f"{self.state.icons_path}app.png"))

        main_layout = QHBoxLayout()

        # Actions
        self.open_xml_action = QAction(QIcon("./icons/xml.png"), "Open XML", self)
        self.open_xml_action.triggered.connect(self.open_file)

        self.save_as_action = QAction(QIcon("./icons/save.png"), "Save File As...", self)
        self.save_as_action.triggered.connect(self.save_file_as)

        self.clear_tree_action = QAction(QIcon("./icons/close.png"), "Close File", self)
        self.clear_tree_action.triggered.connect(self.clear_tree)

        self.edit_node_action = QAction(QIcon("./icons/edit-node.png"), "Edit Current Node", self)
        self.edit_node_action.triggered.connect(self.edit_node)

        self.add_subnode_action = QAction(QIcon("./icons/add-subnode.png"), "Add Single Subnode", self)
        self.add_subnode_action.triggered.connect(self.add_subnode)

        self.remove_type_action = QAction(QIcon("./icons/delete-node.png"), "Remove Node Type", self)
        self.remove_type_action.setToolTip("Remove Selected Node Type from Tree")
        self.remove_type_action.setShortcut("Ctrl+R")
        self.remove_type_action.triggered.connect(self.remove_node_type)

        self.norm_price_action = QAction(QIcon("./icons/coin.png"), "Normalize Prices", self)
        self.norm_price_action.triggered.connect(self.process_prices)

        self.toggle_second_level_visibility_action = QAction(QIcon("./icons/nodes.png"), "Expand/Collapse Properties",
                                                             self)
        self.toggle_second_level_visibility_action.triggered.connect(self.open_close_properties)

        self.download_action = QAction(QIcon("./icons/download.png"), "Download Lextrus XML", self)
        self.download_action.triggered.connect(self.download_xml)

        self.remove_from_start_action = QAction(QIcon("./icons/trim.png"), "Remove/preserve properties", self)
        self.remove_from_start_action.triggered.connect(self.trim_dialog)




        # Create instances of Sidebar and other widgets
        self.sidebar = Sidebar(self)
        self.tree = TreeWidget(self)
        self.tabs = QTabWidget()

        #TABS
        self.tab_group_actions = TabGroupActions(self)
        self.tab_scraping = TabScraping(self)
        self.tab_filter_by_id = TabFilterById(self)
        self.tab_check_media_links = TabCheckMediaLinks(self)

        self.tabs.addTab(self.tab_group_actions, "Group actions")
        self.tabs.addTab(self.tab_scraping, "Site scraping")
        self.tabs.addTab(self.tab_filter_by_id, "Filter by ID")
        self.tabs.addTab(self.tab_check_media_links, "Check Media Links")

        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background-color: #b4c3d1; /* Background color of the tab */
                border-top-left-radius: 10px; /* Rounded top-left corner */
                border-top-right-radius: 10px; /* Rounded top-right corner */
                padding: 10px; /* Padding around the text */
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF; /* Background color of the selected tab */
            }
            
            QTabWidget::pane {
                border: 1px solid #f0f2f5; /* Border color of the tab widget pane */
                border-radius: 2px; /* Rounded corners of the tab widget pane */
            }
        """)

        self.tab_scraping.begin_scraping_property.connect(self.set_scraping_message)
        self.tab_scraping.data_scraped.connect(self.insert_scraped_data)

        #SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # Set desired handle width here
        splitter.addWidget(self.tree)
        splitter.addWidget(self.tabs)
        splitter.setSizes([300, 600])

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(splitter, 0)

        self.main_menu = MainMenu(self)  # Pass self to MainMenu for access to MainWindow methods
        self.setMenuBar(self.main_menu)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Create and set up the custom status bar
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

        # Connect the buttons to start the processes
        # self.tab_group_actions.scan_button.clicked.connect(self.start_scan_tree)
        # self.tab_group_actions.to_low_button.clicked.connect(self.start_to_low)

        # Store threads and workers
        self.threads = []
        self.workers = []

        self.state.property_count_updated.connect(self.status_bar.update_property_count_label)

        self.loading_overlay = LoadingOverlay()
        self.loading_overlay.setParent(self)


# SETTINGS

    def load_settings(self):
        config = ConfigParser()
        if os.path.exists('settings.ini'):
            config.read('settings.ini')
            self.lextrus_xml_url = config.get('Settings', 'LEXTRUS_XML_URL')
            self.xml_download_path = config.get('Settings', 'XML_DOWNLOAD_PATH')
        else:
            QMessageBox.warning(self, "Error", "Some functions won't be working! settings.ini file wasn't found!")

    def trim_dialog(self):
        # Open the dialog
        dialog = TrimTreeDialog(self)
        if dialog.exec():
            number, action, position = dialog.get_inputs()

            # If the user selected a valid number and an action, apply the action
            if number > 0 and action:
                self.tree.trim_tree(self.tree.topLevelItem(0), number, position, action)

        QMessageBox.warning(self, "Operation complete", "Properties was removed/preserved by the selected condition.")

# Actions

    # def download_xml(self):
    #     if self.xml_download_path is None or self.lextrus_xml_url is None:
    #         QMessageBox.warning(self, "Error", "Settings aren't loaded!")
    #         return  # Early exit
    #
    #     try:
    #         # Create a progress dialog
    #         progress_dialog = QProgressDialog("Downloading XML...", "Cancel", 0, 100, self)
    #         progress_dialog.setWindowTitle("Downloading")
    #         progress_dialog.setValue(0)
    #         progress_dialog.setCancelButtonText("Cancel")
    #         progress_dialog.setMinimumDuration(0)  # Show immediately
    #
    #         # Perform the download
    #         response = requests.get(self.lextrus_xml_url)
    #         response.raise_for_status()  # Raise an error for bad responses
    #
    #         # Ensure the download path exists
    #         os.makedirs(self.xml_download_path, exist_ok=True)
    #
    #         # Get today's date in YYYYMMDD format
    #         date_str = datetime.now().strftime("%Y%m%d")
    #
    #         # Base filename
    #         base_filename = f"{date_str}_downloaded.xml"
    #
    #         # Check for existing files and create an index if necessary
    #         i = 0
    #         file_name = os.path.join(self.xml_download_path, base_filename)
    #         while os.path.exists(file_name):
    #             i += 1
    #             file_name = os.path.join(self.xml_download_path, f"{date_str}_downloaded({i}).xml")
    #
    #         # Save the XML content to a file
    #         # with open(file_name, 'wb') as f:
    #         #     f.write(response.content)
    #
    #         with open(file_name, 'wb') as f:
    #             total_length = int(response.headers.get('content-length', 0))
    #             downloaded_length = 0
    #
    #             for data in response.iter_content(chunk_size=4096):
    #                 downloaded_length += len(data)
    #                 f.write(data)
    #
    #                 # Update the progress dialog
    #                 if total_length > 0:
    #                     percent = (downloaded_length / total_length) * 100
    #                     progress_dialog.setValue(int(percent))
    #
    #                 # Check if the user canceled the download
    #                 if progress_dialog.wasCanceled():
    #                     QMessageBox.warning(self, "Canceled", "Download was canceled.")
    #                     return
    #
    #         progress_dialog.setValue(100)  # Complete the dialog
    #
    #         try:
    #             self.load_xml_to_tree(file_name)  # Use your method to load XML
    #         except Exception as e:
    #             QMessageBox.critical(self, "Error", f"Failed to load downloaded XML file:\n{str(e)}")
    #
    #     except requests.RequestException as e:
    #         QMessageBox.critical(self, "Download Error", f"Failed to download the XML: {e}")

    def download_xml(self):
        if self.xml_download_path is None or self.lextrus_xml_url is None:
            QMessageBox.warning(self, "Error", "Settings aren't loaded!")
            return  # Exit early if settings aren't loaded

        # self.progress_dialog = QProgressDialog("Downloading XML...", "Cancel", 0, 100, self)
        # self.progress_dialog.setWindowTitle("Downloading")
        # self.progress_dialog.setMinimumDuration(0)
        # self.progress_dialog.setCancelButtonText("Cancel")
        #
        # # Set fixed size for the progress dialog
        # self.progress_dialog.setFixedSize(400, 100)
        #
        # Create and start the download worker
        self.setEnabled(False)
        self.loading_overlay.show()
        self.loading_overlay.start_animation()  # Start the animation

        self.worker = DownloadWorker(self.lextrus_xml_url, self.xml_download_path)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.error.connect(self.on_download_error)
        self.worker.start()

        # Show the dialog
        # self.progress_dialog.show()

    # def update_progress(self, value):
    #     self.progress_dialog.setValue(value)
    #     if value >= 100:
    #         self.progress_dialog.close()  # Close when complete

    def on_download_finished(self, file_name):
        # self.progress_dialog.close()
        self.setEnabled(True)
        self.loading_overlay.stop_animation()  # Stop the animation
        self.loading_overlay.hide()  # Hide loading animation

        try:
            self.tree.load_xml(file_name)  # Use your method to load XML
            QMessageBox.information(self, "XML File Download", f"Lextrus XML file successfully loaded.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load downloaded XML file:\n{str(e)}")

    def on_download_error(self, error_message):
        self.setEnabled(True)
        self.loading_overlay.stop_animation()  # Stop the animation
        self.loading_overlay.hide()  # Hide loading animation

        QMessageBox.information(self, "Error", f"The file wasn't downloaded: {error_message}.")

    def open_file(self):
        options = QFileDialog.Option.ReadOnly
        xml_file, _ = QFileDialog.getOpenFileName(self, "Open XML File", "./XML/", "XML Files (*.xml);;All Files (*)",
                                                  options=options)
        print(xml_file)
        if xml_file:
            try:
                self.tree.load_xml(xml_file)
                self.setWindowTitle(f"Lextrus XML Edit: {xml_file}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load XML file:\n{str(e)}")

    def open_close_properties(self):
        self.tree.toggle_second_level_visibility()

    def set_scraping_message(self, value):
        self.status_bar.show_message(f"Scraping property: {value}")

    def save_file_as(self):
        options = QFileDialog.Option.DontUseNativeDialog
        file_name, selected_filter = QFileDialog.getSaveFileName(self, "Save File As", "",
                                                   "XML Files (*.xml);;JSON Files (*.json);;All Files (*)",
                                                   options=options)
        if file_name:
            if not (file_name.endswith(".xml") or file_name.endswith(".json")):
                # Append the correct suffix based on the selected filter
                if "XML Files (*.xml)" in selected_filter:
                    file_name += ".xml"
                elif "JSON Files (*.json)" in selected_filter:
                    file_name += ".json"

            # Save based on the file extension
            if file_name.endswith(".xml"):
                self.tree.save_as_xml(file_name)
            elif file_name.endswith(".json"):
                self.tree.save_as_json(file_name)
            else:
                QMessageBox.warning(self, "Invalid Format", "Only XML and JSON formats are supported.")

    def clear_tree(self):
        self.tree.clear()
        self.setWindowTitle(f"Lextrus XML Edit")

    def edit_node(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            if selected_item.childCount() == 0:
                self.tree.edit_item(selected_item, column=1)
            else:
                msgBox = QMessageBox()
                msgBox.setText("Parent node has no value to edit.")
                msgBox.exec()

    def add_subnode(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            text, ok = QInputDialog.getText(self, "Input node name", "Enter node name:")
            if ok and text:
                new_node = dict()
                new_node['tag'] = text
                new_node['text'] = None
                self.tree.add_single_node(selected_item, new_node)
            else:
                QMessageBox.information(self, "Add node cancelled", f"Nothing to add")

    def remove_node_type(self):
        reply = QMessageBox.warning(
            self,  # Parent widget (usually the main window or dialog)
            "Warning",  # Title of the message box
            "Are you sure you want to remove the selected node type?",  # Warning message
            QMessageBox.Yes | QMessageBox.No,  # Buttons
            QMessageBox.No  # Default button
        )
        if reply == QMessageBox.Yes:
            selected_items = self.tree.selectedItems()
            if selected_items:
                selected_item = selected_items[0]
                parent_node = selected_item.parent()
                parent_node_type = parent_node.text(0)
                local_root = parent_node.parent()
                if local_root:
                    child_index = parent_node.indexOfChild(selected_item)
                    for index in range(local_root.childCount()):
                        # get the child of local root and delete child by index
                        if local_root.child(index).text(0) == parent_node_type:
                            local_root.child(index).removeChild(local_root.child(index).child(child_index))
                else:
                    parent_node.removeChild(selected_item)

    def insert_scraped_data(self, data_string):
        scraped_data = json.loads(data_string)
        property_id = scraped_data['ID']
        property_node = self.state.current_property_node
        if property_node.child(0).text(1) == property_id:
            scraped_data.pop("ID")  # remove ID info from dictionary
            for item in scraped_data:
                base_node = QTreeWidgetItem(property_node, [item, ])
                data = scraped_data.get(item, {})
                for key, value in data.items():
                    key = (key.lower()).replace(" ", "_").replace(",", "_").replace("'", "")
                    if key and value:

                        comma_index = value.find(',')  # check value for commas
                        if comma_index != -1:
                            value = value[:comma_index] + ':' + value[comma_index + 1:]

                        dict_node = QTreeWidgetItem(base_node, [key, value])

                    elif key and not value:
                        dict_node = QTreeWidgetItem(base_node, [key, "1"])

                # Expand the property node to show the newly added items
                property_node.setExpanded(True)

    def process_prices(self):
        print("Processing prices start")
        if self.tree.topLevelItemCount() > 0:
            print("Start tree method")
            self.tree.process_price_nodes()
            QMessageBox.information(self, "Finished", "The prices have been corrected.")
        else:
            QMessageBox.information(self, "Warning", "Nothing to process")

# Service Functions
    @Slot(int)
    def update_progress_bar(self, value):
        self.status_bar.progress_bar.setValue(value)
    def get_stylesheet(self):
        return """
            QMainWindow {
                background-color: #f0f2f5;
            }
            QTreeWidget {
                border: none;
                background-color: #ffffff;
                font-size: 14px;
                padding: 6px;
            }
            QTreeWidget::item {
                margin: 1px;
                padding: 3px;
            }
            QTreeWidget::item:hover {
                background-color: #eff5f9;
            }
            QTreeWidget::item:selected {
                background-color: #2794f2;
            }
    
            QLineEdit {
                padding: 1px;
                font-size: 14px;
                border-radius: 3px;
                border: 2px solid #e1e9db;
                height: 1.5em;
            }
            QLineEdit:focus {
                border: 1px solid #7fc8f4;
                height: 1.5em;
            }
            QToolTip {
                background-color: #333333;
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px;
                min-width: 30px;
                min-height: 24px;
                icon-size: 20px;
            }
            
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #cccccc;
            }
            QSplitter::handle {
            background-color: #d0d0d0;
            border: 1px solid #b0b0b0;
            width: 1px;
            height: 50%;
            }
            QSplitter::handle:hover {
                background-color: #a0a0a0;
            }
            
            #sidebar {
                background-color: #1565C0;
                border-radius: 10px;
                margin-right: 10px;
                margin-left: 5px;
            }
            
           QStatusBar {
              
            }
            
            QStatusBar > QProgressBar {
                
            }
            
        """

    #TEMP

    def start_actions(self, actions):
        self.status_bar.show_message(f"Working on {len(actions)} actions")
        print("Start actions")
        self.start_worker(actions)

    def start_scraping(self):
        self.status_bar.show_message(f"Scraping started")
        self.start_worker()
    def start_worker(self, actions=None):
        thread = QThread()
        worker = Worker(self.tree, actions)

        worker.moveToThread(thread)

        self.start_progress_bar()

        worker.progress_updated.connect(self.update_progress_bar)
        worker.finished.connect(self.on_worker_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        print("Before worker run")
        thread.started.connect(lambda: worker.run())

        thread.start()

        # Keep track of threads to ensure they are not destroyed prematurely
        self.threads.append(thread)
        thread.finished.connect(lambda: self.threads.remove(thread))

    def start_progress_bar(self):
        self.status_bar.start_progress()
    @Slot(int)
    def update_progress_bar(self, value):
        self.status_bar.progress_bar.setValue(value)

    @Slot()
    def on_worker_finished(self, task_type=None):
        # Reset progress bar and clear status message
        self.status_bar.stop_progress()
        self.status_bar.show_message("")
        if task_type is not None:
            if task_type == "action":
                QMessageBox.information(self, "Finished Action", "Action finished.")
            elif task_type == "scraping":
                QMessageBox.information(self, "Scraping Finished", "Scraping has been finished. Please check logs!")
            else:
                QMessageBox.information(self, "Finished Task", "Task finished")
        else:
            QMessageBox.information(self, "Finished", "Worker has finished task.")


    def check_media_links(self):
        self.status_bar.show_message(f"Media links check started")
        actions = [
            {"action": "compare_db_media_links_to_tree", "parent": "", "child": "", "value": "", "condition": "", "new_value": ""},
        ]
        self.start_worker(actions)

    # def run_received_actions(self, actions):
    #     for action in actions:
    #         action_type = action["action"]
    #         parent = action["parent"]
    #
    #         if action_type == "add":
    #             new_node = action["child"]
    #             initial_value = action["value"]
    #             if new_node:
    #                 self.tree.add_node_type(parent, new_node, initial_value, items_count, steps_in_one_action)
    #         elif action_type == "remove":
    #             child = action["child"]
    #             child_value = action["value"]
    #             condition = action["condition"]
    #             self.tree.remove_node_type(parent, child, child_value, condition, items_count, steps_in_one_action)
    #         elif action_type == "modify":
    #             child = action["child"]
    #             child_value = action["value"]
    #             condition = action["condition"]
    #             new_value = action["new_value"]
    #             self.tree.modify_node_type(parent, child, child_value, condition, new_value, items_count, steps_in_one_action)


        # for action in self.actions:
        #     action_type = action["action"]
        #     parent = action["parent"]
        #
        #     if action_type == "add":
        #         new_node = action["child"]
        #         initial_value = action["value"]
        #         if new_node:
        #             self.tree_window.add_node_type(parent, new_node, initial_value)
        #     elif action_type == "remove":
        #         child = action["child"]
        #         child_value = action["value"]
        #         condition = action["condition"]
        #         self.tree_window.remove_node_type(parent, child, child_value, condition)
        #     elif action_type == "modify":
        #         child = action["child"]
        #         child_value = action["value"]
        #         condition = action["condition"]
        #         new_value = action["new_value"]
        #         self.tree_window.modify_node_type(parent, child, child_value, condition, new_value)