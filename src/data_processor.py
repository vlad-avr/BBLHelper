import pandas as pd

def load_and_clean_csv(csv_file):
    """
    Loads a CSV file, removes all non-numeric columns, and converts time_us to milliseconds.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with only numeric columns.
    """
    df = pd.read_csv(csv_file)

    # Remove non-numeric columns
    df = df.select_dtypes(include=["number"])

    # Rename " time (us)" to "time_us" if it exists
    if " time (us)" in df.columns:
        df = df.rename(columns={" time (us)": "time_ms"})

    # Convert time_us to milliseconds
    if "time_ms" in df.columns:
        df["time_ms"] = df["time_ms"] / 1000.0

    return df