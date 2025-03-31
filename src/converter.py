import os
import subprocess

def convert_bbl_to_csv(bbl_file):
    """Converts .bbl file to .csv using blackbox_decode."""
    csv_file = bbl_file.replace(".bbl", ".csv")
    try:
        command = f"blackbox_decode {bbl_file} > {csv_file}"
        subprocess.run(command, shell=True, check=True)

        if os.path.exists(csv_file):
            return csv_file
    except subprocess.CalledProcessError:
        return None