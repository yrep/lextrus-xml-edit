from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QTextEdit, QSplitter, QFrame, QDialog, QDialogButtonBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QFont, QTextCharFormat, QBrush, QColor, QSyntaxHighlighter
import re
import os
import configparser

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
        self.matches = []
        self.formats = {
            'phone': QTextCharFormat(),
            'email': QTextCharFormat(),
            'keyword': QTextCharFormat()
        }
        
        self.formats['phone'].setBackground(QBrush(QColor(255, 255, 200)))
        self.formats['email'].setBackground(QBrush(QColor(200, 255, 200)))
        self.formats['keyword'].setBackground(QBrush(QColor(255, 200, 200)))
        
    def set_matches(self, matches):
        self.matches = matches
        self.rehighlight()
        
    def highlightBlock(self, text):
        if not self.matches:
            return
            
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)
        
        for match_start, match_end, match_type in self.matches:
            if match_start >= block_start and match_end <= block_end:
                local_start = match_start - block_start
                local_end = match_end - block_start
                
                if local_start >= 0 and local_end <= len(text):
                    self.setFormat(local_start, local_end - local_start, self.formats.get(match_type, self.formats['phone']))

class TabFindPhones(QWidget):
    progress_updated = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.found_items = []
        self.keywords = self.load_keywords()
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        description = QLabel("Finds objects containing phone numbers or email addresses in description")
        description.setWordWrap(True)
        main_layout.addWidget(description)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # Стиль для всех кнопок
        button_style = """
            QPushButton {
                padding: 8px 15px;
                border: 2px solid #ccc;
                border-radius: 5px;
                background-color: #f0f0f0;
                font-weight: bold;
                color: #333;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border-color: #777;
                padding-top: 9px;
                padding-bottom: 7px;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                color: #aaa;
                border-color: #ddd;
            }
        """
        
        self.find_button = QPushButton("Find Phones")
        self.find_button.setCursor(Qt.PointingHandCursor)
        self.find_button.clicked.connect(self.find_phones)
        self.find_button.setStyleSheet(button_style)
        
        self.copy_button = QPushButton("Copy ID List")
        self.copy_button.setCursor(Qt.PointingHandCursor)
        self.copy_button.clicked.connect(self.copy_ids)
        self.copy_button.setEnabled(False)
        self.copy_button.setStyleSheet(button_style)
        
        self.edit_button = QPushButton("Edit Selected")
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_selected_description)
        self.edit_button.setEnabled(False)
        self.edit_button.setStyleSheet(button_style + """
            QPushButton:enabled {
                background-color: #90EE90;
                border-color: #70c070;
            }
            QPushButton:enabled:hover {
                background-color: #80dd80;
                border-color: #60b060;
            }
            QPushButton:enabled:pressed {
                background-color: #70cc70;
                border-color: #50a050;
            }
        """)
        
        self.pass_button = QPushButton("Pass")
        self.pass_button.setCursor(Qt.PointingHandCursor)
        self.pass_button.clicked.connect(self.mark_as_passed)
        self.pass_button.setEnabled(False)
        self.pass_button.setStyleSheet(button_style + """
            QPushButton:enabled {
                background-color: #ADD8E6;
                border-color: #8db8c6;
            }
            QPushButton:enabled:hover {
                background-color: #9dc8d6;
                border-color: #7da8b6;
            }
            QPushButton:enabled:pressed {
                background-color: #8db8c6;
                border-color: #6d98a6;
            }
        """)
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_description)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet(button_style + """
            QPushButton:enabled {
                background-color: #FFA500;
                border-color: #df8500;
            }
            QPushButton:enabled:hover {
                background-color: #ef9500;
                border-color: #cf7500;
            }
            QPushButton:enabled:pressed {
                background-color: #df8500;
                border-color: #bf6500;
            }
        """)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_results)
        self.clear_button.setStyleSheet(button_style)
        
        button_layout.addWidget(self.find_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.pass_button)
        button_layout.addWidget(self.save_button)
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
        
        # Правильный стиль списка - текст всегда черный
        self.id_list.setStyleSheet("""
            QListWidget {
                background-color: white;
            }
            QListWidget::item {
                color: black;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: rgba(100, 150, 220, 150);
                border-left: 3px solid #0066CC;
                color: black;
            }
            QListWidget::item:selected:!active {
                background-color: rgba(100, 150, 220, 100);
                border-left: 3px solid #0066CC;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #e9ecef;
            }
        """)
        
        left_layout.addWidget(self.id_list)
        splitter.addWidget(left_frame)
        
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(2, 2, 2, 2)
        right_layout.setSpacing(2)
        
        right_top_layout = QHBoxLayout()
        right_top_layout.addWidget(QLabel("Description text:"))
        right_top_layout.addStretch()
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
        self.edit_mode = False
    
    def load_keywords(self):
        default_keywords = [
            'contacts', 'office', 'phone', 'mobile', 'mob', 'tel', 'fax', 'email', 'call us',
            'contact us', 'telephone', 'cell', 'whatsapp', 'viber', 'telegram', 'skype', 'contact', 'call'
        ]
        
        try:
            if os.path.exists('./settings.ini'):
                config = configparser.ConfigParser()
                config.read('./settings.ini', encoding='utf-8')
                
                if 'Keywords' in config and 'keywords' in config['Keywords']:
                    keywords_str = config['Keywords']['keywords']
                    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    if keywords:
                        return keywords
        except:
            pass
        
        return default_keywords
        
    def on_item_selected(self, list_item):
        if not list_item:
            return
        
        item_index = list_item.data(Qt.UserRole)
        if item_index is None or item_index >= len(self.found_items):
            return
        
        self.current_item_index = item_index
        item_data = self.found_items[item_index]
        
        self.edit_button.setEnabled(True)
        self.pass_button.setEnabled(True)
        
        self.save_button.setEnabled(item_data.get('state') == 'edited')
        
        if item_data.get('state') == 'edited':
            self.save_button.setStyleSheet(self.save_button.styleSheet() + """
                QPushButton:enabled {
                    background-color: #FFA500;
                    border-color: #df8500;
                }
            """)
        
        if item_data.get('state') == 'edited':
            display_text = item_data.get('edited_text', item_data['full_text'])
            self.text_edit.setText(display_text)
            self.text_preview.setVisible(False)
            self.text_edit.setVisible(True)
            self.edit_mode = True
        else:
            display_text = item_data['full_text']
            self.text_preview.setText(display_text)
            
            current_displayed_text = self.text_preview.toPlainText()
            matches_info = self.find_phone_matches(current_displayed_text)
            self.highlighter.set_matches(matches_info['matches'])
            
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
        
        self.update_item_colors()
    
    def on_text_changed(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
            
        new_text = self.text_edit.toPlainText()
        item_data = self.found_items[self.current_item_index]
        
        if new_text != item_data.get('original_text', item_data['full_text']):
            item_data['state'] = 'edited'
            item_data['edited_text'] = new_text
            self.save_button.setEnabled(True)
        else:
            item_data['state'] = 'none'
            if 'edited_text' in item_data:
                del item_data['edited_text']
            self.save_button.setEnabled(False)
        
        self.update_item_colors()
        
    def update_item_colors(self):
        for i in range(self.id_list.count()):
            item = self.id_list.item(i)
            item_index = item.data(Qt.UserRole)
            if item_index is not None and item_index < len(self.found_items):
                item_data = self.found_items[item_index]
                state = item_data.get('state', 'none')
                
                if state == 'saved':
                    item.setBackground(QColor(144, 238, 144))
                elif state == 'passed':
                    item.setBackground(QColor(173, 216, 230))
                elif state == 'edited':
                    item.setBackground(QColor(255, 165, 0))
                else:
                    item.setBackground(Qt.transparent)
                
                item.setForeground(QColor(0, 0, 0))
        
    def find_phones(self):
        if self.parent.tree.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Error", "Load XML file first!")
            return
            
        self.find_button.setEnabled(False)
        self.id_list.clear()
        self.text_preview.clear()
        self.text_edit.clear()
        self.found_items = []
        self.current_item_index = -1
        
        root_item = self.parent.tree.topLevelItem(0)
        if not root_item:
            return
            
        found_count = 0
        checked_count = 0
        phone_count = 0
        email_count = 0
        keyword_count = 0
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
                    
                raw_description = en_item.text(1) or ""
                
                matches_info = self.find_phone_matches(raw_description)
                matches = matches_info['matches']
                stats = matches_info['stats']
                
                if matches:
                    found_count += 1
                    
                    email_count += stats.get('email', 0)
                    phone_count += stats.get('phone', 0)
                    keyword_count += stats.get('keyword', 0)
                    
                    item_data = {
                        'id': property_id,
                        'full_text': raw_description,
                        'original_text': raw_description,
                        'desc_item': en_item,
                        'stats': stats,
                        'state': 'none',
                        'has_email': stats.get('email', 0) > 0,
                        'has_phone': stats.get('phone', 0) > 0,
                        'has_keyword': stats.get('keyword', 0) > 0
                    }
                    self.found_items.append(item_data)
                    
                    item_text = f"ID: {property_id} - {len(matches)} matches"
                    
                    type_indicators = []
                    if stats.get('email', 0) > 0:
                        type_indicators.append(f"{stats['email']} email")
                    if stats.get('phone', 0) > 0:
                        type_indicators.append(f"{stats['phone']} phone")
                    if stats.get('keyword', 0) > 0:
                        type_indicators.append(f"{stats['keyword']} keyword")
                    
                    if type_indicators:
                        item_text += f" ({', '.join(type_indicators)})"
                    
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, len(self.found_items) - 1)
                    self.id_list.addItem(item)
        
        self.update_item_colors()
        
        stats_text = f"Found: {found_count} objects"
        type_stats = []
        if phone_count > 0:
            type_stats.append(f"{phone_count} phones")
        if email_count > 0:
            type_stats.append(f"{email_count} emails")
        if keyword_count > 0:
            type_stats.append(f"{keyword_count} keywords")
        
        if type_stats:
            stats_text += f" ({', '.join(type_stats)})"
        
        if found_count > 0:
            total_matches = sum(item['stats'].get('phone', 0) + item['stats'].get('email', 0) + item['stats'].get('keyword', 0) for item in self.found_items)
            stats_text += f" - Total matches: {total_matches}"
        
        self.stats_label.setText(stats_text)
        self.copy_button.setEnabled(len(self.found_items) > 0)
        self.edit_button.setEnabled(False)
        self.pass_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.find_button.setEnabled(True)
        
        if self.found_items and self.id_list.count() > 0:
            self.id_list.setCurrentRow(0)
            self.on_item_selected(self.id_list.item(0))
        
        if found_count > 0:
            message = f"Found {found_count} objects with contacts:\n"
            if phone_count > 0:
                message += f"• {phone_count} with phone numbers\n"
            if email_count > 0:
                message += f"• {email_count} with email addresses\n"
            if keyword_count > 0:
                message += f"• {keyword_count} with keywords\n"
            total_matches = sum(item['stats'].get('phone', 0) + item['stats'].get('email', 0) + item['stats'].get('keyword', 0) for item in self.found_items)
            message += f"• Total matches: {total_matches}"
            
            QMessageBox.information(self, "Search Complete", message)
        else:
            QMessageBox.information(self, "Search Complete", "No contacts found.")
            
    def find_phone_matches(self, text):
        if not text:
            return {'matches': [], 'stats': {'phone': 0, 'email': 0, 'keyword': 0}}
        
        matches = []
        stats = {'phone': 0, 'email': 0, 'keyword': 0}
        
        email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
        
        for match in re.finditer(email_pattern, text, re.IGNORECASE):
            start, end = match.start(), match.end()
            matches.append((start, end, 'email'))
            stats['email'] += 1
        
        phone_patterns = [
            r'\+\d{1,4}\s*\(\d{1,4}\)\s*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d',
            r'\(\d{1,4}\)\s*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d[\s\-]*\d',
            r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',
            r'\d{3}\s\d{3}\s\d{4}',
            r'\+\d{7,15}',
            r'\b\d{7,15}\b'
        ]
        
        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                phone_text = match.group()
                start, end = match.start(), match.end()
                
                digits = ''.join(c for c in phone_text if c.isdigit())
                
                if 7 <= len(digits) <= 15:
                    is_part_of_email = False
                    for email_start, email_end, _ in matches:
                        if start >= email_start and end <= email_end:
                            is_part_of_email = True
                            break
                    
                    if not is_part_of_email:
                        overlapping = False
                        for existing_start, existing_end, existing_type in matches:
                            if existing_type == 'phone':
                                if not (end <= existing_start or start >= existing_end):
                                    overlapping = True
                                    break
                        
                        if not overlapping:
                            matches.append((start, end, 'phone'))
                            stats['phone'] += 1
        
        for keyword in self.keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start, end = match.start(), match.end()
                
                is_part_of_other = False
                for other_start, other_end, other_type in matches:
                    if start >= other_start and end <= other_end:
                        is_part_of_other = True
                        break
                
                if not is_part_of_other:
                    matches.append((start, end, 'keyword'))
                    stats['keyword'] += 1
        
        matches.sort(key=lambda x: x[0])
        
        return {'matches': matches, 'stats': stats}
            
    def edit_selected_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        
        if item_data.get('state') == 'passed':
            reply = QMessageBox.question(self, "Item Passed", 
                                       "This item is marked as passed. Do you want to edit it anyway?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        current_text = item_data['full_text']
        
        dialog = EditDescriptionDialog(current_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            self.text_edit.setText(new_text)
            self.text_preview.setVisible(False)
            self.text_edit.setVisible(True)
            self.edit_mode = True
            
            if new_text != item_data['full_text']:
                item_data['state'] = 'edited'
                item_data['edited_text'] = new_text
                self.save_button.setEnabled(True)
            
            self.update_item_colors()
                
    def save_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        
        new_text = self.text_edit.toPlainText()
        
        try:
            item_data['desc_item'].setText(1, new_text)
            
            item_data['full_text'] = new_text
            item_data['original_text'] = new_text
            item_data['state'] = 'saved'
            
            if 'edited_text' in item_data:
                del item_data['edited_text']
            
            self.text_preview.setText(new_text)
            
            current_displayed_text = self.text_preview.toPlainText()
            matches_info = self.find_phone_matches(current_displayed_text)
            self.highlighter.set_matches(matches_info['matches'])
            
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
            self.save_button.setEnabled(False)
            
            self.update_item_colors()
            
            QMessageBox.information(self, "Success", "Description saved to tree.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save description: {str(e)}")
            
    def mark_as_passed(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        item_data['state'] = 'passed'
        
        if 'edited_text' in item_data:
            del item_data['edited_text']
        
        if self.edit_mode:
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
        
        self.save_button.setEnabled(False)
        
        self.update_item_colors()
            
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
        self.pass_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.text_preview.setVisible(True)
        self.text_edit.setVisible(False)
        self.edit_mode = False
        self.current_item_index = -1
        self.highlighter.set_matches([])