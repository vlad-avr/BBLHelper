import os
import subprocess
import shutil

def convert_bbl_to_csv(bbl_file: str, output_dir: str) -> str | None:
    """
    Converts a .bbl file to multiple output files (.csv and .event) using blackbox_decode.exe.

    Args:
        bbl_file (str): Full path to the .bbl file (e.g., "D:\\path\\to\\log.bbl")
        output_dir (str): Path to the folder where the decoded files should be saved.

    Returns:
        str | None: Path to the folder containing the generated files or None if failed.
    """
    bbl_file = os.path.abspath(bbl_file)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # Construct the relative path to blackbox_decode.exe
    script_dir = os.path.dirname(__file__)
    decoder_exe_path = os.path.join(script_dir, "..", "util", "blackbox_decode.exe")
    decoder_exe_path = os.path.abspath(decoder_exe_path)  # Normalize the path

    try:
        # Run the decoder
        subprocess.run([decoder_exe_path, bbl_file], stderr=subprocess.PIPE, check=True)

        # Move all generated files to the output folder
        for file in os.listdir(os.path.dirname(bbl_file)):
            if file.endswith(".csv") or file.endswith(".event"):
                source_path = os.path.join(os.path.dirname(bbl_file), file)
                destination_path = os.path.join(output_dir, file)
                shutil.move(source_path, destination_path)

        # Return the path to the output folder
        return output_dir
    except subprocess.CalledProcessError as e:
        print(f"Decoding failed: {e.stderr.decode()}")
    except FileNotFoundError:
        print("Executable or .bbl file not found.")

    return None