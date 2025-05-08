import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox, QListWidget
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.converter import convert_bbl_to_csv  # Import the converter logic

class TableWindow(QWidget):
    """Displays the selected CSV log data as a table."""
    def __init__(self, csv_file):
        super().__init__()

        self.setWindowTitle(f"Blackbox Log Data - {os.path.basename(csv_file)}")
        self.setGeometry(150, 150, 900, 500)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.load_csv(csv_file)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_csv(self, csv_file):
        """Loads CSV data into the table widget."""
        df = pd.read_csv(csv_file)
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.table.setItem(row, col, item)

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

        self.list_widget.itemDoubleClicked.connect(self.open_csv_file)

        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def load_csv_files(self):
        """Loads the list of CSV files from the output directory."""
        csv_files = [f for f in os.listdir(self.output_dir) if f.endswith(".csv")]
        self.list_widget.addItems(csv_files)

    def open_csv_file(self, item):
        """Opens the selected CSV file in a new table window without closing the list."""
        csv_file_path = os.path.join(self.output_dir, item.text())
        self.parent.show_table(csv_file_path)

class MainWindow(QMainWindow):
    """Main Window with file selection and processing."""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UAV Blackbox Analyzer")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.label = QLabel("Select an option:")
        self.label.setStyleSheet("font-size: 14px;")

        # Button to decode a new .bbl file
        self.decode_button = QPushButton("Decode New Blackbox Log (.bbl)")
        self.decode_button.clicked.connect(self.open_file_dialog)

        # Button to open an already decoded folder
        self.open_folder_button = QPushButton("Open Decoded Folder")
        self.open_folder_button.clicked.connect(self.open_decoded_folder)

        layout.addWidget(self.label)
        layout.addWidget(self.decode_button)
        layout.addWidget(self.open_folder_button)
        central_widget.setLayout(layout)

        # Keep track of open TableWindows
        self.open_windows = []

    def open_file_dialog(self):
        """Opens a file dialog to select a .bbl log file and process it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Blackbox Log File", "", "Blackbox Logs (*.bbl);;All Files (*)"
        )
        if file_path:
            # Ask the user to select or create a folder for the output
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Output Folder", ""
            )
            if not output_dir:
                QMessageBox.warning(self, "No Folder Selected", "Please select a folder to save the decoded files.")
                return

            self.label.setText(f"Processing: {file_path}")
            output_dir = os.path.join(output_dir, os.path.basename(file_path).replace(".bbl", "_output"))
            os.makedirs(output_dir, exist_ok=True)

            # Decode the .bbl file
            generated_dir = convert_bbl_to_csv(file_path, output_dir)  # Pass both arguments
            if generated_dir:
                self.label.setText(f"Files generated in: {generated_dir}")
                self.show_file_selection(generated_dir)
            else:
                self.label.setText("Conversion failed!")
                QMessageBox.critical(self, "Error", "Failed to convert the .bbl file. Please check the file and try again.")

    def open_decoded_folder(self):
        """Opens a file dialog to select an already decoded folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Decoded Folder", ""
        )
        if folder_path:
            self.label.setText(f"Opening folder: {folder_path}")
            self.show_file_selection(folder_path)

    def show_file_selection(self, output_dir):
        """Opens a new window displaying the list of CSV files."""
        self.file_selection_window = FileSelectionWindow(output_dir, self)
        self.file_selection_window.show()

    def show_table(self, csv_file):
        """Opens a new window displaying the CSV data as a table."""
        table_window = TableWindow(csv_file)
        self.open_windows.append(table_window)  # Keep a reference to prevent garbage collection
        table_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())