#!/usr/bin/env python3
import glob
import tarfile
import subprocess
import sys
import os
import logging


def setup_logging():
    logging.basicConfig(filename='extension_install.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


def install_extensions_from_file(file_path):
    if not os.path.exists(file_path):
        logging.error(f"Error: File {file_path} does not exist.")
        return

    with open(file_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        extension = line.strip()  # Remove newline and any leading/trailing whitespaces
        if extension:  # Skip empty lines
            logging.info(f"Installing extension: {extension}")
            try:
                subprocess.run(["code", "--install-extension", extension], check=True)
                logging.info(f"Successfully installed extension: {extension}")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install extension: {extension}. Error: {str(e)}")

def cleanup_and_archive(dest_folder, archive_name):
    # Delete .sigzip files
    for sigzip_file in glob.glob(os.path.join(dest_folder, "*.sigzip")):
        os.remove(sigzip_file)
        logging.info(f"Deleted {sigzip_file}")

    # Create tar.gz archive
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(dest_folder, arcname=os.path.basename(dest_folder))
        logging.info(f"Archived {dest_folder} into {archive_name}")


if __name__ == "__main__":
    setup_logging()
    destination_folder = os.path.expanduser("~/.vscode/extensions/")

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <path_to_text_file>")
    else:
        file_path = sys.argv[1]
        install_extensions_from_file(file_path)
        cleanup_and_archive(destination_folder, "vscode-extensions-latest.tar.gz")
