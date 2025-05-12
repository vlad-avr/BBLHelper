from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
import os

class HeaderWindow(QWidget):
    """Displays the log headers in a table format."""
    def __init__(self, headers_file):
        super().__init__()

        self.setWindowTitle(f"Log Headers - {os.path.basename(headers_file)}")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()
        self.table = QTableWidget()
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