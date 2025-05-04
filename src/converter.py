import os
import subprocess

def convert_bbl_to_csv(bbl_file):
    """Converts .bbl file to .csv using blackbox_decode in WSL."""
    csv_file = bbl_file.replace(".bbl", ".csv")
    try:
        # Use WSL to run the Linux binary
        command = f"wsl ./mnt/d/Унік/Диплом/blackbox-tools/obj/blackbox_decode /mnt/d/{bbl_file.replace(':', '').replace('\\', '/')} > /mnt/d/{csv_file.replace(':', '').replace('\\', '/')}"
        subprocess.run(command, shell=True, check=True)

        if os.path.exists(csv_file):
            return csv_file
    except subprocess.CalledProcessError:
        return None