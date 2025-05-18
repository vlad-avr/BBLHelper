from PyQt6.QtCore import QThread, pyqtSignal
import pandas as pd
import src.data_processor as data_processor

class TableLoadWorker(QThread):
    finished = pyqtSignal(object)  # emits DataFrame on success
    error = pyqtSignal(str)        # emits error message

    def __init__(self, csv_file):
        super().__init__()
        self.csv_file = csv_file

    def run(self):
        try:
            df = data_processor.load_and_clean_csv(self.csv_file, True)
            self.finished.emit(df)
        except Exception as e:
            self.error.emit(str(e))