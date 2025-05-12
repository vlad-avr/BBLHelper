import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from src.data_processor import load_and_clean_csv  # Import the data processing logic

class TableWindow(QWidget):
    """Displays the processed CSV log data as a table."""
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
        """Loads processed CSV data into the table widget."""
        # Use the load_and_clean_csv function to process the DataFrame
        df = load_and_clean_csv(csv_file)

        # Set up the table with the processed DataFrame
        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(df.columns)

        for row in range(len(df)):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                self.table.setItem(row, col, item)