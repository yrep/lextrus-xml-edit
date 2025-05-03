import json
import re
import time
import urllib

import requests
from PySide6 import QtCore
from lxml import etree

from PySide6.QtGui import Qt, QAction
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QInputDialog, QMessageBox



class TreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setHeaderLabels(["Tag", "Value"])
        self.setColumnWidth(0, 200)
        self.setColumnWidth(1, 150)

        self.itemDoubleClicked.connect(self.edit_item)

        # Connect the context menu event
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)  # Qt.CustomContextMenu
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        # Create the context menu
        menu = QMenu(self)

        # Create an action to add a sub-item
        add_action = QAction("Add Subnode", self)
        add_action.triggered.connect(self.add_sub_item)

        # Create an action to remove the selected item
        remove_action = QAction("Remove Selected Node", self)
        remove_action.triggered.connect(self.remove_selected_item)

        # Add the action to the menu
        menu.addAction(add_action)
        menu.addAction(remove_action)

        # Show the menu at the cursor position
        menu.exec(self.viewport().mapToGlobal(pos))

    def add_sub_item(self):
        # Get the currently selected item
        selected_item = self.currentItem()
        if selected_item:
            # Prompt the user for the new sub-item name
            text, ok = QInputDialog.getText(self, "Add Subnode", "Enter new subnode name (only lowercase letters, numbers and _):")
            if ok and text:
                # Validate the input
                if self.validate_name(text):
                    # Create and add the new sub-item
                    new_sub_item = QTreeWidgetItem(selected_item, [text])
                    selected_item.addChild(new_sub_item)
                else:
                    # Show an error message if validation fails
                    QMessageBox.warning(self, "Invalid Name",
                                        "Please use only letters, numbers and underscores ( _ ). The starting symbol must be a letter.")
        else:
            QMessageBox.warning(self, "Warning", "Please select a node to add a sub-item.")

    def validate_name(self, name):
        return re.match(r'^[a-z][a-z0-9_]*$', name) is not None


    def remove_selected_item(self):
        # Get the currently selected item
        selected_item = self.currentItem()
        if selected_item:
            # Remove the selected item
            index = self.indexOfTopLevelItem(selected_item)
            if index != -1:
                self.takeTopLevelItem(index)

# LOADING XML
    def load_xml(self, xml_file):
        self.clear()

        tree = etree.parse(xml_file)
        root = tree.getroot()

        self.add_elements_to_tree(self.invisibleRootItem(), root)
        self.expandItem(self.invisibleRootItem())
        self.collapseAll()
        self.parent.state.set_property_count(self.count_properties())

    def add_elements_to_tree(self, parent_item, element):
        # Create a QTreeWidgetItem for the current XML element
        item = QTreeWidgetItem(parent_item, [element.tag, element.text.strip() if element.text else ""])

        # Add attributes as child nodes
        for attr_name, attr_value in element.attrib.items():
            QTreeWidgetItem(item, [f"{element.tag}{attr_name}", attr_value])

        # Add child elements
        for child in element:
            self.add_elements_to_tree(item, child)

    def add_single_node(self, parent, new_node):
        QTreeWidgetItem(parent, [new_node['tag'], new_node['text']])

# COUNT PROPERTIES
    def count_properties(self):
        return self.count_nodes_with_name("property") or 0

    def count_nodes_with_name(self, name):
        count = 0
        # Iterate through all top-level items
        for i in range(self.topLevelItemCount()):
            top_level_item = self.topLevelItem(i)
            # Iterate through children of the top-level item
            for j in range(top_level_item.childCount()):
                child_item = top_level_item.child(j)
                if child_item.text(0) == name:
                    count += 1
        return count

    def toggle_second_level_visibility(self):
        # Determine the current state of second-level items
        any_expanded = False
        for index in range(self.topLevelItemCount()):
            top_level_item = self.topLevelItem(index)
            for child_index in range(top_level_item.childCount()):
                second_level_item = top_level_item.child(child_index)
                if second_level_item.isExpanded():
                    any_expanded = True
                    break
            if any_expanded:
                break

        # Toggle the state based on the current state
        for index in range(self.topLevelItemCount()):
            top_level_item = self.topLevelItem(index)
            for child_index in range(top_level_item.childCount()):
                second_level_item = top_level_item.child(child_index)
                second_level_item.setExpanded(not any_expanded)  # Toggle state


