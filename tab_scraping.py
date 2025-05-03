import json
from typing import Callable

import requests
from PySide6.QtCore import Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListView,
                               QHBoxLayout, QMessageBox, QFileDialog)


class TabScraping(QWidget):
    data_scraped = Signal(str)
    begin_scraping_property = Signal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.param_tag_type_input = QLineEdit(self)
        self.param_tag_class_input = QLineEdit(self)
        self.path_to_param_name_input = QLineEdit(self)
        # self.has_value_input = QComboBox(self)
        self.dict_name_input = QLineEdit(self)

        self.param_tag_type_input.setPlaceholderText("Tag")
        self.param_tag_class_input.setPlaceholderText("Class")
        self.path_to_param_name_input.setPlaceholderText("Name path")
        # self.has_value_input.addItems(["yes", "no"])
        self.dict_name_input.setPlaceholderText("Group")

        # Add input fields to form layout
        layout.addWidget(self.param_tag_type_input)
        layout.addWidget(self.param_tag_class_input)
        layout.addWidget(self.path_to_param_name_input)
        # self.form_layout.addWidget(self.has_value_input)
        layout.addWidget(self.dict_name_input)

        # self.node_value = QLineEdit()
        # self.node_value.setPlaceholderText("Enter value")
        # self.form_layout.addRow("Node value:", self.node_value)

        # Add and Remove buttons
        add_button = QPushButton("Add to scraping list", self)
        remove_button = QPushButton("Remove from scraping list", self)
        layout.addWidget(add_button)
        layout.addWidget(remove_button)

        # Scrap list view
        self.scrap_list_view = QListView(self)
        self.scrap_list_model = QStandardItemModel(self)
        self.scrap_list_view.setModel(self.scrap_list_model)

        # Add form layout and scrap list view to main layout
        # layout.addLayout(self.layout)
        layout.addWidget(self.scrap_list_view)

        # Begin scraping button
        scrape_button = QPushButton("Begin scraping", self)
        scrape_button.setStyleSheet("""
                            QPushButton {
                                background-color: #4CAF50;
                                border: none; /* No border */
                                color: white; /* White text */
                                padding: 5px 8px; /* Padding around text */
                                text-align: center; /* Center text */
                                text-decoration: none; /* No underline */
                                display: inline-block; /* Inline-block element */
                                font-size: 16px; /* Font size */
                                margin: 2px 1px; /* Margin around button */
                                cursor: pointer; /* Pointer cursor on hover */
                                border-radius: 6px; /* Rounded corners */
                            }
                            QPushButton:hover {
                                background-color: #45a049; /* Darker green on hover */
                            }
                        """)
        layout.addWidget(scrape_button)

        # Connect signals
        add_button.clicked.connect(self.add_to_scrap_list)
        remove_button.clicked.connect(self.remove_from_scrap_list)
        # scrape_button.clicked.connect(self.begin_scraping)
        scrape_button.clicked.connect(self.parent.start_scraping)

        load_save_buttons_layout = QHBoxLayout()
        layout.addLayout(load_save_buttons_layout)

        self.save_actions_button = QPushButton("Save Scraping List")
        self.save_actions_button.clicked.connect(self.save_scraping_list)
        load_save_buttons_layout.addWidget(self.save_actions_button)

        self.load_actions_button = QPushButton("Load Scraping List")
        self.load_actions_button.setStyleSheet("""
                                                 QPushButton {
                                                     background-color: #f9bf3b;
                                                     border: none; /* No border */
                                                     color: white; /* White text */
                                                     padding: 5px 8px; /* Padding around text */
                                                     text-align: center; /* Center text */
                                                     text-decoration: none; /* No underline */
                                                     display: inline-block; /* Inline-block element */
                                                     font-size: 16px; /* Font size */
                                                     margin: 2px 1px; /* Margin around button */
                                                     cursor: pointer; /* Pointer cursor on hover */
                                                 }
                                                 QPushButton:hover {
                                                     background-color: #f39c12; /* Darker green on hover */
                                                 }
                                             """)
        self.load_actions_button.clicked.connect(self.load_scraping_list)
        load_save_buttons_layout.addWidget(self.load_actions_button)

    def save_scraping_list(self):
        """Save the scrap list to a JSON file."""
        # Open a file dialog to select the file path
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Scrap List", "./scraping/", "JSON Files (*.json);;All Files (*)")

        if file_path:
            # Convert the model items to a list of dictionaries
            scrap_list = [self.scrap_list_model.item(i).text() for i in range(self.scrap_list_model.rowCount())]

            # Write the list to a JSON file
            with open(file_path, 'w') as file:
                json.dump(scrap_list, file, indent=4)
            QMessageBox.information(self, "Save Successful", "Scrap list has been saved successfully.")

    def add_to_scrap_list(self):
        # Create a dictionary from the form inputs
        item_dict = {
            'param_tag_type': self.param_tag_type_input.text(),
            'param_tag_class': self.param_tag_class_input.text(),
            'path_to_param_name': self.path_to_param_name_input.text(),
            # 'has_value': self.has_value_input.currentText(),
            'dict_name': self.dict_name_input.text(),
        }

        # Add the dictionary to the scrap list view
        item = QStandardItem(str(item_dict))
        self.scrap_list_model.appendRow(item)

        # Clear input fields after adding
        self.param_tag_type_input.clear()
        self.param_tag_class_input.clear()
        self.path_to_param_name_input.clear()
        # self.has_value_input.setCurrentIndex(0)
        self.dict_name_input.clear()

    def load_scraping_list(self):
        """Load the scrap list from a JSON file."""
        # Open a file dialog to select the JSON file
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Scrap List", "./scraping/", "JSON Files (*.json);;All Files (*)")

        if file_path:
            # Read the JSON file
            with open(file_path, 'r') as file:
                scrap_list = json.load(file)

            # Clear the current model
            self.scrap_list_model.clear()

            # Populate the model with the loaded data
            for item_str in scrap_list:
                item = QStandardItem(item_str)
                self.scrap_list_model.appendRow(item)

            QMessageBox.information(self, "Load Successful", "Scrap list has been loaded successfully.")

    def remove_from_scrap_list(self):
        # Remove the selected item from the scrap list view
        selected_indexes = self.scrap_list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
            self.scrap_list_model.removeRow(index.row())

    def begin_scraping(self, progress_callback):
        if self.scrap_list_model.rowCount() > 0:
            not_found_pages = []
            data_to_scrape = [self.scrap_list_model.item(i).text() for i in range(self.scrap_list_model.rowCount())]
            root = self.parent.tree.topLevelItem(0)  # Root item
            total_items = self.parent.state.get_property_count()
            # Process the XML tree from the main window
            for i in range(root.childCount()):
                if root.child(i).text(0) == 'property':
                    property_node = root.child(i)
                    message = str(property_node.child(0).text(1))
                    self.begin_scraping_property.emit(message)

                    self.parent.state.current_property_node = root.child(i)
                    property_id = self.parent.state.current_property_node.child(0).text(1)

                    # property_id = property_node.text(0)  # Assuming ID is in the first column

                    # Prepare the URL and request the page
                    url = f'https://lextrusrealestate.com/property-{property_id}/'
                    try:
                        response = requests.get(url)
                        response.raise_for_status()
                    except requests.exceptions.RequestException:
                        not_found_pages.append(property_id)
                        continue

                    # Scraping with BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')

                    body = soup.find('body')
                    property_details_div = body.find('div', id='estatebud-property-details')

                    if property_details_div:

                        scraped_data = {'ID': property_id, }

                        for item_str in data_to_scrape:
                            item = eval(item_str)  # Convert the string back to a dictionary
                            elements = soup.find_all(item['param_tag_type'], class_=item['param_tag_class'])
                            item_dict = {}

                            for element in elements:
                                name = element.select_one(item['path_to_param_name'])

                                if ':' in element.get_text():
                                    cleaned_name = name.get_text(strip=True).rstrip(':') if name else None
                                elif ',' in element.get_text():
                                    cleaned_name = name.get_text(strip=True).rstrip(',') if name else None
                                else:
                                    cleaned_name = name.get_text(strip=True)

                                value = ""

                                if ':' in element.get_text():
                                    value = element.get_text().split(':')[-1].strip()
                                elif ',' in element.get_text():
                                    value = element.get_text().split(',')[-1].strip()
                                else:
                                    pass

                                if cleaned_name:
                                    item_dict[cleaned_name] = value

                            if item_dict:
                                dict_name = item['dict_name']
                                scraped_data[dict_name] = item_dict

                            progress_callback(int((i + 1) / total_items * 100))
                            time.sleep(0.05)  # Delay before the next request

                        if scraped_data:
                            data_string = json.dumps(scraped_data)
                            self.data_scraped.emit(data_string)


                    else:
                        not_found_pages.append(property_id)

                # progress_callback(int((i + 1) / total_items * 100))

            # Handle not found pages
            self.parent.state.current_property_node = None
            if not_found_pages:
                self.save_not_found_pages(not_found_pages)

            # QMessageBox.information(self, "Scraping Completed", "Scraping process is finished!")
        else:
            QMessageBox.information(self, "Scraping start error", "Scraping list is empty.")

    def save_not_found_pages(self, not_found_pages):
        timestamp = datetime.now().strftime("%Y%m%d_%H-%M")
        filename = f"./LOGS/scraping_error_IDs_{timestamp}.txt"
        index = 1

        while os.path.exists(filename):
            filename = f"./LOGS/scraping_error_IDs_{timestamp}({index}).txt"
            index += 1

        with open(filename, 'w') as file:
            for page_id in not_found_pages:
                file.write(f"{page_id}\n")