import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget

class FileSelectionWindow(QWidget):
    """Displays a list of CSV files for the user to select."""
    def __init__(self, output_dir, parent):
        super().__init__()
        self.output_dir = output_dir
        self.parent = parent

        self.setWindowTitle("Select a CSV File")
        self.setGeometry(200, 200, 400, 300)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.load_csv_files()

        self.list_widget.itemDoubleClicked.connect(self.open_column_selection_window)

        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def load_csv_files(self):
        """Loads the list of CSV files from the output directory."""
        csv_files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv")]
        self.list_widget.addItems(csv_files)

    def open_column_selection_window(self, item):
        """Opens the column selection window for the selected file."""
        csv_file_path = os.path.join(self.output_dir, item.text())
        self.parent.show_column_selection(csv_file_path)