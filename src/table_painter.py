from PyQt6.QtGui import QColor

def paint_table_item(item, col_name, value, rssi_max=None, row=None, df=None):
    """
    Paints a QTableWidgetItem based on column name and value.
    - rxSignalReceived, rxFlightChannelsValid: green if 1, red if 0
    - failsafePhase (flags), stateFlags (flags), flightModeFlags (flags): different color per unique value
    - rssi: >60% of max is blue gradient, <=60% is red gradient
    - PID columns: colored by heuristics, green if normal
    """
    # 1. Binary columns
    if col_name in ("rxSignalReceived", "rxFlightChannelsValid"):
        try:
            v = int(value)
            if v == 1:
                item.setBackground(QColor(180, 255, 180))  # green
            elif v == 0:
                item.setBackground(QColor(255, 180, 180))  # red
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
                else:
                    red_ratio = ratio / 0.6
                    r = 255
                    g = int(255 * (1 - red_ratio))
                    b = int(255 * (1 - red_ratio))
                item.setBackground(QColor(r, g, b))
        except Exception:
            pass

    # 4. PID columns
    # axisP[0..2]
    elif col_name.startswith("axisP["):
        try:
            v = float(value)
            # Red: spikes > 250
            if abs(v) > 250:
                item.setBackground(QColor(255, 120, 120))
            # Yellow: high but opposite sign to setpoint (if df and row provided)
            elif df is not None and row is not None:
                axis_idx = int(col_name[6])
                setpoint_col = f"setpoint[{axis_idx}]"
                gyro_col = f"gyroADC[{axis_idx}]"
                if setpoint_col in df.columns and gyro_col in df.columns:
                    setpoint = df.at[row, setpoint_col]
                    gyro = df.at[row, gyro_col]
                    expected = setpoint - gyro
                    if (expected != 0) and (v * expected < 0) and abs(v) > 100:
                        item.setBackground(QColor(255, 255, 120))
                    else:
                        item.setBackground(QColor(180, 255, 180))  # green (normal)
                else:
                    item.setBackground(QColor(180, 255, 180))  # green (normal)
            else:
                item.setBackground(QColor(180, 255, 180))  # green (normal)
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # axisI[0..2]
    elif col_name.startswith("axisI["):
        try:
            v = float(value)
            # Red: large I values
            if abs(v) > 200:
                item.setBackground(QColor(255, 120, 120))
            # Yellow: continues to accumulate after setpoint returns to zero (if df and row provided)
            elif df is not None and row is not None:
                axis_idx = int(col_name[6])
                setpoint_col = f"setpoint[{axis_idx}]"
                if setpoint_col in df.columns:
                    setpoint = df.at[row, setpoint_col]
                    if abs(setpoint) < 1 and abs(v) > 50:
                        item.setBackground(QColor(255, 255, 120))
                    else:
                        item.setBackground(QColor(180, 255, 180))  # green (normal)
                else:
                    item.setBackground(QColor(180, 255, 180))  # green (normal)
            else:
                item.setBackground(QColor(180, 255, 180))  # green (normal)
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # axisD[0..1]
    elif col_name.startswith("axisD[") and col_name not in ("axisD[2]",):
        try:
            v = float(value)
            # Red: very high spikes
            if abs(v) > 200:
                item.setBackground(QColor(255, 120, 120))
            else:
                item.setBackground(QColor(180, 255, 180))  # green (normal)
            # Yellow: jittery D-term (not implemented here, needs rolling std)
            # Red: sustained non-zero during hover (not implemented here)
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # axisF[0..2]
    elif col_name.startswith("axisF["):
        try:
            v = float(value)
            # Red: feedforward with no stick input (if df and row provided)
            if df is not None and row is not None:
                axis_idx = int(col_name[6])
                rc_col = f"rcCommand[{axis_idx}]"
                if rc_col in df.columns:
                    rc = df.at[row, rc_col]
                    if abs(rc) < 1 and abs(v) > 10:
                        item.setBackground(QColor(255, 120, 120))
                    else:
                        item.setBackground(QColor(180, 255, 180))  # green (normal)
                else:
                    item.setBackground(QColor(180, 255, 180))  # green (normal)
            else:
                item.setBackground(QColor(180, 255, 180))  # green (normal)
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # motor[0-3] and eRPM[0-3]
    elif col_name.startswith("motor[") and df is not None and row is not None:
        try:
            v = float(value)
            idx = int(col_name[6])
            # 1. Desync or Failure: motor high, eRPM low/zero
            erpm_col = f"eRPM[{idx}]"
            erpm = df.at[row, erpm_col] if erpm_col in df.columns else None
            if erpm is not None:
                try:
                    erpm_val = float(erpm)
                    if v > 1200 and erpm_val < 100:
                        item.setBackground(QColor(255, 120, 120))  # red
                        return
                    if erpm_val == 0 and v > 1100:
                        item.setBackground(QColor(255, 120, 120))  # red
                        return
                except Exception:
                    pass
            # 4. Stuck min/max
            motors = [float(df.at[row, f"motor[{i}]"]) for i in range(4) if f"motor[{i}]" in df.columns]
            if len(motors) == 4:
                if abs(v - min(motors)) < 1 and max(motors) - min(motors) > 100:
                    item.setBackground(QColor(255, 120, 120))  # red
                    return
                if abs(v - max(motors)) < 1 and min(motors) < 1200:
                    item.setBackground(QColor(255, 120, 120))  # red
                    return
                # 2. Asymmetry
                if max(motors) - min(motors) > 150:
                    item.setBackground(QColor(255, 255, 120))  # yellow
                    return
            # 4. Noisy/Oscillating (simple: large diff from prev row)
            if row > 0 and f"motor[{idx}]" in df.columns:
                prev = float(df.at[row-1, f"motor[{idx}]"])
                if abs(v - prev) > 100:
                    item.setBackground(QColor(255, 255, 120))  # yellow
                    return
            # If all OK
            item.setBackground(QColor(180, 255, 180))  # green
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    elif col_name.startswith("eRPM[") and df is not None and row is not None:
        try:
            v = float(value)
            idx = int(col_name[5])
            # 1. Desync or Failure: motor high, eRPM low/zero
            motor_col = f"motor[{idx}]"
            motor = df.at[row, motor_col] if motor_col in df.columns else None
            if motor is not None:
                try:
                    motor_val = float(motor)
                    if motor_val > 1200 and v < 100:
                        item.setBackground(QColor(255, 120, 120))  # red
                        return
                    if v == 0 and motor_val > 1100:
                        item.setBackground(QColor(255, 120, 120))  # red
                        return
                except Exception:
                    pass
            # 4. Noisy/Oscillating (simple: large diff from prev row)
            if row > 0 and f"eRPM[{idx}]" in df.columns:
                prev = float(df.at[row-1, f"eRPM[{idx}]"])
                if abs(v - prev) > 200:
                    item.setBackground(QColor(255, 255, 120))  # yellow
                    return
            # If all OK
            item.setBackground(QColor(180, 255, 180))  # green
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # gyroUnfilt[0-2] - Raw Noise, Sudden Jumps
    elif col_name.startswith("gyroUnfilt[") and df is not None and row is not None:
        try:
            v = float(value)
            axis_idx = int(col_name[10])
            # Check for rapid sign changes (noise/vibration)
            noisy = False
            for offset in [-2, -1, 1, 2]:
                r = row + offset
                if 0 <= r < len(df):
                    neighbor = float(df.at[r, f"gyroUnfilt[{axis_idx}]"])
                    # Large jump and sign change
                    if abs(v - neighbor) > 80 and (v * neighbor < 0):
                        noisy = True
                        break
            if noisy:
                item.setBackground(QColor(255, 120, 120))  # red
            else:
                item.setBackground(QColor(180, 255, 180))  # green
        except Exception:
            item.setBackground(QColor(180, 255, 180))

    # gyroADC[0-2] - Smoothness, Oscillation, Spikes, Correlation
    elif col_name.startswith("gyroADC[") and df is not None and row is not None:
        try:
            v = float(value)
            axis_idx = int(col_name[8])
            # 1. Compare to gyroUnfilt (smoothness)
            if f"gyroUnfilt[{axis_idx}]" in df.columns:
                raw_val = float(df.at[row, f"gyroUnfilt[{axis_idx}]"])
                diff = abs(v - raw_val)
                # If filtered and unfiltered are very close, under-filtered (yellow)
                if diff < 5:
                    item.setBackground(QColor(255, 255, 120))
                    return
                # If filtered is much flatter than unfiltered, over-filtered (yellow)
                if abs(v) < 0.5 * abs(raw_val) and abs(raw_val) > 30:
                    item.setBackground(QColor(255, 255, 120))
                    return
            # 2. Oscillatory pattern: up-down-up in 3 rows
            oscillatory = False
            if row > 0 and row < len(df) - 1:
                prev = float(df.at[row-1, f"gyroADC[{axis_idx}]"])
                nextv = float(df.at[row+1, f"gyroADC[{axis_idx}]"])
                if (v > prev and v > nextv) or (v < prev and v < nextv):
                    if abs(v - prev) > 20 and abs(v - nextv) > 20:
                        oscillatory = True
            if oscillatory:
                item.setBackground(QColor(255, 255, 120))  # yellow
                return
            # 3. Sudden spike
            if row > 0:
                prev = float(df.at[row-1, f"gyroADC[{axis_idx}]"])
                if abs(v - prev) > 60:
                    item.setBackground(QColor(255, 255, 120))  # yellow
                    return
            # 4. Compare across axes for erratic axis
            erratic = False
            if all(f"gyroADC[{i}]" in df.columns for i in range(3)):
                vals = [float(df.at[row, f"gyroADC[{i}]"]) for i in range(3)]
                if abs(v) > 40 and all(abs(v) > 2 * abs(val) for i, val in enumerate(vals) if i != axis_idx):
                    erratic = True
            if erratic:
                item.setBackground(QColor(255, 255, 120))  # yellow
                return
            # 5. Correlation with PID terms (if available)
            pid_spike = False
            for pid_col in [f"axisP[{axis_idx}]", f"axisD[{axis_idx}]"]:
                if pid_col in df.columns:
                    pid_val = float(df.at[row, pid_col])
                    if abs(v) > 40 and abs(pid_val) > 40:
                        pid_spike = True
            if pid_spike:
                item.setBackground(QColor(255, 255, 120))  # yellow
                return
            # If all OK
            item.setBackground(QColor(180, 255, 180))  # green
        except Exception:
            item.setBackground(QColor(180, 255, 180))  # fallback to green

    # accSmooth[0-2]: Filtered Accelerometer Data
    elif col_name.startswith("accSmooth[") and df is not None and row is not None:
        try:
            v = float(value)
            axis_idx = int(col_name[10])
            # X, Y axes: should be near 0 in hover
            if axis_idx in (0, 1):
                if abs(v) < 2:
                    item.setBackground(QColor(180, 255, 180))  # green
                elif abs(v) > 10:
                    item.setBackground(QColor(255, 120, 120))  # red
                else:
                    item.setBackground(QColor(255, 255, 120))  # yellow
            # Z axis: should be near -9.8 in hover
            elif axis_idx == 2:
                if abs(v + 9.8) < 2:
                    item.setBackground(QColor(180, 255, 180))  # green
                elif abs(v + 9.8) > 6:
                    item.setBackground(QColor(255, 120, 120))  # red
                else:
                    item.setBackground(QColor(255, 255, 120))  # yellow
        except Exception:
            item.setBackground(QColor(255, 255, 120))  # fallback yellow

    # vbatLatest (V): Voltage
    elif col_name == "vbatLatest (V)" and df is not None and row is not None:
        try:
            v = float(value)
            # Normal: >14V (4S) or >21V (6S) at start, gradual decline
            if v > 16:
                item.setBackground(QColor(180, 255, 180))  # green
            elif v < 14:
                item.setBackground(QColor(255, 120, 120))  # red
            else:
                item.setBackground(QColor(255, 255, 120))  # yellow
            # Sudden drop detection
            if row > 0:
                prev = float(df.at[row-1, "vbatLatest (V)"])
                if abs(v - prev) > 2:
                    item.setBackground(QColor(255, 120, 120))  # red
        except Exception:
            item.setBackground(QColor(255, 255, 120))  # fallback yellow

    # amperageLatest (A): Current Draw
    elif col_name == "amperageLatest (A)" and df is not None and row is not None:
        try:
            v = float(value)
            # Normal: 0-5A idle, up to 100A+ on punch
            if v < 0:
                item.setBackground(QColor(255, 120, 120))  # red (sensor error)
            elif v < 10:
                item.setBackground(QColor(180, 255, 180))  # green
            elif v > 120:
                item.setBackground(QColor(255, 120, 120))  # red (very high)
            else:
                item.setBackground(QColor(255, 255, 120))  # yellow
            # Sudden spike detection
            if row > 0:
                prev = float(df.at[row-1, "amperageLatest (A)"])
                if abs(v - prev) > 40:
                    item.setBackground(QColor(255, 120, 120))  # red
        except Exception:
            item.setBackground(QColor(255, 255, 120))  # fallback yellow