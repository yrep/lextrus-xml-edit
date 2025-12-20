from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QTextEdit, QSplitter, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QFont
import re

class TabFindPhones(QWidget):
    progress_updated = Signal(int)
    found_phones = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.found_items = []
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        description = QLabel("Finds objects containing phone numbers in description")
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        self.find_button = QPushButton("Find Phones")
        self.find_button.setCursor(Qt.PointingHandCursor)
        self.find_button.clicked.connect(self.find_phones)
        
        self.copy_button = QPushButton("Copy ID List")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(self.copy_ids)
        self.copy_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_results)
        
        button_layout.addWidget(self.find_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #cccccc; }")
        
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(2)
        left_layout.addWidget(QLabel("Found objects:"))
        self.id_list = QListWidget()
        self.id_list.setSpacing(2)
        self.id_list.itemClicked.connect(self.show_selected_text)
        left_layout.addWidget(self.id_list)
        splitter.addWidget(left_frame)
        
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)
        right_layout.addWidget(QLabel("Description text:"))
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(QFont("Courier", 9))
        right_layout.addWidget(self.text_preview)
        splitter.addWidget(right_frame)
        
        splitter.setSizes([250, 550])
        main_layout.addWidget(splitter, 1)
        
        self.stats_label = QLabel("")
        self.stats_label.setFixedHeight(20)
        main_layout.addWidget(self.stats_label, 0)
        
        self.setLayout(main_layout)
        
    def find_phones(self):
        if self.parent.tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Error", "Load XML file first!")
            return
            
        self.find_button.setEnabled(False)
        self.id_list.clear()
        self.text_preview.clear()
        self.found_items = []
        
        root_item = self.parent.tree.topLevelItem(0)
        if not root_item:
            return
            
        found_count = 0
        checked_count = 0
        total_properties = self.parent.state.get_property_count()
        
        for i in range(root_item.childCount()):
            property_item = root_item.child(i)
            
            if property_item.text(0) == 'property':
                checked_count += 1
                progress = int((checked_count / total_properties) * 100) if total_properties > 0 else 0
                self.progress_updated.emit(progress)
                
                id_item = self.find_child_by_text(property_item, 'id')
                if not id_item:
                    continue
                    
                property_id = id_item.text(1)
                desc_item = self.find_child_by_text(property_item, 'desc')
                if not desc_item:
                    continue
                    
                en_item = self.find_child_by_text(desc_item, 'en')
                if not en_item:
                    continue
                    
                description = en_item.text(1) or ""
                phone_matches = self.find_phone_matches(description)
                
                if phone_matches:
                    found_count += 1
                    item_data = {
                        'id': property_id,
                        'full_text': description,
                        'matches': phone_matches
                    }
                    self.found_items.append(item_data)
                    
                    item_text = f"ID: {property_id} - found: {', '.join([m[:30] + '...' if len(m) > 30 else m for m in phone_matches[:2]])}"
                    if len(phone_matches) > 2:
                        item_text += f" (+{len(phone_matches) - 2})"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, len(self.found_items) - 1)
                    self.id_list.addItem(item)
        
        self.stats_label.setText(f"Objects with phones found: {found_count} from {checked_count}")
        self.copy_button.setEnabled(len(self.found_items) > 0)
        self.find_button.setEnabled(True)
        
        if self.found_items and self.id_list.count() > 0:
            self.id_list.setCurrentRow(0)
            self.show_selected_text(self.id_list.item(0))
        
        if found_count > 0:
            QMessageBox.information(self, "Search Complete", f"Found {found_count} objects with possible phone numbers.")
        else:
            QMessageBox.information(self, "Search Complete", "No phones found.")
            
    def find_phone_matches(self, text):
        if not text:
            return []
            
        matches = []
        
        plus_matches = re.findall(r'(\+\d[+\d\s\-\(\)]{6,})', text)
        matches.extend(plus_matches)
        
        if '357' in text:
            matches.append('357 (Cyprus code)')
        
        digit_sequences = re.findall(r'(\d[\d\s\-\(\)]{6,}\d)', text)
        for seq in digit_sequences:
            clean_seq = re.sub(r'\D', '', seq)
            if len(clean_seq) >= 7:
                matches.append(seq)
        
        pattern_matches = re.findall(r'(\(\d{3}\)\s*\d{3}[- ]?\d{4})', text)
        matches.extend(pattern_matches)
        
        intl_matches = re.findall(r'(\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4})', text)
        matches.extend(intl_matches)
        
        country_matches = re.findall(r'(00\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4})', text)
        matches.extend(country_matches)
        
        text_lower = text.lower()
        keywords = ['contact', 'office', 'call', 'phone', 'mobile', 'tel']
        for keyword in keywords:
            if keyword in text_lower:
                idx = text_lower.find(keyword)
                start = max(0, idx - 15)
                end = min(len(text), idx + len(keyword) + 15)
                context = text[start:end]
                matches.append(f"{keyword}: {context}")
        
        return list(set(matches))[:5]
        
    def find_child_by_text(self, parent_item, text):
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.text(0) == text:
                return child
        return None
        
    def show_selected_text(self, list_item):
        if not list_item:
            return
            
        item_index = list_item.data(Qt.UserRole)
        if item_index is None or item_index >= len(self.found_items):
            return
            
        item_data = self.found_items[item_index]
        display_text = f"ID: {item_data['id']}\n"
        display_text += "=" * 50 + "\n\n"
        display_text += "Found matches:\n"
        
        for i, match in enumerate(item_data['matches'], 1):
            display_text += f"{i}. {match}\n"
        
        display_text += "\n" + "=" * 50 + "\n\n"
        display_text += "Full description:\n"
        display_text += "-" * 50 + "\n"
        
        full_text = item_data['full_text']
        for match in item_data['matches']:
            phone_part = match.split(": ")[-1] if ": " in match else match
            if phone_part and phone_part in full_text:
                full_text = full_text.replace(phone_part, f"***{phone_part}***")
        
        display_text += full_text
        self.text_preview.setText(display_text)
        
    def copy_ids(self):
        if not self.found_items:
            return
            
        ids_string = ", ".join([item['id'] for item in self.found_items])
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(ids_string)
        
        QMessageBox.information(self, "Copied", f"{len(self.found_items)} IDs copied to clipboard.")
    
    def clear_results(self):
        self.id_list.clear()
        self.text_preview.clear()
        self.found_items = []
        self.stats_label.setText("")
        self.copy_button.setEnabled(False)