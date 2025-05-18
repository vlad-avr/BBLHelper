import os
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QMessageBox, QLabel
from src.data_processor import load_and_clean_csv

FRIENDLY_COLUMN_NAMES = {
    "axisP[0]": "PID proportional term for roll axis",
    "axisI[0]": "PID integral term for roll axis",
    "axisD[0]": "PID derivative term for roll axis",
    "axisF[0]": "PID feedforward term for roll axis",
    "axisP[1]": "PID proportional term for pitch axis",
    "axisI[1]": "PID integral term for pitch axis",
    "axisD[1]": "PID derivative term for pitch axis",
    "axisF[1]": "PID feedforward term for pitch axis",
    "axisP[2]": "PID proportional term for yaw axis",
    "axisI[2]": "PID integral term for yaw axis",
    "axisD[2]": "PID derivative term for yaw axis",
    "axisF[2]": "PID feedforward term for yaw axis",
    "gyroADC[0]": "Filtered gyro data (rotation rate) roll",
    "gyroADC[1]": "Filtered gyro data (rotation rate) pitch",
    "gyroADC[2]": "Filtered gyro data (rotation rate) yaw",
    "gyroUnfilt[0]": "Unfiltered gyro data (rotation rate) roll",
    "gyroUnfilt[1]": "Unfiltered gyro data (rotation rate) pitch",
    "gyroUnfilt[2]": "Unfiltered gyro data (rotation rate) yaw",
    "accSmooth[0]": "Smoothed accelerometer data roll",
    "accSmooth[1]": "Smoothed accelerometer data pitch",
    "accSmooth[2]": "Smoothed accelerometer data yaw",
    "setpoint[0]": "Target angular velocity for roll",
    "setpoint[1]": "Target angular velocity for pitch",
    "setpoint[2]": "Target angular velocity for yaw",
    "setpoint[3]": "Target throttle value",
    "motor[0]": "Motor 1 throttle effort",
    "motor[1]": "Motor 2 throttle effort",
    "motor[2]": "Motor 3 throttle effort",
    "motor[3]": "Motor 4 throttle effort",
    "eRPM[0]": "Electrical motor 1 RPM",
    "eRPM[1]": "Electrical motor 2 RPM",
    "eRPM[2]": "Electrical motor 3 RPM",
    "eRPM[3]": "Electrical motor 4 RPM",
    "rcCommand[0]": "Raw stick input for roll",
    "rcCommand[1]": "Raw stick input for pitch",
    "rcCommand[2]": "Raw stick input for yaw",
    "rcCommand[3]": "Raw stick input for throttle",
    "vbatLatest (V)": "Latest battery voltage (10 = 1 V)",
    "amperageLatest (A)": "Estimated current draw (100 = 1 A)",
    "loopIteration": "Number of completed PID loops",
    "rssi": "Received Signal Strength Indicator (RSSI)",
    "energyCumulative (mAh)": "Total energy drawn (mAh).",
    "flightModeFlags (flags)": "Active flight modes (ANGLE, HORIZON, ACRO, etc.)",
    "stateFlags (flags)": "Internal FC states (ARMED, CALIBRATING, etc.)",
    "failsafePhase (flags)": "Current failsafe phase (IDLE, RX_LOSS, etc.)",
    "rxSignalReceived": "Is RX signal received (0 = no, 1 = yes)",
    "rxFlightChannelsValid": "Are all RC channels valid (0 = no, 1 = yes)",
}

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
        df = load_and_clean_csv(self.csv_file)
        columns = [col for col in df.columns if col != "time (us)"]  # Exclude 'time (us)'

        # Build mapping: friendly name -> raw name
        self.friendly_to_raw = {}
        friendly_names = []
        for col in columns:
            friendly = FRIENDLY_COLUMN_NAMES.get(col, col.strip())
            friendly_names.append(friendly)
            self.friendly_to_raw[friendly] = col

        self.list_widget.addItems(friendly_names)

    def plot_graph(self):
        """Plots the selected columns and clears the selection."""
        selected_friendly = [item.text() for item in self.list_widget.selectedItems()]
        if not selected_friendly:
            QMessageBox.warning(self, "No Columns Selected", "Please select at least one column to plot.")
            return

        # Map friendly names back to raw column names
        selected_columns = [self.friendly_to_raw[name] for name in selected_friendly]

        if self.parent:
            self.parent.plot_graph(self.csv_file, selected_columns)

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