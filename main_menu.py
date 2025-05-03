from PySide6.QtWidgets import QMenuBar
from PySide6.QtCore import Qt


class MainMenu(QMenuBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.create_menus()

    def create_menus(self):
        file_menu = self.addMenu("File")
        file_menu.addAction(self.parent.download_action)
        file_menu.addAction(self.parent.open_xml_action)
        file_menu.addAction(self.parent.save_as_action)
        file_menu.addAction(self.parent.clear_tree_action)

        edit_menu = self.addMenu("Edit")
        edit_menu.addAction(self.parent.edit_node_action)
        edit_menu.addAction(self.parent.remove_type_action)
        edit_menu.addAction(self.parent.add_subnode_action)
        edit_menu.addAction(self.parent.norm_price_action)
        edit_menu.addAction(self.parent.remove_from_start_action)

        edit_menu = self.addMenu("View")
        edit_menu.addAction(self.parent.toggle_second_level_visibility_action)
