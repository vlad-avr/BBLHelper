import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QToolBar, QTextEdit, QLineEdit, QComboBox
)
from PyQt6.QtGui import QAction  # Import QAction from PyQt6.QtGui
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt  # Import QUrl and Qt
import tempfile
from itertools import cycle, islice  # Import cycle and islice to repeat and limit colors
import random  # Import random for generating random colors
import markdown  # Add this import at the top
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.table_window import TableWindow
from ui.file_selection import FileSelectionWindow
from ui.column_selection import ColumnSelectionWindow
import plotly.express as px
from src.converter import convert_bbl_to_csv  # Import the converter logic
from bokeh.plotting import figure, output_file, show  # Import Bokeh for plotting
from bokeh.palettes import Category10  # Import a color palette
from src.data_processor import load_and_clean_csv  # Import the data processing logic
from src.data_processor import (
    plot_pid_loop_analysis,
    plot_throttle_voltage,
    plot_motor_desync,
    plot_stick_input_vs_movement,  # Import the Stick Input vs. Actual Movement plot function
)
from src.assistant import ask_chatgpt

class MainWindow(QMainWindow):
    """Main Window with file selection, processing, and AI assistant chat."""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("UAV Blackbox Analyzer")
        self.setGeometry(100, 100, 800, 600)

        # Create a toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Add buttons to the toolbar
        decode_action = QAction("Decode Blackbox Log", self)
        decode_action.triggered.connect(self.open_file_dialog)
        self.toolbar.addAction(decode_action)

        open_folder_action = QAction("Open Decoded Folder", self)
        open_folder_action.triggered.connect(self.open_decoded_folder)
        self.toolbar.addAction(open_folder_action)

        # Central widget for the chat interface
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.chat_display)

        # --- Input row: chat input (left) + model selector (right) ---
        input_row = QHBoxLayout()

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.returnPressed.connect(self.handle_chat_input)
        input_row.addWidget(self.chat_input, stretch=1)

        self.model_selector = QComboBox()
        self.model_selector.addItems([
            "gpt-3.5-turbo",      # Default
            "gpt-4-1106-preview", # GPT-4.1
            "gpt-4-1106-vision-preview", # GPT-4.1 mini (example, adjust as needed)
            "gpt-4o",             # OpenAI o4-mini
            "gpt-4-0125-preview", # GPT-4.1 nano (example, adjust as needed)
        ])
        self.model_selector.setCurrentText("gpt-3.5-turbo")
        input_row.addWidget(self.model_selector)

        layout.addLayout(input_row)
        central_widget.setLayout(layout)

        # Keep track of open windows
        self.open_file_selection_windows = []  # Track multiple file selection windows
        self.open_column_selection_windows = []  # Track multiple column selection windows
        self.open_table_windows = []  # Track multiple table windows

    def closeEvent(self, event):
        """Closes all child windows when the main window is closed."""
        # Close all file selection windows
        for window in self.open_file_selection_windows:
            window.close()

        # Close all column selection windows
        for window in self.open_column_selection_windows:
            window.close()

        # Close all table windows
        for window in self.open_table_windows:
            window.close()

        # Accept the close event to proceed with closing the main window
        event.accept()

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

            self.chat_display.append(f"Processing: {file_path}")
            output_dir = os.path.join(output_dir, os.path.basename(file_path).replace(".bbl", "_output"))
            os.makedirs(output_dir, exist_ok=True)

            generated_dir = convert_bbl_to_csv(file_path, output_dir)
            if generated_dir:
                self.chat_display.append(f"Files generated in: {generated_dir}")
                self.show_file_selection(generated_dir)
            else:
                self.chat_display.append("Conversion failed!")
                QMessageBox.critical(self, "Error", "Failed to convert the .bbl file. Please check the file and try again.")

    def open_decoded_folder(self):
        """Opens a file dialog to select an already decoded folder."""
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Decoded Folder", ""
        )
        if folder_path:
            self.chat_display.append(f"Opening folder: {folder_path}")
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
        # Load and clean the CSV file
        df = load_and_clean_csv(csv_file)

        # Ensure "time_us" column exists after cleaning
        if "time_ms" not in df.columns:
            print("No valid 'time_ms' column found after cleaning.")
            return

        if len(columns) > 50:
            print("Too many columns selected for plotting. Please select fewer columns.")
            return

        # Create a Bokeh figure
        p = figure(title=f"Graph for {os.path.basename(csv_file)}",
                   x_axis_label="Time (ms)", y_axis_label="Values",
                   tooltips=[("Time (ms)", "$x"), ("Value", "$y")],
                   width=900, height=600)

        # Generate random colors for each column
        colors = ["#" + ''.join(random.choices("0123456789ABCDEF", k=6)) for _ in columns]

        # Add lines for each selected column with a unique color
        for i, column in enumerate(columns):
            if column in df.columns:  # Ensure the column exists after cleaning
                p.line(df["time_ms"], df[column], legend_label=column, line_width=2, color=colors[i])

        # Customize the legend
        p.legend.title = "Columns"
        p.legend.location = "top_left"

        # Save the plot to an HTML file and open it in the browser
        output_file("plot.html")
        show(p)

    def plot_pid_loop_analysis(self, csv_file):
        """Calls the PID Loop Analysis plot function."""
        plot_pid_loop_analysis(csv_file)

    def plot_throttle_voltage(self, csv_file):
        """Calls the Throttle and Voltage Drop plot function."""
        plot_throttle_voltage(csv_file)

    def plot_motor_desync(self, csv_file):
        """Calls the Motor Desync or Oscillations plot function."""
        plot_motor_desync(csv_file)

    def plot_stick_input_vs_movement(self, csv_file):
        """Calls the Stick Input vs. Actual Movement plot function."""
        plot_stick_input_vs_movement(csv_file)

    def handle_chat_input(self):
        """Handles user input in the chat interface."""
        user_message = self.chat_input.text().strip()
        if user_message:
            user_html = (
                '<div style="color:#1565c0;">'
                '<b>You:</b> {}</div>'
            ).format(user_message)
            self.chat_display.insertHtml(user_html)
            self.chat_display.insertPlainText("\n")
            self.chat_input.clear()

            # Get selected model
            selected_model = self.model_selector.currentText()

            messages = [
                {"role": "system", "content": "You are a helpful assistant for UAV data analysis."},
                {"role": "user", "content": user_message}
            ]

            try:
                ai_response = ask_chatgpt(messages, model=selected_model)
            except Exception as e:
                ai_response = f"AI: Error communicating with ChatGPT: {e}"

            ai_html_content = markdown.markdown(ai_response, extensions=['tables'])
            ai_html = (
                '<div style="color:#388e3c;">'
                '<b>AI:</b> {}</div>'
            ).format(ai_html_content)
            self.chat_display.insertHtml(ai_html)
            self.chat_display.insertPlainText("\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())