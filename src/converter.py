import os
import subprocess
import shutil

# Keywords of headers to keep
# keywords = [
#     "PID",
#     "rateProfileValues",
#     "gyro",
#     "accel",
#     "dterm",
#     "looptime",
#     "blackbox_rate",
#     "firmware",
#     "Product",
#     "feature",
#     "rcSmoothing",
#     "setpoint",
#     "anti_gravity",
#     "dynamic_filter",
#     "DynLPF",
#     "gyro_lowpass",
#     "dterm_lowpass",
#     "yaw_lowpass"
#     ]
def convert_bbl_to_csv(bbl_file: str, output_dir: str) -> str | None:
    """
    Converts a .bbl file to multiple output files (.csv and .event) using blackbox_decode.exe.
    Extracts unique header lines into a headers.txt file.

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
        # Extract unique headers from the .bbl file
        headers_file_path = os.path.join(output_dir, "headers.txt")
        seen_headers = set()  # Track unique headers
        with open(bbl_file, "r", encoding="latin-1") as bbl:  # Use 'latin-1' encoding
            with open(headers_file_path, "w", encoding="utf-8") as headers_file:
                for line in bbl:
                    if line.startswith("H "):
                        header_content = line[2:].strip()  # Remove "H " prefix and strip whitespace
                        # if any(kw.lower() in header_content.lower() for kw in keywords):
                        if header_content not in seen_headers:  # Check for duplicates
                            headers_file.write(header_content + "\n")
                            seen_headers.add(header_content)  # Add to the set

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