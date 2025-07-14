#!/usr/bin/env python3
import argparse
from pathlib import Path


# Deletes the empty files
# def delete_empty_jsonl_files(directory: Path):
#     """
#     Delete all empty .jsonl files in the given directory.
#     Prints the path of each file it deletes.
#     """
#     for file in directory.glob("*.jsonl"):
#         if file.is_file() and file.stat().st_size == 0:
#             print(f"Deleting empty file: {file}")
#             file.unlink()

# def main():
#     parser = argparse.ArgumentParser(
#         description="Delete empty .jsonl files from a directory."
#     )
#     parser.add_argument(
#         "directory",
#         nargs="?",
#         default="Res_Pairs - Copy",
#         help="Directory to scan (default: current directory)."
#     )
#     args = parser.parse_args()
#     dir_path = Path(args.directory).resolve()
#     if not dir_path.is_dir():
#         print(f"Error: {dir_path} is not a directory.")
#         return
#     delete_empty_jsonl_files(dir_path)

# if __name__ == "__main__":
#     main()

# import os

# # 1. Path to the directory containing your files
# folder = "Output"

# # 2. Iterate over every file in that folder
# for filename in os.listdir(folder):
#     # 3. Check if the old substring is in the filename
#     if "gen_problem_gen" in filename:
#         # 4. Build the new filename by replacing the substring
#         new_name = filename.replace("gen_problem_gen", "gen_prob_gen")
#         # 5. Perform the rename
#         os.rename(
#             os.path.join(folder, filename),
#             os.path.join(folder, new_name)
#         )
#         print(f"Renamed: {filename} → {new_name}")


