import os
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QPushButton, QMessageBox

class ColumnSelectionWindow(QWidget):
    """Allows the user to select columns for graphing and view raw CSV."""
    def __init__(self, csv_file, parent=None):
        super().__init__()
        self.csv_file = csv_file
        self.parent = parent  # Optional parent reference for callbacks

        self.setWindowTitle(f"Select Columns for Graph - {os.path.basename(csv_file)}")
        self.setGeometry(200, 200, 400, 400)

        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_columns()

        # Button to plot the graph
        self.plot_button = QPushButton("Plot Graph")
        self.plot_button.clicked.connect(self.plot_graph)

        # Button to view the raw CSV
        self.view_button = QPushButton("View Raw CSV")
        self.view_button.clicked.connect(self.view_csv)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.plot_button)
        layout.addWidget(self.view_button)
        self.setLayout(layout)

    def load_columns(self):
        """Loads column names from the CSV file, excluding 'time (us)'."""
        df = pd.read_csv(self.csv_file)
        columns = [col for col in df.columns if col != " time (us)"]  # Exclude 'time (us)'
        self.list_widget.addItems(columns)

    def plot_graph(self):
        """Plots the selected columns and clears the selection."""
        selected_columns = [item.text() for item in self.list_widget.selectedItems()]
        if not selected_columns:
            QMessageBox.warning(self, "No Columns Selected", "Please select at least one column to plot.")
            return

        if self.parent:
            self.parent.plot_graph(self.csv_file, selected_columns)

        # Clear the selection after plotting
        self.list_widget.clearSelection()

    def view_csv(self):
        """Opens the raw CSV file in a table view."""
        if self.parent:
            self.parent.show_table(self.csv_file)