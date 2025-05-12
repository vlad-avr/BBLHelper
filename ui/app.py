import sys
import os
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl  # Import QUrl
import tempfile
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"  # Disable GPU acceleration
os.environ["QT_QUICK_BACKEND"] = "software"
from ui.table_window import TableWindow
from ui.file_selection import FileSelectionWindow
from ui.column_selection import ColumnSelectionWindow
import plotly.express as px
from src.converter import convert_bbl_to_csv  # Import the converter logic
from bokeh.plotting import figure, output_file, show  # Import Bokeh for plotting
from bokeh.palettes import Category10  # Import a color palette

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

        # Keep track of open windows
        self.open_file_selection_windows = []  # Track multiple file selection windows
        self.open_column_selection_windows = []  # Track multiple column selection windows
        self.open_table_windows = []  # Track multiple table windows

    def open_file_dialog(self):
        """Opens a file dialog to select a .bbl log file and process it."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Blackbox Log File", "", "Blackbox Logs (*.bbl);;All Files (*)"
        )
        if file_path:
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Output Folder", ""
            )
            if not output_dir:
                QMessageBox.warning(self, "No Folder Selected", "Please select a folder to save the decoded files.")
                return

            self.label.setText(f"Processing: {file_path}")
            output_dir = os.path.join(output_dir, os.path.basename(file_path).replace(".bbl", "_output"))
            os.makedirs(output_dir, exist_ok=True)

            generated_dir = convert_bbl_to_csv(file_path, output_dir)
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
        """Opens a new file selection window."""
        file_selection_window = FileSelectionWindow(output_dir, self)
        self.open_file_selection_windows.append(file_selection_window)
        file_selection_window.show()

        # Remove the window from the list when it is closed
        file_selection_window.destroyed.connect(
            lambda: self.open_file_selection_windows.remove(file_selection_window)
        )

    def show_table(self, csv_file):
        """Opens a new window displaying the CSV data as a table."""
        table_window = TableWindow(csv_file)
        self.open_table_windows.append(table_window)
        table_window.show()

        # Remove the window from the list when it is closed
        table_window.destroyed.connect(
            lambda: self.open_table_windows.remove(table_window)
        )

    def show_column_selection(self, csv_file):
        """Opens a new column selection window."""
        column_selection_window = ColumnSelectionWindow(csv_file, self)
        self.open_column_selection_windows.append(column_selection_window)
        column_selection_window.show()

        # Remove the window from the list when it is closed
        column_selection_window.destroyed.connect(
            lambda: self.open_column_selection_windows.remove(column_selection_window)
        )

    def plot_graph(self, csv_file, columns):
        """Plots the selected columns from the CSV file using Bokeh."""
        df = pd.read_csv(csv_file)
        if " time (us)" not in df.columns:
            print("CSV file missing 'time (us)' column.")
            return

        df = df.rename(columns={" time (us)": "time_us"})  # Fix column name

        # Create a Bokeh figure
        p = figure(title=f"Graph for {os.path.basename(csv_file)}",
                   x_axis_label="Time (us)", y_axis_label="Values",
                   tooltips=[("Time (us)", "$x"), ("Value", "$y")],
                   width=900, height=600)

        # Use a color palette to assign unique colors to each column
        colors = Category10[len(columns)] if len(columns) <= 10 else Category10[10] * (len(columns) // 10 + 1)

        # Add lines for each selected column with a unique color
        for i, column in enumerate(columns):
            p.line(df["time_us"], df[column], legend_label=column, line_width=2, color=colors[i])

        # Customize the legend
        p.legend.title = "Columns"
        p.legend.location = "top_left"

        # Save the plot to an HTML file and open it in the browser
        output_file("plot.html")
        show(p)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())