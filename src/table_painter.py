from PyQt6.QtGui import QColor

def paint_table_item(item, col_name, value, rssi_max=None, row=None, df=None):
    """
    Paints a QTableWidgetItem based on column name and value.
    Adds a tooltip if the cell is painted yellow or red, explaining the reason.
    """
    # Helper to set color and tooltip
    def set_color_and_tooltip(color, tooltip=None):
        item.setBackground(color)
        if tooltip:
            item.setToolTip(tooltip)

    # 1. Binary columns
    if col_name in ("rxSignalReceived", "rxFlightChannelsValid"):
        try:
            v = int(value)
            if v == 1:
                item.setBackground(QColor(180, 255, 180))  # green
            elif v == 0:
                set_color_and_tooltip(QColor(255, 180, 180), "Signal not received (0 = no, 1 = yes)")
        except Exception:
            pass

    # 2. Flags columns
    elif col_name in ("failsafePhase (flags)", "stateFlags (flags)", "flightModeFlags (flags)"):
        color_palette = [
            QColor(200, 200, 255), QColor(255, 220, 180), QColor(200, 255, 200),
            QColor(255, 200, 255), QColor(255, 255, 180), QColor(220, 255, 255),
            QColor(255, 180, 220), QColor(220, 220, 220)
        ]
        idx = abs(hash(str(value))) % len(color_palette)
        item.setBackground(color_palette[idx])

    # 3. RSSI
    elif col_name == "rssi" and rssi_max is not None:
        try:
            v = float(value)
            if rssi_max > 0:
                ratio = max(0.0, min(1.0, v / rssi_max))
                if ratio > 0.6:
                    blue_ratio = (ratio - 0.6) / 0.4
                    r = int(255 * (1 - blue_ratio))
                    g = int(255 * (1 - blue_ratio))
                    b = 255
                    item.setBackground(QColor(r, g, b))
                else:
                    red_ratio = ratio / 0.6
                    r = 255
                    g = int(255 * (1 - red_ratio))
                    b = int(255 * (1 - red_ratio))
                    set_color_and_tooltip(QColor(r, g, b), "RSSI is low (≤60% of max)")
        except Exception:
            pass

    # 4. PID columns
    elif col_name.startswith("axisP["):
        try:
            v = float(value)
            if abs(v) > 250:
                set_color_and_tooltip(QColor(255, 120, 120), "P-term spike (>250)")
            elif df is not None and row is not None:
                axis_idx = int(col_name[6])
                setpoint_col = f"setpoint[{axis_idx}]"
                gyro_col = f"gyroADC[{axis_idx}]"
                if setpoint_col in df.columns and gyro_col in df.columns:
                    setpoint = df.at[row, setpoint_col]
                    gyro = df.at[row, gyro_col]
                    expected = setpoint - gyro
                    if (expected != 0) and (v * expected < 0) and abs(v) > 100:
                        set_color_and_tooltip(QColor(255, 255, 120), "P-term high but opposite sign to setpoint")
                    else:
                        item.setBackground(QColor(180, 255, 180))  # green
                else:
                    item.setBackground(QColor(180, 255, 180))  # green
            else:
                item.setBackground(QColor(180, 255, 180))  # green
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    elif col_name.startswith("axisI["):
        try:
            v = float(value)
            if abs(v) > 200:
                set_color_and_tooltip(QColor(255, 120, 120), "Large I-term value (>200)")
            elif df is not None and row is not None:
                axis_idx = int(col_name[6])
                setpoint_col = f"setpoint[{axis_idx}]"
                if setpoint_col in df.columns:
                    setpoint = df.at[row, setpoint_col]
                    if abs(setpoint) < 1 and abs(v) > 50:
                        set_color_and_tooltip(QColor(255, 255, 120), "I-term accumulating with zero setpoint (possible wind-up)")
                    else:
                        item.setBackground(QColor(180, 255, 180))
                else:
                    item.setBackground(QColor(180, 255, 180))
            else:
                item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    elif col_name.startswith("axisD[") and col_name not in ("axisD[2]",):
        try:
            v = float(value)
            if abs(v) > 200:
                set_color_and_tooltip(QColor(255, 120, 120), "D-term spike (>200)")
            else:
                item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    elif col_name.startswith("axisF["):
        try:
            v = float(value)
            if df is not None and row is not None:
                axis_idx = int(col_name[6])
                rc_col = f"rcCommand[{axis_idx}]"
                if rc_col in df.columns:
                    rc = df.at[row, rc_col]
                    if abs(rc) < 1 and abs(v) > 10:
                        set_color_and_tooltip(QColor(255, 120, 120), "Feedforward with no stick input")
                    else:
                        item.setBackground(QColor(180, 255, 180))
                else:
                    item.setBackground(QColor(180, 255, 180))
            else:
                item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    # motor[0-3] and eRPM[0-3]
    elif col_name.startswith("motor[") and df is not None and row is not None:
        try:
            v = float(value)
            idx = int(col_name[6])
            erpm_col = f"eRPM[{idx}]"
            erpm = df.at[row, erpm_col] if erpm_col in df.columns else None
            if erpm is not None:
                try:
                    erpm_val = float(erpm)
                    if v > 1200 and erpm_val < 100:
                        set_color_and_tooltip(QColor(255, 120, 120), "Motor high, eRPM low (possible desync/failure)")
                        return
                    if erpm_val == 0 and v > 1100:
                        set_color_and_tooltip(QColor(255, 120, 120), "eRPM dropped to 0 while motor command is high")
                        return
                except Exception:
                    pass
            motors = [float(df.at[row, f"motor[{i}]"]) for i in range(4) if f"motor[{i}]" in df.columns]
            if len(motors) == 4:
                if v < 50 and max(motors) >= 1000:
                    set_color_and_tooltip(QColor(255, 120, 120), "Motor struck min value (possible desync)")
                    return
                if v > 2000 and min(motors) < 1000:
                    set_color_and_tooltip(QColor(255, 120, 120), "Motor struck max value (possible desync)")
                    return
                if max(motors) - min(motors) > 750:
                    set_color_and_tooltip(QColor(255, 255, 120), "Persistent large difference between motors (>750)")
                    return
            if row > 0 and f"motor[{idx}]" in df.columns:
                prev = float(df.at[row-1, f"motor[{idx}]"])
                if abs(v - prev) > 100:
                    set_color_and_tooltip(QColor(255, 255, 120), "Fast oscillation in motor output")
                    return
            item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    elif col_name.startswith("eRPM[") and df is not None and row is not None:
        try:
            v = float(value)
            idx = int(col_name[5])
            motor_col = f"motor[{idx}]"
            motor = df.at[row, motor_col] if motor_col in df.columns else None
            if motor is not None:
                try:
                    motor_val = float(motor)
                    if motor_val > 1200 and v < 100:
                        set_color_and_tooltip(QColor(255, 120, 120), "Motor high, eRPM low (possible desync/failure)")
                        return
                    if v == 0 and motor_val > 1100:
                        set_color_and_tooltip(QColor(255, 120, 120), "eRPM dropped to 0 while motor command is high")
                        return
                except Exception:
                    pass
            if row > 0 and f"eRPM[{idx}]" in df.columns:
                prev = float(df.at[row-1, f"eRPM[{idx}]"])
                if abs(v - prev) > 200:
                    set_color_and_tooltip(QColor(255, 255, 120), "Big fluctuation in eRPM (possible mechanical issue)")
                    return
            item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    # gyroUnfilt[0-2] - Raw Noise, Sudden Jumps
    elif col_name.startswith("gyroUnfilt[") and df is not None and row is not None:
        try:
            v = float(value)
            axis_idx = int(col_name[10])
            noisy = False
            for offset in [-2, -1, 1, 2]:
                r = row + offset
                if 0 <= r < len(df):
                    neighbor = float(df.at[r, f"gyroUnfilt[{axis_idx}]"])
                    if abs(v - neighbor) > 80 and (v * neighbor < 0):
                        noisy = True
                        break
            if noisy:
                set_color_and_tooltip(QColor(255, 120, 120), "Rapid sign-changing jumps (noise/vibration)")
            else:
                item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    # gyroADC[0-2] - Smoothness, Oscillation, Spikes, Correlation
    elif col_name.startswith("gyroADC[") and df is not None and row is not None:
        try:
            v = float(value)
            axis_idx = int(col_name[8])
            if f"gyroUnfilt[{axis_idx}]" in df.columns:
                raw_val = float(df.at[row, f"gyroUnfilt[{axis_idx}]"])
                diff = abs(v - raw_val)
                if diff < 5 and abs(raw_val) > 1 and abs(v) > 1:
                    set_color_and_tooltip(QColor(255, 255, 120), "Filtered and unfiltered gyro very similar (under-filtered)")
                    return
                if abs(v) < 0.5 * abs(raw_val) and abs(raw_val) > 30:
                    set_color_and_tooltip(QColor(255, 255, 120), "Filtered gyro much flatter than unfiltered (over-filtered)")
                    return
            oscillatory = False
            if row > 0 and row < len(df) - 1:
                prev = float(df.at[row-1, f"gyroADC[{axis_idx}]"])
                nextv = float(df.at[row+1, f"gyroADC[{axis_idx}]"])
                if (v > prev and v > nextv) or (v < prev and v < nextv):
                    if abs(v - prev) > 20 and abs(v - nextv) > 20:
                        oscillatory = True
            if oscillatory:
                set_color_and_tooltip(QColor(255, 255, 120), "Oscillatory pattern detected in gyroADC")
                return
            if row > 0:
                prev = float(df.at[row-1, f"gyroADC[{axis_idx}]"])
                if abs(v - prev) > 60:
                    set_color_and_tooltip(QColor(255, 255, 120), "Sudden spike in gyroADC")
                    return
            erratic = False
            if all(f"gyroADC[{i}]" in df.columns for i in range(3)):
                vals = [float(df.at[row, f"gyroADC[{i}]"]) for i in range(3)]
                if abs(v) > 40 and all(abs(v) > 2 * abs(val) for i, val in enumerate(vals) if i != axis_idx):
                    erratic = True
            if erratic:
                set_color_and_tooltip(QColor(255, 255, 120), "Erratic value on one gyro axis (possible mechanical issue)")
                return
            pid_spike = False
            for pid_col in [f"axisP[{axis_idx}]", f"axisD[{axis_idx}]"]:
                if pid_col in df.columns:
                    pid_val = float(df.at[row, pid_col])
                    if abs(v) > 40 and abs(pid_val) > 40:
                        pid_spike = True
            if pid_spike:
                set_color_and_tooltip(QColor(255, 255, 120), "Gyro spike correlates with PID spike (possible instability)")
                return
            item.setBackground(QColor(180, 255, 180))
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    # accSmooth[0-2]: Filtered Accelerometer Data
    elif col_name.startswith("accSmooth[") and df is not None and row is not None:
        try:
            v = float(value)/100.0
            axis_idx = int(col_name[10])
            if axis_idx in (0, 1):
                if abs(v) < 2:
                    item.setBackground(QColor(180, 255, 180))
                elif abs(v) > 10:
                    set_color_and_tooltip(QColor(255, 120, 120), "Accelerometer axis value is high (possible misalignment or vibration)")
                else:
                    set_color_and_tooltip(QColor(255, 255, 120), "Accelerometer axis value is moderately high")
            elif axis_idx == 2:
                if abs(v - 20.48) < 2:
                    item.setBackground(QColor(180, 255, 180))
                elif abs(v - 20.48) > 10:
                    set_color_and_tooltip(QColor(255, 120, 120), "Z-axis not near freefall accelearation (possible calibration/orientation error)")
                else:
                    set_color_and_tooltip(QColor(255, 255, 120), "Z-axis moderately off from freefall accelearation")
        except Exception:
            set_color_and_tooltip(QColor(255, 255, 120), "Accelerometer data issue")

    # vbatLatest (V): Voltage
    elif col_name == "vbatLatest (V)" and df is not None and row is not None:
        try:
            v = float(value)
            if v > 16:
                item.setBackground(QColor(180, 255, 180))
            elif v < 14:
                set_color_and_tooltip(QColor(255, 120, 120), "Voltage very low (<14V)")
            else:
                set_color_and_tooltip(QColor(255, 255, 120), "Voltage is in warning range")
            if row > 0:
                prev = float(df.at[row-1, "vbatLatest (V)"])
                if abs(v - prev) > 2:
                    set_color_and_tooltip(QColor(255, 120, 120), "Sudden voltage drop detected")
        except Exception:
            set_color_and_tooltip(QColor(255, 255, 120), "Voltage data issue")

    # amperageLatest (A): Current Draw
    elif col_name == "amperageLatest (A)" and df is not None and row is not None:
        try:
            v = float(value)
            if v < 0:
                set_color_and_tooltip(QColor(255, 120, 120), "Negative current (sensor error)")
            elif v < 10:
                item.setBackground(QColor(180, 255, 180))
            elif v > 120:
                set_color_and_tooltip(QColor(255, 120, 120), "Very high current draw (>120A)")
            else:
                set_color_and_tooltip(QColor(255, 255, 120), "High current draw")
            if row > 0:
                prev = float(df.at[row-1, "amperageLatest (A)"])
                if abs(v - prev) > 40:
                    set_color_and_tooltip(QColor(255, 120, 120), "Sudden spike in current draw")
        except Exception:
            set_color_and_tooltip(QColor(255, 255, 120), "Current data issue")
    else:
        item.setBackground(QColor(255, 255, 255))  # white