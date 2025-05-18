from PyQt6.QtGui import QColor

def paint_table_item(item, col_name, value, rssi_max=None):
    """
    Paints a QTableWidgetItem based on column name and value.
    - rxSignalReceived, rxFlightChannelsValid: green if 1, red if 0
    - failsafePhase (flags), stateFlags (flags), flightModeFlags (flags): different color per unique value
    - rssi: blue gradient from max (deep blue) to 0 (white)
    """
    # 1. Binary columns: green for 1, red for 0
    if col_name in ("rxSignalReceived", "rxFlightChannelsValid"):
        try:
            v = int(value)
            if v == 1:
                item.setBackground(QColor(180, 255, 180))  # green
            elif v == 0:
                item.setBackground(QColor(255, 180, 180))  # red
        except Exception:
            pass

    # 2. Flags columns: assign a color per unique value (hash-based)
    elif col_name in ("failsafePhase (flags)", "stateFlags (flags)", "flightModeFlags (flags)"):
        color_palette = [
            QColor(200, 200, 255), QColor(255, 220, 180), QColor(200, 255, 200),
            QColor(255, 200, 255), QColor(255, 255, 180), QColor(220, 255, 255),
            QColor(255, 180, 220), QColor(220, 220, 220)
        ]
        idx = abs(hash(str(value))) % len(color_palette)
        item.setBackground(color_palette[idx])

    # 3. RSSI: blue gradient from max (deep blue) to 0 (white)
    elif col_name == " rssi" and rssi_max is not None:
        try:
            v = float(value)
            # Clamp ratio between 0 and 1
            ratio = max(0.0, min(1.0, v / rssi_max)) if rssi_max > 0 else 0.0
            # Gradient from white (low) to blue (high)
            r = int(255 * (1 - ratio))
            g = int(255 * (1 - ratio))
            b = 255
            item.setBackground(QColor(r, g, b))
        except Exception:
            pass