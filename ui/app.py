import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem
)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.converter import convert_bbl_to_csv  # Import the converter logic

class TableWindow(QWidget):
    """Displays the converted .bbl log data as a table."""
    def __init__(self, csv_file):
        super().__init__()

        self.setWindowTitle("Blackbox Log Data")
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

class MainWindow(QMainWindow):
    """Main Window with file selection and processing."""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UAV Blackbox Analyzer")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.label = QLabel("No file selected")
        self.label.setStyleSheet("font-size: 14px;")

        self.open_button = QPushButton("Open Blackbox Log (.bbl)")
        self.open_button.clicked.connect(self.open_file_dialog)

        layout.addWidget(self.label)
        layout.addWidget(self.open_button)
        central_widget.setLayout(layout)

    def open_file_dialog(self):
        """Opens a file dialog to select a .bbl log file and process it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Blackbox Log File", "", "Blackbox Logs (*.bbl);;All Files (*)"
        )
        if file_path:
            self.label.setText(f"Processing: {file_path}")
            csv_file = convert_bbl_to_csv(file_path)  # Use external converter function

            if csv_file:
                self.label.setText(f"Converted: {csv_file}")
                self.show_table(csv_file)

    def show_table(self, csv_file):
        """Opens a new window displaying the CSV data as a table."""
        self.table_window = TableWindow(csv_file)
        self.table_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())