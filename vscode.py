#!/usr/bin/env python3.11
import glob
import tarfile
import subprocess
import sys
import os
import logging
from inotify.adapters import Inotify
from threading import Thread
import shutil

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

def monitor_directory(directory, dest_folder):
    inotify = Inotify()

    inotify.add_watch(directory)

    for event in inotify.event_gen():
        if event is not None:
            (header, type_names, watch_path, filename) = event
            logging.info(f"Event {type_names} occurred on {os.path.join(watch_path, filename)}")

            if 'IN_CREATE' in type_names or 'IN_MOVED_TO' in type_names:
                src_file = os.path.join(watch_path, filename)
                dest_file = os.path.join(dest_folder, filename)

                if not os.path.exists(dest_file):
                    shutil.copy(src_file, dest_file)
                    logging.info(f"Copied {src_file} to {dest_file}")

def cleanup_and_archive(dest_folder, archive_name):
    # Delete .sigzip files
    for sigzip_file in glob.glob(os.path.join(dest_folder, "*.sigzip")):
        os.remove(sigzip_file)
        logging.info(f"Deleted {sigzip_file}")

    # Rename remaining files to have .vsix extension
    for filename in os.listdir(dest_folder):
        old_filepath = os.path.join(dest_folder, filename)
        new_filepath = os.path.join(dest_folder, f"{filename}.vsix")

        os.rename(old_filepath, new_filepath)
        logging.info(f"Renamed {old_filepath} to {new_filepath}")

    # Create tar.gz archive
    with tarfile.open(archive_name, "w:gz") as tar:
        tar.add(dest_folder, arcname=os.path.basename(dest_folder))
        logging.info(f"Archived {dest_folder} into {archive_name}")

if __name__ == "__main__":
    setup_logging()

    monitored_directory = os.path.expanduser("~/.config/Code/CachedExtensionVSIXs")
    destination_folder = os.path.expanduser("~/vsixfiles")

    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    Thread(target=monitor_directory, args=(monitored_directory, destination_folder)).start()

    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <path_to_text_file>")
    else:
        file_path = sys.argv[1]
        install_extensions_from_file(file_path)
    cleanup_and_archive(destination_folder, "vscode-extensions-latest.tar.gz")
