import os
import pandas as pd
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableView, QTableWidgetItem, QLabel, QProgressDialog, QTableWidget
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction
from src.data_processor import load_and_clean_csv
from ui.column_selection import FRIENDLY_COLUMN_NAMES  # Add this import at the top
from src.table_painter import paint_table_item
from src.pandas_table_model import PandasTableModel

class TableWindow(QWidget):
    """Displays the processed CSV log data and analysis results."""
    context_extracted = pyqtSignal(str)  # Signal to send context as string

    def __init__(self, csv_file, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"Blackbox Log Data - {os.path.basename(csv_file)}")
        self.setGeometry(150, 150, 1200, 600)  # Adjusted width for two sections

        # Main layout (horizontal split)
        main_layout = QHBoxLayout()

        # Left section: Raw CSV data
        left_layout = QVBoxLayout()
        self.raw_table = QTableView()
        self.raw_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.raw_table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.raw_table.horizontalHeader().setMouseTracking(True)  # <-- Add this line
        self.load_table_in_thread(csv_file)
        left_layout.addWidget(QLabel("Raw CSV Data"))
        left_layout.addWidget(self.raw_table)

        # Right section: Analysis results
        right_layout = QVBoxLayout()
        self.analysis_table = QTableWidget()
        self.analysis_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.analysis_table.customContextMenuRequested.connect(self.show_metrics_context_menu)
        self.perform_analysis(csv_file)
        right_layout.addWidget(QLabel("Analysis Results"))
        right_layout.addWidget(self.analysis_table)

        # Add left and right sections to the main layout
        main_layout.addLayout(left_layout, 4)   # 4 parts (80%)
        main_layout.addLayout(right_layout, 1)  # 1 part (20%)

        self.setLayout(main_layout)

    # def load_csv(self, csv_file):
    #     """Loads processed CSV data into the table widget."""
    #     # Use the load_and_clean_csv function to process the DataFrame
    #     df = load_and_clean_csv(csv_file, load_non_numeric=True)

    #     # Set up the table with the processed DataFrame
    #     self.raw_table.setRowCount(len(df))
    #     self.raw_table.setColumnCount(len(df.columns))
    #     self.raw_table.setHorizontalHeaderLabels(df.columns)

    #     rssi_max = None
    #     print("Columns in DataFrame:", df.columns)
    #     if " rssi" in df.columns:
    #         try:
    #             rssi_max = df[" rssi"].max()
    #         except Exception:
    #             rssi_max = None

    #     for row in range(len(df)):
    #         for col in range(len(df.columns)):
    #             col_name = df.columns[col].strip()
    #             item = QTableWidgetItem(str(df.iloc[row, col]))
    #             paint_table_item(item, col_name, df.iloc[row, col], rssi_max=rssi_max)
    #             self.raw_table.setItem(row, col, item)

    def load_table_in_thread(self, csv_file):
        from workers.table_loader_worker import TableLoadWorker
        self.table_worker = TableLoadWorker(csv_file)
        self.table_worker.finished.connect(self.on_table_loaded)
        self.table_worker.error.connect(self.on_table_load_error)
        # self.raw_table.setRowCount(0)
        # self.raw_table.setColumnCount(0)
        # self.raw_table.clear()
        # self.raw_table.setHorizontalHeaderLabels([])
        # self.raw_table.setRowCount(1)
        # self.raw_table.setColumnCount(1)
        # self.raw_table.setItem(0, 0, QTableWidgetItem("Loading table, please wait..."))
        self.progress_dialog = QProgressDialog("Loading table...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Please wait")
        self.progress_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.progress_dialog.show()
        self.table_worker.start()

    def on_table_loaded(self, df):
        df.columns = [col.strip() for col in df.columns]
        rssi_max = df["rssi"].max() if "rssi" in df.columns else None
        self.model = PandasTableModel(df, rssi_max=rssi_max)
        self.raw_table.setModel(self.model)
        # for col in range(len(df.columns)):
        #     col_name = df.columns[col]
        #     tooltip = FRIENDLY_COLUMN_NAMES.get(col_name)
        #     if tooltip:
        #         self.raw_table.horizontalHeaderItem(col).setToolTip(tooltip)
        # rssi_max = None
        # if " rssi" in df.columns:
        #     try:
        #         rssi_max = df[" rssi"].max()
        #     except Exception:
        #         rssi_max = None
        # for row in range(len(df)):
        #     for col in range(len(df.columns)):
        #         item = QTableWidgetItem(str(df.iloc[row, col]))
        #         paint_table_item(item, df.columns[col].strip(), df.iloc[row, col], rssi_max=rssi_max, row=row, df=df)
                # self.raw_table.setItem(row, col, item)
        self.progress_dialog.close()

    def on_table_load_error(self, msg):
        self.raw_table.clear()
        self.raw_table.setRowCount(1)
        self.raw_table.setColumnCount(1)
        self.raw_table.setItem(0, 0, QTableWidgetItem(f"Error loading table: {msg}"))

    def perform_analysis(self, csv_file):
        """Performs data analysis and displays the results in the analysis table."""
        df = load_and_clean_csv(csv_file, load_non_numeric=True)

        # Prepare analysis results
        analysis_results = []

        # 1. Tracking Error (Setpoint vs Gyro)
        if "setpoint[0]" in df.columns and "gyroADC[0]" in df.columns:
            mae_roll = (df["setpoint[0]"] - df["gyroADC[0]"]).abs().mean()
            rmse_roll = ((df["setpoint[0]"] - df["gyroADC[0]"])**2).mean()**0.5
            analysis_results.append(["MAE (Roll)", f"{mae_roll:.2f}"])
            analysis_results.append(["RMSE (Roll)", f"{rmse_roll:.2f}"])

        # 2. PID Balance Metrics
        if all(col in df.columns for col in ["axisP[0]", "axisI[0]", "axisD[0]"]):
            total_pid = df["axisP[0]"].abs().sum()+df["axisI[0]"].abs().sum()+df["axisD[0]"].abs().sum()
            p_contrib = df["axisP[0]"].abs().sum() / total_pid * 100
            i_contrib = df["axisI[0]"].abs().sum() / total_pid * 100
            d_contrib = df["axisD[0]"].abs().sum() / total_pid * 100
            analysis_results.append(["P Contribution (%)", f"{p_contrib:.2f}%"])
            analysis_results.append(["I Contribution (%)", f"{i_contrib:.2f}%"])
            analysis_results.append(["D Contribution (%)", f"{d_contrib:.2f}%"])

        # 3. Overshoot and Bounceback
        if "gyroADC[0]" in df.columns and "setpoint[0]" in df.columns:
            overshoot = (df["gyroADC[0]"] - df["setpoint[0]"]).max()
            analysis_results.append(["Max Overshoot (Roll)", f"{overshoot:.2f}"])

        # 4. Noise & Jitter (Filtering)
        if "gyroADC[0]" in df.columns:
            noise_roll = df["gyroADC[0]"].diff().std()
            analysis_results.append(["Gyro Noise Std (Roll)", f"{noise_roll:.2f}"])

        # 5. Battery Voltage Sag
        if "vbatLatest (V)" in df.columns:
            min_voltage = df["vbatLatest (V)"].min()
            voltage_drop = df["vbatLatest (V)"].max() - min_voltage
            analysis_results.append(["Min Voltage", f"{min_voltage:.2f}V"])
            analysis_results.append(["Voltage Drop", f"{voltage_drop:.2f}V"])

        if "throttle" in df.columns and "vbatLatest (V)" in df.columns:
            correlation = df["throttle"].corr(df["vbatLatest (V)"])
            analysis_results.append(["Throttle-Voltage Correlation", f"{correlation:.2f}"])

        # 6. Command Latency
        if "setpoint[0]" in df.columns and "gyroADC[0]" in df.columns:
            df["roll_error"] = df["setpoint[0]"] - df["gyroADC[0]"]
            # Placeholder for cross-correlation lag calculation
            analysis_results.append(["Command Latency (Lag)", "Not Implemented"])

        # 7. Motor Output Symmetry
        motor_columns = [col for col in df.columns if col.startswith("motor[")]
        if motor_columns:
            motor_imbalance = df[motor_columns].std(axis=1).mean()
            analysis_results.append(["Motor Imbalance (Std)", f"{motor_imbalance:.2f}"])

        # 8. Runtime Statistics
        if "time_ms" in df.columns:
            flight_time = (df["time_ms"].iloc[-1] - df["time_ms"].iloc[0])/1000  # Convert to seconds
            analysis_results.append(["Flight Time (s)", f"{flight_time:.2f}s"])

        if "throttle" in df.columns:
            avg_throttle = df["throttle"].mean()
            analysis_results.append(["Avg Throttle", f"{avg_throttle:.2f}"])

        if "amperageLatest (A)" in df.columns:
            max_current = df["amperageLatest (A)"].max()
            analysis_results.append(["Max Current", f"{max_current:.2f}A"])

        # Populate the analysis table
        self.analysis_table.setRowCount(len(analysis_results))
        self.analysis_table.setColumnCount(2)
        self.analysis_table.setHorizontalHeaderLabels(["Metric", "Value"])

        for row, (metric, value) in enumerate(analysis_results):
            self.analysis_table.setItem(row, 0, QTableWidgetItem(metric))
            self.analysis_table.setItem(row, 1, QTableWidgetItem(value))

    def add_selection_to_chat_context(self):
        """Extracts selected cells and emits them as context."""
        selected = self.raw_table.selectionModel().selectedIndexes()
        if not selected:
            return
        rows = sorted(set(idx.row() for idx in selected))
        cols = sorted(set(idx.column() for idx in selected))
        headers = [self.model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole) for col in cols]
        extracted = ["\t".join(headers)]
        for row in rows:
            row_data = []
            for col in cols:
                idx = self.model.index(row, col)
                row_data.append(str(self.model.data(idx, Qt.ItemDataRole.DisplayRole)))
            extracted.append("\t".join(row_data))
        context_str = "\n".join(extracted)
        self.context_extracted.emit(context_str)

    def show_table_context_menu(self, pos):
        menu = QMenu(self)
        add_context_action = QAction("Add context to chat", self)
        add_context_action.triggered.connect(self.add_selection_to_chat_context)
        menu.addAction(add_context_action)
        menu.exec(self.raw_table.mapToGlobal(pos))

    def show_metrics_context_menu(self, pos):
        menu = QMenu(self)
        add_context_action = QAction("Add context to chat", self)
        add_context_action.triggered.connect(self.add_metrics_selection_to_chat_context)
        menu.addAction(add_context_action)
        menu.exec(self.analysis_table.mapToGlobal(pos))

    def add_metrics_selection_to_chat_context(self):
        selected_ranges = self.analysis_table.selectedRanges()
        if not selected_ranges:
            return

        sel = selected_ranges[0]
        rows = range(sel.topRow(), sel.bottomRow() + 1)
        cols = range(sel.leftColumn(), sel.rightColumn() + 1)

        # Extract header
        headers = [self.analysis_table.horizontalHeaderItem(col).text() for col in cols]
        extracted = ["\t".join(headers)]

        # Extract data
        for row in rows:
            row_data = []
            for col in cols:
                item = self.analysis_table.item(row, col)
                row_data.append(item.text() if item else "")
            extracted.append("\t".join(row_data))

        context_str = "\n".join(extracted)
        self.context_extracted.emit(context_str)