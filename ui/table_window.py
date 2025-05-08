import os
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

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