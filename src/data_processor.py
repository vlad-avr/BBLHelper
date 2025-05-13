from bokeh.plotting import figure, show
from bokeh.palettes import Category10
from itertools import cycle
import pandas as pd

def load_and_clean_csv(csv_file, load_non_numeric=False):
    """
    Loads a CSV file, removes all non-numeric columns, and converts time_us to milliseconds.
    Adds a calculated "throttle" column based on motor outputs.

    Args:
        csv_file (str): Path to the CSV file.
        load_non_numeric (bool): Whether to include non-numeric columns.

    Returns:
        pd.DataFrame: Cleaned DataFrame with only numeric columns.
    """
    df = pd.read_csv(csv_file)

    # Remove non-numeric columns
    if not load_non_numeric:
        df = df.select_dtypes(include=["number"])

    # Rename " time (us)" to "time_ms" if it exists
    if " time (us)" in df.columns:
        df = df.rename(columns={" time (us)": "time_ms"})

    # Convert time_us to milliseconds
    if "time_ms" in df.columns:
        df["time_ms"] = df["time_ms"] / 1000.0

    # Add a "throttle" column if motor columns exist
    motor_columns = [" motor[0]", " motor[1]", " motor[2]", " motor[3]"]
    if all(col in df.columns for col in motor_columns):
        df["throttle"] = df[" motor[0]"] + df[" motor[1]"] + df[" motor[2]"] + df[" motor[3]"]

    return df

def plot_pid_loop_analysis(csv_file):
    """Plots PID Loop Analysis."""
    df = load_and_clean_csv(csv_file)

    # Ensure required columns exist
    y_columns = [" gyroADC[0]", " setpoint[0]", " axisP[0]", " axisI[0]", " axisD[0]", " axisF[0]"]
    valid_columns = [col for col in y_columns if col in df.columns]

    if not valid_columns:
        print("Error: No valid columns for PID Loop Analysis.")
        return

    # Create a Bokeh figure
    p = figure(title="PID Loop Analysis (Roll)", x_axis_label="Time (ms)", y_axis_label="Values", width=900, height=600)

    # Assign colors to each column
    colors = cycle(Category10[10])  # Cycle through Category10 palette

    for column, color in zip(valid_columns, colors):
        p.line(df["time_ms"], df[column], legend_label=column, line_width=2, color=color)

    # Customize the legend
    p.legend.title = "PID Components"
    p.legend.location = "top_left"

    # Show the plot
    show(p)

def plot_throttle_voltage(csv_file):
    """Plots Throttle and Voltage Drop."""
    df = load_and_clean_csv(csv_file)

    # Ensure required columns exist
    y_columns = [" motor[0]", " motor[1]", " motor[2]", " motor[3]", " vbatLatest (V)"]
    valid_columns = [col for col in y_columns if col in df.columns]

    if not valid_columns:
        print("Error: No valid columns for Throttle and Voltage Drop.")
        return

    # Create a Bokeh figure
    p = figure(title="Throttle and Voltage Drop", x_axis_label="Time (ms)", y_axis_label="Values", width=900, height=600)

    # Assign colors to each column
    colors = cycle(Category10[10])  # Cycle through Category10 palette

    for column, color in zip(valid_columns, colors):
        p.line(df["time_ms"], df[column], legend_label=column, line_width=2, color=color)

    # Customize the legend
    p.legend.title = "Throttle and Voltage"
    p.legend.location = "top_left"

    # Show the plot
    show(p)

def plot_motor_desync(csv_file):
    """Plots Motor Desync or Oscillations."""
    df = load_and_clean_csv(csv_file)

    # Dynamically find motor columns
    motor_columns = [col for col in df.columns if col.startswith(" motor")]

    if not motor_columns:
        print("Error: No valid motor columns for Motor Desync or Oscillations.")
        return

    # Create a Bokeh figure
    p = figure(title="Motor Desync or Oscillations", x_axis_label="Time (ms)", y_axis_label="Motor Outputs", width=900, height=600)

    # Assign colors to each column
    colors = cycle(Category10[10])  # Cycle through Category10 palette

    for column, color in zip(motor_columns, colors):
        p.line(df["time_ms"], df[column], legend_label=column, line_width=2, color=color)

    # Customize the legend
    p.legend.title = "Motor Outputs"
    p.legend.location = "top_left"

    # Show the plot
    show(p)

def plot_stick_input_vs_movement(csv_file):
    """Plots Stick Input vs. Actual Movement."""
    df = load_and_clean_csv(csv_file)

    # Ensure required columns exist
    y_columns = [" rcCommand[0]", " rcCommand[1]", " rcCommand[2]",
                 " gyroADC[0]", " gyroADC[1]", " gyroADC[2]"]
    valid_columns = [col for col in y_columns if col in df.columns]

    if not valid_columns:
        print("Error: No valid columns for Stick Input vs. Actual Movement.")
        return

    # Create a Bokeh figure
    p = figure(title="Stick Input vs. Actual Movement", x_axis_label="Time (ms)", y_axis_label="Values", width=900, height=600)

    # Assign colors to each column
    colors = cycle(Category10[10])  # Cycle through Category10 palette

    for column, color in zip(valid_columns, colors):
        p.line(df["time_ms"], df[column], legend_label=column, line_width=2, color=color)

    # Customize the legend
    p.legend.title = "Stick Input and Movement"
    p.legend.location = "top_left"

    # Show the plot
    show(p)