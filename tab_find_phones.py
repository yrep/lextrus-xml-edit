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
        self.matches = []  # Список кортежей (start_pos, end_pos, match_type)
        self.formats = {
            'phone': QTextCharFormat(),
            'email': QTextCharFormat(),
            'cyprus': QTextCharFormat(),
            'keyword': QTextCharFormat()
        }
        
        # Настраиваем форматы
        self.formats['phone'].setBackground(QBrush(QColor(255, 255, 200)))  # Светло-желтый для телефонов
        self.formats['email'].setBackground(QBrush(QColor(200, 255, 200)))  # Светло-зеленый для email
        self.formats['cyprus'].setBackground(QBrush(QColor(200, 200, 255)))  # Светло-синий для кода Кипра
        self.formats['keyword'].setBackground(QBrush(QColor(255, 200, 200)))  # Светло-красный для ключевых слов
        
    def set_matches(self, matches):
        self.matches = matches
        self.rehighlight()
        
    def highlightBlock(self, text):
        if not self.matches:
            return
            
        # Получаем позиции начала и конца текущего блока
        block_start = self.currentBlock().position()
        block_end = block_start + len(text)
        
        # Находим совпадения, которые попадают в этот блок
        for match_start, match_end, match_type in self.matches:
            if match_start >= block_start and match_end <= block_end:
                # Преобразуем глобальные позиции в позиции внутри блока
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
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        description = QLabel("Finds objects containing phone numbers or email addresses in description")
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
        self.edit_button.setStyleSheet("background-color: #90EE90;")
        self.edit_button.setCursor(Qt.PointingHandCursor)
        self.edit_button.clicked.connect(self.edit_selected_description)
        self.edit_button.setEnabled(False)
        
        self.pass_button = QPushButton("Pass")
        self.pass_button.setStyleSheet("background-color: #ADD8E6;")
        self.pass_button.setCursor(Qt.PointingHandCursor)
        self.pass_button.clicked.connect(self.mark_as_passed)
        self.pass_button.setEnabled(False)
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.clicked.connect(self.save_description)
        self.save_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.setCursor(Qt.PointingHandCursor)
        self.clear_button.clicked.connect(self.clear_results)
        
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
        self.original_text = ""
        self.edit_mode = False
        
    def on_item_selected(self, list_item):
        if not list_item:
            return
        
        item_index = list_item.data(Qt.UserRole)
        if item_index is None or item_index >= len(self.found_items):
            return
        
        self.current_item_index = item_index
        item_data = self.found_items[item_index]
        
        self.original_text = item_data.get('original_text', item_data['full_text'])
        
        text_changed = item_data.get('text_changed', False)
        
        self.edit_button.setEnabled(True)
        self.pass_button.setEnabled(True)
        self.save_button.setEnabled(text_changed)
        
        if text_changed:
            self.save_button.setStyleSheet("background-color: #FFA500;")
        else:
            self.save_button.setStyleSheet("")
        
        if text_changed or self.edit_mode:
            display_text = item_data.get('edited_text', item_data['full_text'])
            self.text_edit.setText(display_text)
            self.text_preview.setVisible(False)
            self.text_edit.setVisible(True)
            self.edit_mode = True
        else:
            display_text = item_data['full_text']
            self.text_preview.setText(display_text)
            self.highlighter.set_matches(item_data['matches'])
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
        
    def on_text_changed(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
            
        new_text = self.text_edit.toPlainText()
        item_data = self.found_items[self.current_item_index]
        
        original_text = item_data.get('original_text', item_data['full_text'])
        text_changed = new_text != original_text
        
        item_data['text_changed'] = text_changed
        if text_changed:
            item_data['edited_text'] = new_text
        
        self.save_button.setEnabled(text_changed)
        
        if text_changed:
            self.save_button.setStyleSheet("background-color: #FFA500;")
        
        self.update_item_colors()
        
    def update_item_colors(self):
        for i in range(self.id_list.count()):
            item = self.id_list.item(i)
            item_index = item.data(Qt.UserRole)
            if item_index is not None and item_index < len(self.found_items):
                item_data = self.found_items[item_index]
                if item_data.get('status') == 'saved':
                    item.setBackground(QColor(144, 238, 144))
                elif item_data.get('status') == 'passed':
                    item.setBackground(QColor(173, 216, 230))
                elif item_data.get('text_changed', False):
                    item.setBackground(QColor(255, 165, 0))
                else:
                    item.setBackground(Qt.transparent)
        
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
        cyprus_count = 0
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
                matches_info = self.find_phone_matches(description)
                matches = matches_info['matches']
                stats = matches_info['stats']
                
                if matches:
                    found_count += 1
                    
                    # Обновляем статистику
                    if stats.get('cyprus', 0) > 0:
                        cyprus_count += 1
                    if stats.get('email', 0) > 0:
                        email_count += 1
                    if stats.get('phone', 0) > 0:
                        phone_count += 1
                    
                    item_data = {
                        'id': property_id,
                        'full_text': description,
                        'original_text': description,
                        'desc_item': en_item,
                        'matches': matches,
                        'stats': stats,
                        'status': '',
                        'text_changed': False,
                        'has_email': stats.get('email', 0) > 0,
                        'has_phone': stats.get('phone', 0) > 0,
                        'has_cyprus': stats.get('cyprus', 0) > 0
                    }
                    self.found_items.append(item_data)
                    
                    # Обновляем текст элемента списка
                    item_text = f"ID: {property_id} - {len(matches)} matches"
                    
                    type_indicators = []
                    if stats.get('cyprus', 0) > 0:
                        type_indicators.append(f"{stats['cyprus']} Cyprus")
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
        
        # Обновляем статистику
        stats_text = f"Found: {found_count} objects"
        if cyprus_count > 0:
            stats_text += f", {cyprus_count} with Cyprus code (357)"
        if phone_count > 0:
            stats_text += f", {phone_count} with phones"
        if email_count > 0:
            stats_text += f", {email_count} with emails"
        if found_count > 0:
            total_matches = sum(len(item['matches']) for item in self.found_items)
            stats_text += f" (total matches: {total_matches})"
        
        self.stats_label.setText(stats_text)
        self.copy_button.setEnabled(len(self.found_items) > 0)
        self.edit_button.setEnabled(False)
        self.pass_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet("")
        self.find_button.setEnabled(True)
        
        if self.found_items and self.id_list.count() > 0:
            self.id_list.setCurrentRow(0)
            self.on_item_selected(self.id_list.item(0))
        
        if found_count > 0:
            message = f"Found {found_count} objects with contacts:\n"
            if cyprus_count > 0:
                message += f"• {cyprus_count} with Cyprus code (357)\n"
            if phone_count > 0:
                message += f"• {phone_count} with phone numbers\n"
            if email_count > 0:
                message += f"• {email_count} with email addresses\n"
            total_matches = sum(len(item['matches']) for item in self.found_items)
            message += f"• Total matches: {total_matches}"
            
            QMessageBox.information(self, "Search Complete", message)
        else:
            QMessageBox.information(self, "Search Complete", "No contacts found.")
            
    def find_phone_matches(self, text):
        if not text:
            return {'matches': [], 'stats': {}}
        
        matches = []
        stats = {
            'phone': 0,
            'email': 0,
            'cyprus': 0,
            'keyword': 0
        }
        
        # 1. Ищем email адреса
        email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\.[a-zA-Z]{2,}',
        ]
        
        for pattern in email_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                matches.append((match.start(), match.end(), 'email'))
                stats['email'] += 1
        
        # 2. Ищем код 357 (Кипр) - отдельно подчеркиваем каждое вхождение
        for match in re.finditer(r'357', text):
            matches.append((match.start(), match.end(), 'cyprus'))
            stats['cyprus'] += 1
        
        # 3. Ищем номера телефонов в различных форматах
        
        # Телефоны с + и 7+ цифр
        plus_pattern = r'\+\d[\d\s\-\(\)]{6,}\d'
        for match in re.finditer(plus_pattern, text):
            # Проверяем что в совпадении есть минимум 7 цифр
            digit_count = sum(1 for c in match.group() if c.isdigit())
            if digit_count >= 7:
                matches.append((match.start(), match.end(), 'phone'))
                stats['phone'] += 1
        
        # Телефоны без + но с 7+ цифр
        digit_pattern = r'\d[\d\s\-\(\)]{5,}\d'
        for match in re.finditer(digit_pattern, text):
            digit_count = sum(1 for c in match.group() if c.isdigit())
            if digit_count >= 7:
                # Проверяем что это не часть email и не код 357
                is_part_of_email = False
                for email_start, email_end, _ in matches:
                    if match.start() >= email_start and match.end() <= email_end:
                        is_part_of_email = True
                        break
                
                is_part_of_cyprus = False
                for cyprus_start, cyprus_end, _ in [(s, e, t) for (s, e, t) in matches if t == 'cyprus']:
                    if match.start() >= cyprus_start and match.end() <= cyprus_end:
                        is_part_of_cyprus = True
                        break
                
                if not is_part_of_email and not is_part_of_cyprus:
                    matches.append((match.start(), match.end(), 'phone'))
                    stats['phone'] += 1
        
        # Стандартные форматы телефонов
        standard_patterns = [
            r'\(\d{3}\)\s*\d{3}[- ]?\d{4}',
            r'\+\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4}',
            r'00\d{1,3}[\s\-]?\d{1,4}[\s\-]?\d{3}[\s\-]?\d{4}',
        ]
        
        for pattern in standard_patterns:
            for match in re.finditer(pattern, text):
                # Проверяем что это не часть уже найденного совпадения
                overlapping = False
                for existing_start, existing_end, _ in matches:
                    if not (match.end() <= existing_start or match.start() >= existing_end):
                        overlapping = True
                        break
                
                if not overlapping:
                    matches.append((match.start(), match.end(), 'phone'))
                    stats['phone'] += 1
        
        # 4. Ищем ключевые слова и подсвечиваем их
        keywords = ['contacts', 'office', 'phone', 'mobile', 'mob', 'tel', 'fax', 'email', 'call us',
                   'contact us', 'telephone', 'cell', 'whatsapp', 'viber', 'telegram', 'skype']
        
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Проверяем что это не часть уже найденного совпадения
                overlapping = False
                for existing_start, existing_end, _ in matches:
                    if not (match.end() <= existing_start or match.start() >= existing_end):
                        overlapping = True
                        break
                
                if not overlapping:
                    matches.append((match.start(), match.end(), 'keyword'))
                    stats['keyword'] += 1
        
        # Сортируем совпадения по позиции начала
        matches.sort(key=lambda x: x[0])
        
        return {'matches': matches, 'stats': stats}
            
    def edit_selected_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        
        if item_data.get('status') == 'passed':
            reply = QMessageBox.question(self, "Item Passed", 
                                       "This item is marked as passed. Do you want to edit it anyway?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        if item_data.get('text_changed', False):
            current_text = item_data.get('edited_text', item_data['full_text'])
        else:
            current_text = item_data['full_text']
        
        dialog = EditDescriptionDialog(current_text, self)
        if dialog.exec() == QDialog.Accepted:
            new_text = dialog.get_text()
            self.text_edit.setText(new_text)
            self.text_preview.setVisible(False)
            self.text_edit.setVisible(True)
            self.edit_mode = True
            self.on_text_changed()
                
    def save_description(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        
        if item_data.get('text_changed', False):
            new_text = item_data.get('edited_text', item_data['full_text'])
        else:
            new_text = item_data['full_text']
        
        try:
            item_data['desc_item'].setText(1, new_text)
            item_data['full_text'] = new_text
            item_data['original_text'] = new_text
            
            matches_info = self.find_phone_matches(new_text)
            item_data['matches'] = matches_info['matches']
            item_data['stats'] = matches_info['stats']
            item_data['status'] = 'saved'
            item_data['text_changed'] = False
            
            if 'edited_text' in item_data:
                del item_data['edited_text']
            
            self.text_preview.setText(new_text)
            self.highlighter.set_matches(item_data['matches'])
            
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
            self.save_button.setEnabled(False)
            self.save_button.setStyleSheet("")
            
            self.update_item_colors()
            
            QMessageBox.information(self, "Success", "Description saved to tree.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save description: {str(e)}")
            
    def mark_as_passed(self):
        if self.current_item_index < 0 or self.current_item_index >= len(self.found_items):
            return
        
        item_data = self.found_items[self.current_item_index]
        item_data['status'] = 'passed'
        item_data['text_changed'] = False
        
        if 'edited_text' in item_data:
            del item_data['edited_text']
        
        if self.edit_mode:
            self.text_preview.setVisible(True)
            self.text_edit.setVisible(False)
            self.edit_mode = False
            self.save_button.setEnabled(False)
            self.save_button.setStyleSheet("")
        
        self.update_item_colors()
        self.on_item_selected(self.id_list.item(self.current_item_index))
            
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
        self.save_button.setStyleSheet("")