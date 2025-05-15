import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
os.sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.header_window import HeaderWindow

class FileSelectionWindow(QWidget):
    """Displays a list of CSV files for the user to select."""
    def __init__(self, output_dir, parent):
        super().__init__()
        self.output_dir = output_dir
        self.parent = parent
        self.open_header_windows = []  # Track multiple header windows

        self.setWindowTitle("Select a CSV File")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.load_csv_files()

        # Button to show log headers
        self.show_headers_button = QPushButton("Show Log Headers")
        self.show_headers_button.clicked.connect(self.show_log_headers)

        self.list_widget.itemDoubleClicked.connect(self.open_column_selection_window)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.show_headers_button)
        self.setLayout(layout)

    def load_csv_files(self):
        """Loads the list of CSV files from the output directory."""
        csv_files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv")]
        self.list_widget.addItems(csv_files)

    def open_column_selection_window(self, item):
        """Opens the column selection window for the selected file."""
        csv_file_path = os.path.join(self.output_dir, item.text())
        self.parent.show_column_selection(csv_file_path)

    def show_log_headers(self):
        """Opens a new window to display the log headers."""
        headers_file = os.path.join(self.output_dir, "headers.txt")
        if not os.path.exists(headers_file):
            QMessageBox.warning(self, "Headers File Not Found", "The headers.txt file is missing.")
            return

        header_window = HeaderWindow(headers_file)
        header_window.context_extracted.connect(self.parent.add_chat_context)  # <-- Connect here!
        self.open_header_windows.append(header_window)
        header_window.show()

        # Remove the window from the list when it is closed
        header_window.destroyed.connect(
            lambda: self.open_header_windows.remove(header_window)
        )