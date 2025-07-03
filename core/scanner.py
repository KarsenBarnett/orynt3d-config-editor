# core/scanner.py
import os

def find_model_folders(root):
    model_folders = []
    for dirpath, dirnames, filenames in os.walk(root):
        if not any(part.startswith('.') for part in dirpath.split(os.sep)):
            model_folders.append(dirpath)
    return model_folders

def find_xmp_files(root):
    xmp_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        if not any(part.startswith('.') for part in dirpath.split(os.sep)):
            for file in filenames:
                if file.lower().endswith(".xmp"):
                    xmp_files.append(os.path.join(dirpath, file))
    return xmp_files
