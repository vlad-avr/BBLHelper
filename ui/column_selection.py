import os
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QMessageBox, QLabel

class ColumnSelectionWindow(QWidget):
    """Allows the user to select columns for graphing and view raw CSV, with a section for preset plots."""
    def __init__(self, csv_file, parent=None):
        super().__init__()
        self.csv_file = csv_file
        self.parent = parent  # Optional parent reference for callbacks

        self.setWindowTitle(f"Select Columns for Graph - {os.path.basename(csv_file)}")
        self.setGeometry(200, 200, 800, 400)  # Adjusted width for two sections

        # Main layout (horizontal split)
        main_layout = QHBoxLayout()

        # Left section: Column selection
        left_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_columns()

        # Button to plot the graph
        self.plot_button = QPushButton("Plot Graph")
        self.plot_button.clicked.connect(self.plot_graph)

        # Button to view the raw CSV
        self.view_button = QPushButton("View Raw CSV")
        self.view_button.clicked.connect(self.view_csv)

        left_layout.addWidget(self.list_widget)
        left_layout.addWidget(self.plot_button)
        left_layout.addWidget(self.view_button)

        # Right section: Preset plots
        right_layout = QVBoxLayout()

        # Add buttons for preset plots
        self.pid_button = QPushButton("PID Loop Analysis")
        self.pid_button.clicked.connect(self.plot_pid_loop_analysis)
        right_layout.addWidget(self.pid_button)

        self.throttle_button = QPushButton("Throttle and Voltage Drop")
        self.throttle_button.clicked.connect(self.plot_throttle_voltage)
        right_layout.addWidget(self.throttle_button)

        self.motor_button = QPushButton("Motor Desync or Oscillations")
        self.motor_button.clicked.connect(self.plot_motor_desync)
        right_layout.addWidget(self.motor_button)

        # Add button for Stick Input vs. Actual Movement
        self.stick_input_button = QPushButton("Stick Input vs. Actual Movement")
        self.stick_input_button.clicked.connect(self.plot_stick_input_vs_movement)
        right_layout.addWidget(self.stick_input_button)

        # Add left and right sections to the main layout
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        self.setLayout(main_layout)

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

    def plot_pid_loop_analysis(self):
        """Plots the PID Loop Analysis preset."""
        if self.parent:
            self.parent.plot_pid_loop_analysis(self.csv_file)

    def plot_throttle_voltage(self):
        """Plots the Throttle and Voltage Drop preset."""
        if self.parent:
            self.parent.plot_throttle_voltage(self.csv_file)

    def plot_motor_desync(self):
        """Plots the Motor Desync or Oscillations preset."""
        if self.parent:
            self.parent.plot_motor_desync(self.csv_file)

    def plot_stick_input_vs_movement(self):
        """Plots the Stick Input vs. Actual Movement preset."""
        if self.parent:
            self.parent.plot_stick_input_vs_movement(self.csv_file)