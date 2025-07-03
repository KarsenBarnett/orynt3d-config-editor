import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QLineEdit,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QCheckBox,
    QScrollArea, QFrame, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import your existing modules here
from core import scanner, indexer, mapper, editor, generator, logger

def load_attribute_yaml():
    # Use your mapper's method or replicate here if needed
    return mapper.load_attribute_yaml()

class MultiSelectComboBox(QComboBox):
    def __init__(self, items):
        super().__init__()
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        self.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.checked_items = set()
        self.items = items

        # Store mapping of index to item text for checkbox access
        for item in self.items:
            self.addItem(item)
        self.model().itemChanged.connect(self.handle_item_changed)

    def handle_item_changed(self, item):
        text = item.text()
        if item.checkState() == Qt.Checked:
            self.checked_items.add(text)
        else:
            self.checked_items.discard(text)

    def showPopup(self):
        for i in range(self.count()):
            item = self.model().item(i)
            if item.text() in self.checked_items:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
        super().showPopup()

    def checked_values(self):
        return list(self.checked_items)

    def set_checked(self, values):
        self.checked_items = set(values)
        for i in range(self.count()):
            item = self.model().item(i)
            item.setCheckState(Qt.Checked if item.text() in self.checked_items else Qt.Unchecked)


class ManualReviewPanel(QWidget):
    def __init__(self, review_queue, attribute_yaml, save_callback):
        super().__init__()
        self.review_queue = review_queue
        self.attribute_yaml = attribute_yaml
        self.save_callback = save_callback
        self.current_index = 0
        self.log_lines = []

        self.init_ui()
        if self.review_queue:
            self.load_next_item()
        else:
            self.log("Review queue is empty.")

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header for folder path
        self.folder_label = QLabel("Folder: (none)")
        self.folder_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.folder_label)

        # Scroll area for attributes
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        layout.addWidget(self.scroll_area, 1)

        self.attrs_widget = QWidget()
        self.attrs_layout = QVBoxLayout()
        self.attrs_widget.setLayout(self.attrs_layout)
        self.scroll_area.setWidget(self.attrs_widget)

        # Filter input for attribute keys
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filter attributes:")
        filter_layout.addWidget(filter_label)
        self.filter_input = QLineEdit()
        self.filter_input.textChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)

        # Attribute controls dict: key -> MultiSelectComboBox
        self.attr_controls = {}

        # Build controls for all attribute keys
        for key, values in sorted(self.attribute_yaml.items()):
            key_label = QLabel(key.capitalize())
            key_label.setToolTip(f"Attribute key: {key}")
            combo = MultiSelectComboBox(values)
            self.attrs_layout.addWidget(key_label)
            self.attrs_layout.addWidget(combo)
            self.attr_controls[key] = combo

        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.prev_item)
        nav_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_item)
        nav_layout.addWidget(self.next_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_current)
        nav_layout.addWidget(self.save_btn)

        layout.addLayout(nav_layout)

        # Logs panel
        log_label = QLabel("Logs:")
        layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        layout.addWidget(self.log_text)

        # Export logs button
        self.export_logs_btn = QPushButton("Export Logs")
        self.export_logs_btn.clicked.connect(self.export_logs)
        layout.addWidget(self.export_logs_btn)

    def log(self, message):
        self.log_lines.append(message)
        self.log_text.append(message)

    def load_next_item(self):
        if self.current_index >= len(self.review_queue):
            self.log("Reached end of review queue.")
            self.clear_fields()
            return
        folder, attrs = self.review_queue[self.current_index]
        self.folder_label.setText(f"Folder: {folder}")
        self.log(f"Reviewing {folder}")

        # Populate controls with existing values or clear if missing
        for key, combo in self.attr_controls.items():
            values = attrs.get(key, [])
            combo.set_checked(values)

        self.log(f"Loaded attributes: {attrs}")

    def clear_fields(self):
        self.folder_label.setText("Folder: (none)")
        for combo in self.attr_controls.values():
            combo.set_checked([])

    def save_current(self):
        if self.current_index >= len(self.review_queue):
            self.log("No item to save.")
            return
        folder, _ = self.review_queue[self.current_index]
        new_attrs = {}
        for key, combo in self.attr_controls.items():
            checked = combo.checked_values()
            if checked:
                new_attrs[key] = checked
        self.review_queue[self.current_index] = (folder, new_attrs)
        self.log(f"Saved attributes for {folder}: {new_attrs}")

        # Call the real save/generate config callback
        try:
            self.save_callback(folder, new_attrs)
            self.log(f"Config generated for {folder}")
        except Exception as e:
            self.log(f"Error saving config for {folder}: {e}")

    def prev_item(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_next_item()
        else:
            self.log("Already at the first item.")

    def next_item(self):
        if self.current_index < len(self.review_queue) - 1:
            self.current_index += 1
            self.load_next_item()
        else:
            self.log("Already at the last item.")

    def export_logs(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Export Logs", "review_logs.txt", "Text Files (*.txt);;All Files (*)", options=options)
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.log_lines))
                self.log(f"Logs exported to {filename}")
            except Exception as e:
                self.log(f"Failed to export logs: {e}")

    def apply_filter(self, text):
        text = text.strip().lower()
        for key, combo in self.attr_controls.items():
            show = text in key.lower()
            combo.setVisible(show)
            # Also show/hide label, assuming it is the previous widget in layout
            idx = self.attrs_layout.indexOf(combo)
            if idx > 0:
                label_widget = self.attrs_layout.itemAt(idx - 1).widget()
                if label_widget:
                    label_widget.setVisible(show)

class MainWindow(QMainWindow):
    def __init__(self, review_queue, attribute_yaml):
        super().__init__()
        self.setWindowTitle("Orynt3D Attribute Manual Review")
        self.resize(850, 750)
        self.review_panel = ManualReviewPanel(review_queue, attribute_yaml, self.save_config)
        self.setCentralWidget(self.review_panel)

        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        load_queue_action = file_menu.addAction("Load Review Queue...")
        load_queue_action.triggered.connect(self.load_review_queue)

        export_logs_action = file_menu.addAction("Export Logs...")
        export_logs_action.triggered.connect(self.review_panel.export_logs)

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def save_config(self, folder, attributes):
        # Use your generator module's function here
        generator.generate_config(folder, attributes)
        logger.log(f"Generated config for {folder}")

    def load_review_queue(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open Review Queue File", "", "JSON Files (*.json);;All Files (*)", options=options)
        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    queue = json.load(f)
                # Validate queue format: list of [folder, attributes] pairs
                if not isinstance(queue, list) or not all(isinstance(i, list) and len(i) == 2 for i in queue):
                    raise ValueError("Invalid review queue format.")
                self.review_panel.review_queue = queue
                self.review_panel.current_index = 0
                self.review_panel.load_next_item()
                self.review_panel.log(f"Loaded review queue from {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading Queue", f"Failed to load queue:\n{e}")

def run_gui(review_queue=None):
    if review_queue is None:
        review_queue = []  # Or preload from somewhere
    app = QApplication(sys.argv)
    attribute_yaml = load_attribute_yaml()
    main_win = MainWindow(review_queue, attribute_yaml)
    main_win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # Example: start with empty queue or load from your app
    run_gui()
