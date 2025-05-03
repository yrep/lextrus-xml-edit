from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QTreeWidget


class AppState(QObject):
    # Signals
    property_count_updated = Signal(int)
    current_property_node = None

    def __init__(self):
        super().__init__()
        self.__tree_widget = None     # Will hold the reference to QTreeWidget
        self.__property_count = 0     # Property nodes count
        self.__is_processing = False  # Processing status
        self.path_to_app = ''
        self.icons_path = ''
        self.opened_file = ''

    def set_tree_widget(self, tree_widget: QTreeWidget):
        self.__tree_widget = tree_widget

    def get_tree_widget(self) -> QTreeWidget:
        return self.__tree_widget

    def set_property_count(self, count: int):
        if count >= 0:
            self.__property_count = count
        else:
            self.__property_count = 0
        self.property_count_updated.emit(self.__property_count)
    
    def get_property_count(self) -> int:
        return self.__property_count
    
    def set_processing_status(self, status: bool):
        self.__is_processing = status

    def get_processing_status(self) -> bool:
        return self.__is_processing

