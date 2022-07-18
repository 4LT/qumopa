#!/bin/env python3

import glob
import shutil
from tkinter import messagebox
from sys import stderr, stdin
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

def_filter = [
    # Include everything
    "**/*",

    # Exclude qumopa junk
    "!qumopa.py",
    "!_qumopa_conf.py",

    # Exclude Quake junk
    "!config.cfg",
    "!*.sav",
    "!*.dem",
    "!*.tga",
    "!*.jpg",
    "!*.jpeg",
    "!*.png",

    # Exclude other junk
    "!__pycache__/**",

    # Include automatic playback
    "demo[0-9].dem",
]

def main():
    (files, error_msg) = get_paths()

    if files == None:
        alert(error_msg)
        exit(1)

    (success, error_msg) = zip_files(files)

    if not success:
        alert(error_msg)
        exit(1)

def get_paths():
    conf_path = Path("_qumopa_conf.py")

    if conf_path.exists():
        try:
            from _qumopa_conf import filter as filt
        except ImportError:    
            return (None, "Unable to import configuration")
    else:
        filt = def_filter


    paths = set()

    for pat in filt:
        if len(pat) > 0 and pat[0] == "!":
            for path in glob.iglob(pat[1:], recursive=True):
                paths = paths - { path }
        else:
            for path in glob.iglob(pat, recursive=True):
                paths.add(path)

    paths = { path for path in paths if not Path(path).is_dir() }

    return (paths, None)

def zip_files(files):
    if len(files) == 0:
        return (False, "No files to zip")

    mod_name = Path.cwd().parts[-1]

    if "/" in mod_name or "\\" in mod_name or len(mod_name) == 0:
        return (False, "Invalid mod name")

    zip_filename = mod_name + ".zip"
    files = files - { zip_filename }

    try:
        zip_file = ZipFile(
            zip_filename,
            mode="w",
            compression=ZIP_DEFLATED,
            compresslevel=9
        )

        for file in files:
            full_path = Path(mod_name).joinpath(file)
            zip_file.write(file, arcname=full_path)

        zip_file.close()
    except OSError:
        return (False, "Failed to write zip archive")

    return (True, None)

def alert(msg):
    if stdin and stdin.isatty():
        print(msg, file=stderr)
    else:
        messagebox.showerror(title="Error", message=msg)

if __name__ == "__main__":
    main()
