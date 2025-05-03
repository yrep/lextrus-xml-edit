from PySide6.QtCore import QThread, Signal, Slot, QObject
import time
import random


class Worker(QObject):
    progress_updated = Signal(int)
    finished = Signal(str)

    def __init__(self, tree, actions):
        super().__init__()
        self.tree = tree
        self.actions = actions

    @Slot()
    def run(self):
        task_type = ""
        try:
            if self.actions is not None:
                task_type = "action"
                for index, action in enumerate(self.actions):
                    method_name = action["action"]
                    method = getattr(self.tree, method_name)
                    # is_last_action = (index == len(self.actions) - 1)

                    # Call the method with the appropriate arguments
                    method(self.update_progress, action)

                    # if is_last_action:
                    #    self.finished.emit()  # Signal that all actions are done
            else:
                # method = getattr(self.parent().tab_scraping, 'begin_scraping')
                # method(self.test_method)
                task_type = "scraping"
                self.tree.parent.tab_scraping.begin_scraping(self.update_progress)
        except Exception as e:
            print(f"Exception in worker.run method: {e}")
        finally:
            self.finished.emit(task_type)

    def update_progress(self, value):
        self.progress_updated.emit(value)

    def test_method(self):
        print('test_method was called')
