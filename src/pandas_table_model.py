from PyQt6.QtCore import QAbstractTableModel, Qt
from PyQt6.QtGui import QColor
from ui.column_selection import FRIENDLY_COLUMN_NAMES
from src.table_painter import paint_table_item

class PandasTableModel(QAbstractTableModel):
    def __init__(self, df, rssi_max=None):
        super().__init__()
        self._df = df
        self.rssi_max = rssi_max

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self._df.iloc[index.row(), index.column()]
        col_name = self._df.columns[index.column()].strip()
        if role == Qt.ItemDataRole.DisplayRole:
            return str(value)
        if role == Qt.ItemDataRole.BackgroundRole or role == Qt.ItemDataRole.ToolTipRole:
            from PyQt6.QtWidgets import QTableWidgetItem
            item = QTableWidgetItem(str(value))
            paint_table_item(item, col_name, value, rssi_max=self.rssi_max, row=index.row(), df=self._df)
            if role == Qt.ItemDataRole.BackgroundRole:
                return item.background().color()
            if role == Qt.ItemDataRole.ToolTipRole:
                return item.toolTip() or ""
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            col_name = self._df.columns[section].strip()
            if role == Qt.ItemDataRole.DisplayRole:
                return str(col_name)
            if role == Qt.ItemDataRole.ToolTipRole:
                from ui.column_selection import FRIENDLY_COLUMN_NAMES
                return FRIENDLY_COLUMN_NAMES.get(col_name, "")
        return super().headerData(section, orientation, role)