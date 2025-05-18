import sys
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QMessageBox, QToolBar, QTextEdit, QLineEdit, QComboBox, QMenu, QListWidget, QListWidgetItem, QDialog, QFormLayout
)
from PyQt6.QtGui import QAction  # QAction ONLY from QtGui
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal  # Import QUrl, Qt, QThread, and pyqtSignal
import tempfile
from itertools import cycle, islice  # Import cycle and islice to repeat and limit colors
import random  # Import random for generating random colors
import markdown  # Add this import at the top
import base64  # Import base64 for encoding images
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.table_window import TableWindow
from ui.file_selection import FileSelectionWindow
from ui.column_selection import ColumnSelectionWindow
from workers.chat_worker import ChatWorker  # Import the ChatWorker class
from src.context_processor import tsv_to_markdown  # Import the context processor
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
from ui.column_selection import FRIENDLY_COLUMN_NAMES

class DecodeWorker(QThread):
    finished = pyqtSignal(str)  # emits output_dir on success
    error = pyqtSignal(str)     # emits error message

    def __init__(self, file_path, output_dir):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir

    def run(self):
        try:
            from src.converter import convert_bbl_to_csv
            generated_dir = convert_bbl_to_csv(self.file_path, self.output_dir)
            if generated_dir:
                self.finished.emit(generated_dir)
            else:
                self.error.emit("Failed to convert the .bbl file. Please check the file and try again.")
        except Exception as e:
            self.error.emit(str(e))

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

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        self.toolbar.addAction(settings_action)

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
            "gpt-4.1-mini-2025-04-14", # GPT-4.1 mini (example, adjust as needed)
            "gpt-4o",             # OpenAI o4-mini
            "gpt-4.1-nano-2025-04-14", # GPT-4.1 nano (example, adjust as needed)
        ])
        self.model_selector.setCurrentText("gpt-3.5-turbo")
        input_row.addWidget(self.model_selector)

        self.context_selector = QComboBox()
        self.context_selector.setVisible(False)  # Hidden by default
        self.context_selector.addItem("No context")  # Default option
        self.context_selector.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.context_selector.customContextMenuRequested.connect(self.show_context_selector_menu)
        input_row.addWidget(self.context_selector)

        self.clear_contexts_button = QPushButton("Clear Contexts")
        self.clear_contexts_button.setVisible(False)
        self.clear_contexts_button.clicked.connect(self.clear_chat_contexts)
        input_row.addWidget(self.clear_contexts_button)

        self.attach_image_button = QPushButton("Attach Image")
        self.attach_image_button.clicked.connect(self.attach_image_to_chat)
        input_row.addWidget(self.attach_image_button)

        layout.addLayout(input_row)

        self.image_list = QListWidget()
        self.image_list.setMaximumHeight(60)
        layout.addWidget(self.image_list)
        self.image_list.setVisible(False)
        self.image_list.itemDoubleClicked.connect(self.remove_selected_image)

        central_widget.setLayout(layout)

        # Keep track of open windows
        self.open_file_selection_windows = []  # Track multiple file selection windows
        self.open_column_selection_windows = []  # Track multiple column selection windows
        self.open_table_windows = []  # Track multiple table windows

        self.chat_contexts = []  # List to store context strings
        self.attached_images = []  # Store attached images for the next chat message

        self.all_models = [
            "gpt-3.5-turbo",
            "gpt-4-1106-preview",
            "gpt-4.1-mini-2025-04-14",
            "gpt-4o",
            "gpt-4.1-nano-2025-04-14",
        ]
        self.vision_models = [
            "gpt-4o",
            "gpt-4-1106-preview",  # If you have access to vision in this model
            # Add other vision-capable models here
        ]

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
        """Opens a file dialog to select a .bbl log file and process it in a thread."""
        bbl_path, decoded_path = self.load_paths()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Blackbox Log File", bbl_path, "Blackbox Logs (*.bbl);;All Files (*)"
        )
        if file_path:
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Output Folder", decoded_path
            )
            if not output_dir:
                QMessageBox.warning(self, "No Folder Selected", "Please select a folder to save the decoded files.")
                return
            output_dir = os.path.join(output_dir, os.path.basename(file_path).replace(".bbl", "_output"))
            os.makedirs(output_dir, exist_ok=True)

            # Show FileSelectionWindow with "decoding" message
            file_selection_window = FileSelectionWindow(output_dir, self)
            file_selection_window.setWindowTitle("Decoding in Progress")
            file_selection_window.list_widget.clear()
            file_selection_window.list_widget.addItem(f"{os.path.basename(file_path)} is being decoded. This may take some time...")
            file_selection_window.show()
            self.open_file_selection_windows.append(file_selection_window)
            file_selection_window.destroyed.connect(
                lambda: self.open_file_selection_windows.remove(file_selection_window)
            )

            # Start decoding in a thread
            self.decode_worker = DecodeWorker(file_path, output_dir)
            self.decode_worker.finished.connect(lambda gen_dir: self.on_decode_finished(gen_dir, file_selection_window))
            self.decode_worker.error.connect(lambda msg: self.on_decode_error(msg, file_selection_window))
            self.decode_worker.start()

    def open_decoded_folder(self):
        """Opens a file dialog to select an already decoded folder."""
        _, decoded_path = self.load_paths()
        folder_path = QFileDialog.getExistingDirectory(
            self, "Select Decoded Folder", decoded_path
        )
        if folder_path:
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
        table_window.context_extracted.connect(self.add_chat_context)  # Connect the signal
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
            QMessageBox.criitical(self,"Error", "No valid 'time_ms' column found.")
            return

        if len(columns) > 50:
            QMessageBox.warning(self, "Too many columns selected for plotting.",  "Please select fewer columns.")
            return

        # Create a Bokeh figure
        p = figure(
            title=f"Graph for {os.path.basename(csv_file)}",
            x_axis_label="Time (ms)",
            y_axis_label="Values",
            tooltips=[
                ("Time (ms)", "$x"),
                ("Value", "$y"),
                ("Column", "@legend_label")  # This works if you use ColumnDataSource with a 'legend_label' field
            ],
            width=900, height=600
        )

        # Generate random colors for each column
        colors = ["#" + ''.join(random.choices("0123456789ABCDEF", k=6)) for _ in columns]

        # Friendly names mapping
        friendly_names = {col: FRIENDLY_COLUMN_NAMES.get(col, col) for col in columns}

        # Add lines for each selected column with a unique color
        for i, column in enumerate(columns):
            if column in df.columns:
                p.line(
                    df["time_ms"], df[column],
                    legend_label=friendly_names[column],  # Use friendly name
                    line_width=2,
                    color=colors[i]
                )

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

            selected_model = self.model_selector.currentText()

            # --- Context handling ---
            context_idx = self.context_selector.currentIndex() - 1  # -1 because "No context" is at 0
            messages = [{"role": "system", "content": "You are a helpful assistant for UAV data analysis."}]
            if context_idx >= 0:
                context_str = self.chat_contexts[context_idx]
                context_md = tsv_to_markdown(context_str)
                messages.append({"role": "user", "content": f"Here is some context data:\n{context_md}"})

            user_content = user_message

            # Only include images that are still in the image_list
            current_images = []
            current_filenames = [self.image_list.item(i).text() for i in range(self.image_list.count())]
            for fname, img in self.attached_images:
                if fname in current_filenames:
                    current_images.append(img)

            if current_images:
                content_blocks = [{"type": "text", "text": user_content}]
                content_blocks.extend(current_images)
                messages.append({
                    "role": "user",
                    "content": content_blocks
                })
                self.attached_images = [
                    (fname, img) for fname, img in self.attached_images if fname not in current_filenames
                ]
                self.update_image_list()
            else:
                messages.append({"role": "user", "content": user_content})

            # Disable input while waiting
            self.chat_input.setDisabled(True)
            self.attach_image_button.setDisabled(True)
            self.model_selector.setDisabled(True)
            self.context_selector.setDisabled(True)

            # Start worker thread
            self.chat_worker = ChatWorker(messages, selected_model)
            self.chat_worker.finished.connect(self.on_ai_response)
            self.chat_worker.error.connect(self.on_ai_response)
            self.chat_worker.start()

    def on_ai_response(self, ai_response):
        """Handles the AI response and updates the chat display."""
        ai_html_content = markdown.markdown(ai_response, extensions=['tables'])
        ai_html = (
            '<div style="color:#388e3c;">'
            '<b>AI:</b> {}</div>'
        ).format(ai_html_content)
        self.chat_display.insertHtml(ai_html)
        self.chat_display.insertPlainText("\n")

        # Re-enable input
        self.chat_input.setDisabled(False)
        self.attach_image_button.setDisabled(False)
        self.model_selector.setDisabled(False)
        self.context_selector.setDisabled(False)
        self.chat_input.setFocus()

    def attach_image_to_chat(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            with open(file_path, "rb") as img_file:
                b64_img = base64.b64encode(img_file.read()).decode("utf-8")
            image_data = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_img}"
                }
            }
            self.attached_images.append((os.path.basename(file_path), image_data))
            self.update_image_list()
            QMessageBox.information(self, "Image Attached", "Image will be sent with your next message.")
        # Always update model selector, even if no file selected (in case of removal)
        self.update_model_selector()

    def remove_selected_image(self, item):
        """Removes the selected image from the list and updates attached_images."""
        row = self.image_list.row(item)
        if row >= 0:
            del self.attached_images[row]
            self.image_list.takeItem(row)
            self.image_list.setVisible(bool(self.attached_images))
            self.update_model_selector()

    def update_image_list(self):
        self.image_list.clear()
        for fname, _ in self.attached_images:
            self.image_list.addItem(fname)
        self.image_list.setVisible(bool(self.attached_images))
        self.update_model_selector()  # <-- Add this line

    def show_table_context_menu(self, pos):
        menu = QMenu(self)
        add_context_action = QAction("Add context to chat", self)
        add_context_action.triggered.connect(self.add_selection_to_chat_context)
        menu.addAction(add_context_action)
        menu.exec(self.raw_table.mapToGlobal(pos))

    def add_chat_context(self, context_str):
        """Add extracted context to the list and update the dropdown."""
        self.chat_contexts.append(context_str)
        # Show the context selector and clear button if hidden
        self.context_selector.setVisible(True)
        self.clear_contexts_button.setVisible(True)
        # Add a preview (first line or first 40 chars) as the dropdown entry
        preview = context_str.splitlines()[0] if context_str else "Context"
        if len(preview) > 40:
            preview = preview[:37] + "..."
        self.context_selector.addItem(f"Selection {len(self.chat_contexts)}: {preview}")
        QMessageBox.information(self, "Context Added", "Selection added as chat context.")
        self.update_model_selector()  # <-- Add this line

    def clear_chat_contexts(self):
        """Clears all chat contexts and updates the UI."""
        self.chat_contexts.clear()
        self.context_selector.clear()
        self.context_selector.addItem("No context")
        if self.context_selector.count() <= 1:
            self.context_selector.setVisible(False)
            self.clear_contexts_button.setVisible(False)
        QMessageBox.information(self, "Contexts Cleared", "All chat contexts have been cleared.")
        self.update_model_selector()  # <-- Add this line

    def show_context_selector_menu(self, pos):
        if self.context_selector.count() <= 1:
            return
        menu = QMenu(self)
        remove_action = QAction("Remove selected context", self)
        remove_action.triggered.connect(self.remove_selected_context)
        menu.addAction(remove_action)
        menu.exec(self.context_selector.mapToGlobal(pos))

    def remove_selected_context(self):
        idx = self.context_selector.currentIndex()
        if idx > 0:
            del self.chat_contexts[idx - 1]
            self.context_selector.removeItem(idx)
            if self.context_selector.count() <= 1:
                self.context_selector.setVisible(False)
                self.clear_contexts_button.setVisible(False)
        self.update_model_selector()  # <-- Add this line

    def remove_selected_image(self, item):
        """Removes the selected image from the list."""
        row = self.image_list.row(item)
        self.image_list.takeItem(row)

    def open_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QFormLayout(dialog)

        bbl_edit = QLineEdit()
        decoded_edit = QLineEdit()

        # Load current paths
        bbl_path, decoded_path = self.load_paths()
        bbl_edit.setText(bbl_path)
        decoded_edit.setText(decoded_path)

        browse_bbl = QPushButton("Browse")
        browse_decoded = QPushButton("Browse")

        def browse_bbl_folder():
            folder = QFileDialog.getExistingDirectory(self, "Select Default .bbl Folder", bbl_edit.text())
            if folder:
                bbl_edit.setText(folder)
        def browse_decoded_folder():
            folder = QFileDialog.getExistingDirectory(self, "Select Default Decoded Folder", decoded_edit.text())
            if folder:
                decoded_edit.setText(folder)

        browse_bbl.clicked.connect(browse_bbl_folder)
        browse_decoded.clicked.connect(browse_decoded_folder)

        layout.addRow("Default .bbl folder:", bbl_edit)
        layout.addRow("", browse_bbl)
        layout.addRow("Default decoded folder:", decoded_edit)
        layout.addRow("", browse_decoded)

        save_btn = QPushButton("Save")
        layout.addRow(save_btn)
        def save_and_close():
            self.save_paths(bbl_edit.text(), decoded_edit.text())
            dialog.accept()
        save_btn.clicked.connect(save_and_close)

        dialog.exec()

    def save_paths(self, bbl_path, decoded_path):
        with open("path.txt", "w", encoding="utf-8") as f:
            f.write(f"{bbl_path}\n{decoded_path}\n")

    def load_paths(self):
        try:
            with open("path.txt", "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                bbl_path = lines[0] if len(lines) > 0 else "C:\\"
                decoded_path = lines[1] if len(lines) > 1 else "C:\\"
                return bbl_path, decoded_path
        except FileNotFoundError:
            return "C:\\", "C:\\"

    def update_model_selector(self):
        # If images or context are attached, only show vision models
        has_images = self.image_list.count() > 0
        has_context = (
            self.context_selector.isVisible() and
            self.context_selector.currentIndex() > 0
        )
        if has_images:
            allowed_models = self.vision_models
        else:
            allowed_models = self.all_models

        current = self.model_selector.currentText()
        self.model_selector.blockSignals(True)
        self.model_selector.clear()
        self.model_selector.addItems(allowed_models)
        # Restore selection if possible
        if current in allowed_models:
            self.model_selector.setCurrentText(current)
        self.model_selector.blockSignals(False)

    def on_decode_finished(self, generated_dir, file_selection_window):
        # Update the file selection window with real CSV files
        file_selection_window.setWindowTitle("Select a CSV File")
        file_selection_window.list_widget.clear()
        file_selection_window.load_csv_files()
        QMessageBox.information(self, "Decoding Complete", "Decoding finished successfully.")

    def on_decode_error(self, msg, file_selection_window):
        QMessageBox.critical(self, "Error", msg)
        file_selection_window.close()
