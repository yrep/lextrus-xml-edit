from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtGui import QIcon, QAction

from sidebar_button import ScalableIconButton


class Sidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

        # Initialize the layout and widget
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setFixedWidth(56)

        # Create a button with an icon
        self.download_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}download.png"), "")
        self.open_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}xml.png"), "")
        self.save_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}save.png"), "")
        self.remove_node_type_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}delete-node.png"), "")
        self.add_single_subnode_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}add-subnode.png"), "")
        self.norm_price_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}coin.png"), "")
        self.trim_button = ScalableIconButton(QIcon(f"{self.parent.state.icons_path}trim.png"), "")

        # Add the button to the layout
        self.layout.addWidget(self.download_button)
        self.layout.addWidget(self.open_button)
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.remove_node_type_button)
        self.layout.addWidget(self.add_single_subnode_button)
        self.layout.addWidget(self.norm_price_button)
        self.layout.addWidget(self.trim_button)
        self.layout.addStretch()

        # Connect button click to the action
        self.download_button.clicked.connect(self.parent.download_action.trigger)
        self.open_button.clicked.connect(self.parent.open_xml_action.trigger)
        self.save_button.clicked.connect(self.parent.save_as_action.trigger)
        self.remove_node_type_button.clicked.connect(self.parent.remove_type_action.trigger)
        self.add_single_subnode_button.clicked.connect(self.parent.add_subnode_action.trigger)
        self.norm_price_button.clicked.connect(self.parent.norm_price_action.trigger)
        self.trim_button.clicked.connect(self.parent.remove_from_start_action.trigger)

        self.sidebar_stylesheet = """
        
            QPushButton {
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }
            
            QPushButton:hover {
                background: transparent;
                border: none;
            }
            
        """

        self.setStyleSheet(self.sidebar_stylesheet)



        # self.open_action = self.parent.open_xml_action

        # Create buttons
        # self.sidebar_open_button = QPushButton(QIcon("./icons/delete-node.png"), "")

        # Add buttons to the layout
        # self.layout.addWidget(self.sidebar_open_button)
        # self.layout.addStretch()

        # self.sidebar_open_button.clicked.connect(self.parent.open_xml_action)