# EDIT ITEM
    def edit_item(self, item, column):
        if column == 1:  # and self.current_editor_item == None:
            item.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.editItem(item, column)
            # self.current_editor_item = item


    def delete_selected_node_type(self):
        pass

#OPERATIONS

    # @staticmethod
    # def check_condition(condition, child_value, node_value):
    #     match condition:
    #         case "":
    #             return True
    #         case "equal":
    #             return node_value == child_value
    #         case "contains":
    #             return child_value in node_value
    #         case "does not contain":
    #             return child_value not in node_value

    def add_node_type(self, update_progress_callback, action_item):
        root = self.topLevelItem(0)
        # action_item = kwargs.get('action')
        parent_node_type = action_item["parent"]
        new_node_type = action_item["child"]
        initial_value = action_item["value"]
        total_items = self.parent.state.get_property_count()

        # # counter initial value takes current progress bar value in case it is not the first action
        # counter = self.parent.status_bar.progress_bar.value()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.text(0) == parent_node_type:
                QTreeWidgetItem(item, [new_node_type, initial_value])
            print(f"Updating progress bar: {(int((i + 1) / total_items * 100))})")
            update_progress_callback(int((i + 1) / total_items * 100))

    def remove_selected_item(self):
        # Get the currently selected item
        selected_items = self.selectedItems()
        if not selected_items:
            return  # No item selected

        # Assume we are only dealing with a single selected item for simplicity
        item_to_remove = selected_items[0]

        # Remove the item and all its children
        self.remove_item(item_to_remove)
        self.parent.state.set_property_count(self.count_properties())

    def remove_item(self, item: QTreeWidgetItem):
        if not item:
            return

        # Check if the item is a top-level item or a child item
        parent = item.parent()
        if parent:
            # Remove the item from its parent
            parent.removeChild(item)
        else:
            # Remove the item from the tree (it's a top-level item)
            index = self.indexOfTopLevelItem(item)
            if index != -1:
                self.takeTopLevelItem(index)

        # Optionally, you can also delete the item to free memory
        del item


    def remove_node_by_condition(self, update_progress_callback, action_item):
        root = self.topLevelItem(0)
        parent = action_item['parent']
        child = action_item['child']
        child_value = action_item['value']
        condition = action_item['condition']

        nodes_to_remove = []

        for i in range(root.childCount()):
            update_progress_callback(int((i + 1) / root.childCount() * 100))
            if root.child(i).text(0) == parent:
                node_to_remove = root.child(i)
                if self.check_children_for_condition(node_to_remove, child, condition, child_value):
                    nodes_to_remove.append(node_to_remove)

            else:
                pass

        for node in nodes_to_remove:
            self.remove_item(node)

        self.parent.state.set_property_count(self.count_properties())

    def compare_db_media_links_to_tree(self, update_progress_callback, action_item=None):
        url = 'https://aparteu.com/api/v1/get-info/'
        body = {'action': 'get_lextrus_media_urls'}

        try:
            # Send the POST request with the body as JSON
            response = requests.post(url, json=body)
            print(body)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()  # Parse JSON response
            if data:
                self.iterate_over_media_links(data)
            #QMessageBox.information(None, "Response", str(data))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(None, "Error", str(e))


    def iterate_over_media_links(self, data):
        if self.topLevelItemCount() > 0:
            links_db = data
            if len(links_db) > 0:


                links_tree = self.get_ids_and_media_links()

                # print(str(type(links_db)))
                # print(str(type(links_tree)))

                links_tree.sort(key=lambda x: x['id'])
                links_db.sort(key=lambda x: x['id_in'])

                # print(str(len(links_db)))
                # print(str(len(links_tree)))

                broken_links_object = compare_link_lists(links_tree, links_db)

                not_found_list = broken_links_object['ids_not_found']
                broken_links_list = broken_links_object['ids_broken_links']

                not_found_list_string = ",".join(not_found_list)
                broken_links_list_string = ",".join(broken_links_list)

                self.parent.tab_check_media_links.result_property_ids_nf.setText(not_found_list_string)
                self.parent.tab_check_media_links.result_property_ids_bl.setText(broken_links_list_string)

                # for link in links_tree:
                #     print(link)
            else:
                QMessageBox.critical(None, "Error", "Server returned 0 media links.")


            #QMessageBox.critical(None, "Error", root_item.text(0))
        else:
            QMessageBox.critical(None, "Error", "Load XML file first.")

    def get_ids_and_media_links(self):
        root_item = self.topLevelItem(0)
        tree_link_list = []

        for i in range(root_item.childCount()):
            property_item = root_item.child(i)

            if property_item.text(0) == 'property':
                id = property_item.child(0).text(1)
                # print("ID: " + str(id))
                links = []

                images_node = self.get_child_by_name(property_item, 'images')
                # print("Image_node: " + str(images_node))

                if images_node:  # Check if images_node is not None
                    # print("Image_node count: " + str(images_node.childCount()))

                    for index in range(images_node.childCount()):
                        image = images_node.child(index)

                        link = self.get_child_by_name(image, 'url')  # Fix indentation here
                        if link is not None:
                            cleaned_link = self.remove_link_suffix(link.text(1))
                            links.append(cleaned_link)  # Make sure to call text() to get the URL string
                else:
                    print("No images node found for property: " + str(id))

                tree_item = {
                    "id": id,
                    "links": links
                }
                tree_link_list.append(tree_item)

        return tree_link_list

    def remove_link_suffix(self, link_url):
        suffix = '/ourl='
        if link_url.endswith(suffix):
            return link_url[:-len(suffix)]
        return link_url

    def check_children_for_condition(self, item: QTreeWidgetItem, child_name: str, condition: str, val: str) -> bool:
        # print('############## Enterng: check_children_for_condition ###############')
        # print("Item: " + item.text(0))
        # print("Child: " + child_name)
        # print("Condition: " + condition)
        # print("Val: " + val)

        # Iterate over the children of the current item
        for i in range(item.childCount()):
            # print(f'Enterng for loop {i} with total count {item.childCount()} in check_children_for_condition')
            child = item.child(i)
            # print("Child: " + item.child(i).text(0))

            # Recursively check children
            if child.childCount() > 0:
                # print("Child has children: " + str(child.childCount()))
                if self.check_children_for_condition(child, child_name, condition, val):
                    # print("--- For Child returned true: " + str(child.text(0)))
                    return True

            # Check if the child has the specified name
            if child.text(0) == child_name:
                child_value = child.text(1)
                # print("Child value: " + child_value)
                if condition == 'equal':
                    # print("??? Compare child value: " + child_value + " and " + val)
                    if child_value == val:
                        # print("+++ Success: they are equal")
                        return True
                elif condition == 'contains':
                    if val in child_value:
                        return True
                elif condition == 'does not contain':
                    if val not in child_value:
                        return True
                else:
                    raise ValueError(f"Unsupported condition: {condition}")

        # Return False if no matching child is found
        return False


    def modify_node_type(self, progress_callback, action_item):
        parent = action_item["parent"]
        child = action_item["child"]
        child_value = action_item["value"]
        condition = action_item["condition"]
        new_value = action_item["new_value"]
        root = self.topLevelItem(0)
        total_items = self.parent.state.get_property_count()
        for i in range(root.childCount()):

            item = root.child(i)
            if item.text(0) == parent:
                child_node_to_change = self.get_child_by_name(item, child)
                if self.check_condition(condition, child_value, child_node_to_change.text(1)):
                    child_node_to_change.setText(1, new_value)
                else:
                    pass
            progress_callback(int((i + 1) / total_items * 100))

    def process_price_nodes(self):
        root = self.invisibleRootItem()

        def traverse(item, level):

            if level == 3 and item.text(0) == 'price' and item.text(1) != '':
                try:
                    value = int(float(item.text(1)))
                    print(value)
                    if value % 1000 != 0:
                        value = ((value // 1000) + 1) * 1000
                    item.setText(1, str(value))
                except ValueError:
                    pass

            elif level < 3:
                for i in range(item.childCount()):
                    traverse(item.child(i), level + 1)

        for i in range(root.childCount()):
            traverse(root.child(i), 1)


    def get_child_by_name(self, parent, name):
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.text(0) == name:
                return child
        return None

    def save_as_xml(self, file_name):
        self.clean_description()
        root_item = self.invisibleRootItem().child(0)
        root = self.build_xml_element(root_item)
        tree = etree.ElementTree(root)
        tree.write(file_name)

    def build_xml_element(self, item):
        elem = etree.Element(item.text(0))
        elem.text = item.text(1)
        for i in range(item.childCount()):
            child = item.child(i)
            elem.append(self.build_xml_element(child))
        return elem

    def save_as_json(self, file_name):
        root_item = self.invisibleRootItem().child(0)
        root = self.build_json_dict(root_item)
        with open(file_name, 'w') as json_file:
            json.dump(root, json_file, indent=4)

    def build_json_dict(self, item):
        result = {"tag": item.text(0), "text": item.text(1), "children": []}
        for i in range(item.childCount()):
            child = item.child(i)
            result["children"].append(self.build_json_dict(child))
        return result

    def clean_description(self):
        root = self.topLevelItem(0)
        for i in range(root.childCount()):
            property_node = root.child(i)

            desc_node = find_child_by_text(property_node, "desc")
            if desc_node:
                en_node = desc_node.child(0)

                if en_node and en_node.text(0) == 'en':
                    original_text = en_node.text(1)
                    lines = original_text.splitlines()

                    if lines:
                        cleaned_first_line = clean_text(lines[0])
                        lines[0] = cleaned_first_line

                    updated_text = "\n".join(lines)
                    en_node.setText(1, updated_text)

    def trim_tree(self, parent_item, number, position, action):
        """
        Trims or preserves child items in the QTreeWidget based on the given number, position, and action.

        :param parent_item: The parent QTreeWidgetItem (usually the root item).
        :param number: The number of items to remove or preserve.
        :param position: Whether to trim from the 'start' or 'end'.
        :param action: Action to perform - 'remove' or 'preserve'.
        """
        child_items = [parent_item.child(i) for i in range(parent_item.childCount())]

        if position == "start":
            # Remove from start or preserve from start
            if action == "remove":
                child_items = child_items[number:]  # Remove the first N items
            elif action == "preserve":
                child_items = child_items[:number]  # Preserve the first N items
        elif position == "end":
            # Remove from end or preserve from end
            if action == "remove":
                child_items = child_items[:-number]  # Remove the last N items
            elif action == "preserve":
                child_items = child_items[-number:]  # Preserve the last N items

        # Clear current children and add the remaining child items
        parent_item.takeChildren()
        for item in child_items:
            parent_item.addChild(item)

        # Optionally, you could update the count of remaining properties, or any other UI elements
        self.expandItem(parent_item)  # Expand the root item after modification

        self.parent.state.set_property_count(self.count_properties())



def find_child_by_text(parent_item, text):
    for i in range(parent_item.childCount()):
        child = parent_item.child(i)
        if child.text(0) == text:
            return child
    return None

def clean_text(text):
    # replacements = [
    #     "? ",
    #     " ?",
    #     "&quot;",
    #     "Property ID: ",
    #     "Ref: ",
    #     "?",
    # ]
    #
    # for pattern in replacements:
    #     text = text.replace(pattern, "")
    #
    # text = re.sub(r" {2,}", " ", text)

    replacements = [
        r"\? ",
        r" \?",
        r"&quot;",
        r"Property ID: ",
        r"Ref: ",
        r"\?",
    ]

    pattern = "|".join(replacements)

    text = re.sub(pattern, "", text)

    # remove all text after (id)
    text = re.sub(r"(\(\d+\)).*", r"\1", text)

    # remove starting " – €" and ending "+VAT"
    text = re.sub(r" – €.*?\+VAT", "", text)

    text = re.sub(r'\s+', ' ', text)

    text = text.lstrip('\uFE0F \u200B')

    #text = re.sub(r'^[\s\u200B-\u200D\uFEFF]+|[\s\u200B-\u200D\uFEFF]+$', '', text)
    # text = text.replace('\uFE0F', '')
    # text = text.lstrip('\u200B')
    #text = re.sub(r'^\s*', '', text)

    return text

def compare_link_lists(links_tree_sorted, links_db_sorted):

    links_tree_dict = [item['id'] for item in links_tree_sorted]

    print(links_tree_dict)

    results = {
        'ids_not_found': [],
        'ids_broken_links': [],
    }

    for item_db in links_db_sorted:
        db_id = item_db['id_in']
        db_links_obj = item_db['media']

        db_links = [item['url'] for item in db_links_obj]

        # print("Media list: " + str(db_links))

        if db_id in links_tree_dict:
            tree_item = find_item_by_value(links_tree_sorted, 'id', db_id)
            tree_item_links = tree_item['links']

            if set(tree_item_links) == set(db_links):
                pass
            else:
                results['ids_broken_links'].append(db_id)

        else:
            results['ids_not_found'].append(db_id)

    return results


def find_item_by_value(item_list, key, value):
    for item in item_list:
        if item.get(key) == value:
            return item
    return None