from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
import os

class HeaderWindow(QWidget):
    """Displays the log headers in a table format."""
    context_extracted = pyqtSignal(str)

    def __init__(self, headers_file):
        super().__init__()

        self.setWindowTitle(f"Log Headers - {os.path.basename(headers_file)}")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_header_context_menu)
        self.load_headers(headers_file)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_headers(self, headers_file):
        """Loads the headers from the file and displays them in a table."""
        with open(headers_file, "r") as file:
            lines = file.readlines()

        # Parse headers into key-value pairs
        headers = [line.strip().split(":", 1) for line in lines if ":" in line]

        # Set up the table
        self.table.setRowCount(len(headers))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Name", "Value"])

        for row, (name, value) in enumerate(headers):
            self.table.setItem(row, 0, QTableWidgetItem(name.strip()))
            self.table.setItem(row, 1, QTableWidgetItem(value.strip()))

    def show_header_context_menu(self, pos):
        menu = QMenu(self)
        add_context_action = QAction("Add context to chat", self)
        add_context_action.triggered.connect(self.add_header_selection_to_chat_context)
        menu.addAction(add_context_action)
        menu.exec(self.table.mapToGlobal(pos))

    def add_header_selection_to_chat_context(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            return

        sel = selected_ranges[0]
        rows = range(sel.topRow(), sel.bottomRow() + 1)
        # Always both columns (Name, Value)
        headers = [self.table.horizontalHeaderItem(col).text() for col in range(self.table.columnCount())]
        extracted = ["\t".join(headers)]

        for row in rows:
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            extracted.append("\t".join(row_data))

        context_str = "\n".join(extracted)
        self.context_extracted.emit(context_str)