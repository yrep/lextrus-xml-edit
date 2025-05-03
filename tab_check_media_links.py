import json
from typing import Callable

import requests
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListView,
                               QHBoxLayout, QMessageBox, QFileDialog)


class TabCheckMediaLinks(QWidget):
    links_checked = Signal(str)
    start_check = Signal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.start_check_button = QPushButton("Start checking media links", self)
        self.start_check_button.setStyleSheet("""
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
        self.start_check_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.start_check_button)


        self.result_property_ids_nf_label = QLabel("Not found in the XML file:", self)
        layout.addWidget(self.result_property_ids_nf_label)


        self.result_property_ids_nf = QTextEdit("")
        self.result_property_ids_nf.setReadOnly(True)
        self.result_property_ids_nf.setMinimumHeight(100)
        layout.addWidget(self.result_property_ids_nf)

        self.result_property_ids_bl_label = QLabel("Propertyes with broken links in DB (id_in):", self)
        layout.addWidget(self.result_property_ids_bl_label)

        self.result_property_ids_bl = QTextEdit("")
        self.result_property_ids_bl.setReadOnly(True)
        self.result_property_ids_bl.setMinimumHeight(100)
        layout.addWidget(self.result_property_ids_bl)


        self.start_check_button.clicked.connect(self.parent.check_media_links)