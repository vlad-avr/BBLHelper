from PyQt6.QtCore import QThread, pyqtSignal
from src.assistant import ask_chatgpt

class ChatWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, messages, model):
        super().__init__()
        self.messages = messages
        self.model = model

    def run(self):
        try:
            ai_response = ask_chatgpt(self.messages, model=self.model)
            self.finished.emit(ai_response)
        except Exception as e:
            self.error.emit(f"AI: Error communicating with ChatGPT: {e}")