from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QTextEdit, QSplitter, QFrame, QTextBrowser, QDialog, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QFont, QTextCharFormat, QBrush, QColor, QTextCursor, QSyntaxHighlighter, QTextDocument
import re

class EditDescriptionDialog(QDialog):
    def __init__(self, current_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Description")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        self.text_edit = QTextEdit()
        self.text_edit.setText(current_text)
        self.text_edit.setFont(QFont("Courier", 10))
        layout.addWidget(self.text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_text(self):
        return self.text_edit.toPlainText()

class PhoneHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.match_lines = []
        self.format = QTextCharFormat()
        self.format.setBackground(QBrush(QColor(255, 255, 200)))
        
    def set_match_lines(self, match_lines):
        self.match_lines = match_lines
        self.rehighlight()
        
    def highlightBlock(self, text):
        block_number = self.currentBlock().blockNumber()
        if block_number in self.match_lines:
            self.setFormat(0, len(text), self.format)

class TabFindPhones(QWidget):
    progress_updated = Signal(int)
    
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
        
        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_selected_description)
        self.edit_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_results)
        
        button_layout.addWidget(self.find_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet("QSplitter::handle { background-color: #cccccc; }")
        
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(2, 2, 2, 2)
        left_layout.setSpacing(2)
        left_layout.addWidget(QLabel("Found objects:"))
        self.id_list = QListWidget()
        self.id_list.setSpacing(3)
        self.id_list.itemClicked.connect(self.on_item_selected)
        left_layout.addWidget(self.id_list)
        splitter.addWidget(left_frame)
        
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)
        
        right_top_layout = QHBoxLayout()
        right_top_layout.addWidget(QLabel("Description text:"))
        self.save_button = QPushButton("Save Changes")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_description)
        self.save_button.setEnabled(False)
        right_top_layout.addStretch()
        right_top_layout.addWidget(self.save_button)
        right_layout.addLayout(right_top_layout)
        
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setFont(QFont("Courier", 9))
        self.highlighter = PhoneHighlighter(self.text_preview.document())
        right_layout.addWidget(self.text_preview)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier", 9))
        self.text_edit.setVisible(False)
        self.text_edit.textChanged.connect(self.on_text_changed)
        right_layout.addWidget(self.text_edit)
        
        splitter.addWidget(right_frame)
        
        splitter.setSizes([250, 550])
        main_layout.addWidget(splitter, 1)
        
        self.stats_label = QLabel("")
        self.stats_label.setFixedHeight(20)
        main_layout.addWidget(self.stats_label, 0)
        
        self.setLayout(main_layout)
        
        self.current_item_index = -1
        self.original_text = ""
        
    def on_item_selected(self, list_item):
        if not list_item:
            return
        
        self.edit_button.setEnabled(True)
        item_index = list_item.data(Qt.UserRole)
        if item_index is None or item_index >= len(self.found_items):
            return
        
        self.current_item_index = item_index
        item_data = self.found_items[item_index]
        self.original_text = item_data['full_text']
        
        self.text_preview.setText(item_data['full_text'])
        self.highlighter.set_match_lines(item_data['match_lines'])
        self.text_preview.setVisible(True)
        self.text_edit.setVisible(False)
        self.save_button.setEnabled(False)
        
    def on_text_changed(self):
        self.save_button.setEnabled(self.text_edit.toPlainText() != self.original_text)
        
    def find_phones(self):
        if self.parent.tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Error", "Load XML file first!")
            return
            
        self.find_button.setEnabled(False)
        self.id_list.clear()
        self.text_preview.clear()
        self.text_edit.clear()
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
                match_lines = self.find_phone_matches(description)
                
                if match_lines:
                    found_count += 1
                    item_data = {
                        'id': property_id,
                        'full_text': description,
                        'desc_item': en_item,
                        'match_lines': match_lines,
                        'match_count': len(match_lines)
                    }
                    self.found_items.append(item_data)
                    
                    item_text = f"ID: {property_id} - {len(match_lines)} matches"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, len(self.found_items) - 1)
                    self.id_list.addItem(item)
        
        self.stats_label.setText(f"Objects with phones found: {found_count} from {checked_count}")
        self.copy_button.setEnabled(len(self.found_items) > 0)
        self.edit_button.setEnabled(False)
        self.find_button.setEnabled(True)
        
        if self.found_items and self.id_list.count() > 0:
            self.id_list.setCurrentRow(0)
            self.on_item_selected(self.id_list.item(0))
        
        if found_count > 0:
            QMessageBox.information(self, "Search Complete", f"Found {found_count} objects with possible phone numbers.")
        else:
            QMessageBox.information(self, "Search Complete", "No phones found.")
            
    def find_phone_matches(self, text):
        if not text:
            return []
        
        lines = text.split('\n')
        match_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            found = False
            
            if re.search(r'(\+\d[+\d\s\-\(\)]{6,})', line):
                found = True
            
            if '357' in line:
                found = True
            
            digit_sequences = re.findall(r'(\d[\d\s\-\(\)]{6,}\d)', line)
            for seq in digit_sequences:
                clean_seq = re.sub(r'\D', '', seq)
                if len(clean_seq) >= 7:
                    found = True
                    break
            
            if re.search(r'(\(\d{3}\)\s*\d{3}[- ]?\d{4})', line):
                found = True
            
            if re.search(r'(\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4})', line):
                found = True
            
            if re.search(r'(00\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4})', line):
                found = True
            
            line_lower = line.lower()
            keywords = ['contact', 'office', 'call', 'phone', 'mobile', 'tel', 'fax']
            for keyword in keywords:
                if keyword in line_lower:
                    found = True
                    break
            
            if found:
                match_lines.append(i)
        
        return match_lines
            
    def edit_selected_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        dialog = EditDescriptionDialog(self.original_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            if new_text != self.original_text:
                self.text_edit.setText(new_text)
                self.text_preview.setVisible(False)
                self.text_edit.setVisible(True)
                self.save_button.setEnabled(True)
                
    def save_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        new_text = self.text_edit.toPlainText()
        item_data = self.found_items[self.current_item_index]
        
        try:
            item_data['desc_item'].setText(1, new_text)
            item_data['full_text'] = new_text
            
            match_lines = self.find_phone_matches(new_text)
            item_data['match_lines'] = match_lines
            item_data['match_count'] = len(match_lines)
            
            self.text_preview.setText(new_text)
            self.highlighter.set_match_lines(match_lines)
            
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.save_button.setEnabled(False)
            
            self.update_list_item(self.current_item_index, len(match_lines))
            
            QMessageBox.information(self, "Success", "Description saved to tree.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save description: {str(e)}")
            
    def update_list_item(self, item_index, match_count):
        for i in range(self.id_list.count()):
            item = self.id_list.item(i)
            if item.data(Qt.UserRole) == item_index:
                item_text = f"ID: {self.found_items[item_index]['id']} - {match_count} matches"
                item.setText(item_text)
                break
            
    def find_child_by_text(self, parent_item, text):
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.text(0) == text:
                return child
        return None
        
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
        self.text_edit.clear()
        self.found_items = []
        self.stats_label.setText("")
        self.copy_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.text_preview.setVisible(True)
        self.text_edit.setVisible(False)
        self.current_item_index = -1
        self.highlighter.set_match_lines([])