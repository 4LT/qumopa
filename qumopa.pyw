#!/bin/env python3

import glob
import sys
from traceback import format_exception
from tkinter import messagebox
from tkinter import filedialog
from sys import stderr, stdin
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from configparser import ConfigParser

def_filter = [
    # Include everything
    "**/*",

    # Exclude Quake junk
    "!config.cfg",
    "!*.sav",
    "!*.dem",
    "!*.tga",
    "!*.jpg",
    "!*.jpeg",
    "!*.png",

    # Include automatic playback
    "demo[0-9].dem",
]

class Message:
    def __init__(self, msg, kind="error", fatal=False):
        self.kind = kind
        self.fatal = fatal

        self.box = messagebox.Message(
            message=msg,
            icon=kind,
            title=kind.capitalize(),
            type="abortretryignore" if kind == "warning" else "ok"
        )

    def show(self):
        return self.box.show()

class UserConfig:
    @staticmethod
    def alert(msg):
        messagebox.showwarning(
            message=msg,
            title="Warning"
        )

    def __init__(self):
        self.config = ConfigParser()

        if sys.platform == "win32":
            conf_folder = Path.home().joinpath("AppData/Local/Temp")
        else:
            conf_folder = Path.home().joinpath(".cache")

        conf_folder.mkdir(exist_ok=True, parents=True)
        self.path = conf_folder.joinpath("qumopa.conf")
        self.load()

    def load(self):

        fail = not self.path.exists()

        if not fail:
            try:
                self.config.read(self.path)
            except:
                Config.alert("Failed to load config {}; using defaults"
                        .format(self.path))
                fail = True

        if not fail:
            if "paths" in self.config:
                self.game_path = self.config["paths"].get("Game")
                self.start_save_path = self.config["paths"].get("Save")
            else:
                Config.alert("No \"paths\" section in {}; using defaults"
                        .format(self.path))
                fail = True

        if fail:
            self.game_path = None
            self.start_save_path = None

        return 

    def save(self):
        paths = {}

        if self.game_path is not None:
            paths["Game"] = self.game_path

        if self.start_save_path is not None:
            paths["Save"] = self.start_save_path

        self.config["paths"] = paths

        try:
            with open(self.path, "w") as conf_file:
                self.config.write(conf_file)
        except:
            Config.alert("Failed to write {}".format(self.path))
            return False

        return True


class Application:
    STATE_GETTING_FOLDER = 0
    STATE_GETTING_SAVE = 1

    message = None
    files = None
    save_file = None
    folder = None
    abort = False
    state = STATE_GETTING_FOLDER
    user_config = UserConfig()

    def next(self):
        if self.message is not None:
            response = self.message.show()
            
            if self.message.fatal:
                self.abort = True
            elif self.message.kind == "warning":
                self.abort = response == "abort"
                
                if response == "retry":
                    self.reset()

            elif self.message.kind == "error":
                self.reset()

            self.message = None

        elif self.files is None:
            self.folder = ask_folder(self.user_config.game_path)

            if self.folder is None:
                self.abort = True
            else:
                self.message = check_folder(self.folder)

                if self.message is None:
                    (self.files, self.message) = get_paths(self.folder)

        elif self.save_file is None:
            self.state = Application.STATE_GETTING_SAVE
            start_path = self.user_config.start_save_path or self.folder.parent
            mod_name = get_mod_name(self.folder)
            (self.save_file, self.message) = ask_save(start_path, mod_name)

            if self.save_file is None and self.message is None:
                self.abort = True

    def done(self):
        complete = self.save_file is not None and self.message is None
        return complete or self.abort

    def reset(self):
        if self.state == Application.STATE_GETTING_FOLDER:
            self.files = None
        elif self.state == Application.STATE_GETTING_SAVE:
            self.save_file = None

    def run(self):
        while not self.done():
            self.next()

        if self.abort or not self.finalize():
            exit(1)

    def finalize(self):
        zip_files(self.save_file, self.folder, self.files)
        self.user_config.game_path = self.folder.parent
        self.user_config.start_save_path = str(Path(self.save_file.name).parent)
        self.user_config.save()

        return True

def ask_folder(start_path):
    folder = filedialog.askdirectory(
        mustexist=True,
        title="Choose a mod folder",
        initialdir=start_path
    )

    if folder == ():
        return None
    else:
        return Path(folder)

def ask_save(start_path, mod_name):
    try:
        zip_file = filedialog.asksaveasfile(
            title="Zip mod",
            initialdir=start_path,
            initialfile=mod_name + ".zip",
            filetypes=[
                ("Zip", ".zip"),
                ("Any", "*")
            ],
            mode="wb"
        )
    except:
        return (None, Message("Failed to open zip file for writing"))

    return (zip_file, None)

def check_folder(folder):
    message = None

    progs_path = folder.joinpath("progs.dat")
    pak_path = folder.joinpath("pak0.pak")
    maps_path = folder.joinpath("maps")

    has_pak = pak_path.exists() and not pak_path.is_dir()
    has_progs = progs_path.exists() and not progs_path.is_dir()
    has_maps = maps_path.is_dir()

    if not (has_progs or has_pak or has_maps):
        message = Message(
            "No progs.dat, pak, or maps folder found",
            kind="warning"
        )
    elif not (has_progs or has_pak):
        bsp_pat = str(maps_path) + "/*.bsp"
        has_bsp = next(glob.iglob(bsp_pat), None) != None

        if not has_bsp:
            message = Message(
                "No progs.dat, pak, or maps found",
                kind="warning"
            )

    return message

def get_paths(folder):
    filt = def_filter
    paths = set()

    for pat in filt:
        if len(pat) > 0 and pat[0] == "!":
            for path in glob.iglob(pat[1:], recursive=True, root_dir=folder):
                paths = paths - { path }
        else:
            for path in glob.iglob(pat, recursive=True, root_dir=folder):
                paths.add(path)

    paths = { path for path in paths if not Path(path).is_dir() }
    
    if len(paths) == 0:
        return (None, Message("No files to package"))
    else:
        return (paths, None)

def get_mod_name(path):
    abs_path = path.resolve()
    if len(abs_path.parts) < 2:
        return "unknown"
    else:
        return abs_path.parts[-1]

def zip_files(zip_file, folder, files):
    files = files - { Path(zip_file.name).name }

    success = False
    message = None

    try:
        zip_file_writer = ZipFile(
            zip_file,
            mode="w",
            compression=ZIP_DEFLATED,
            compresslevel=9
        )

        for file in files:
            abs_path = folder.resolve().joinpath(file)
            mod_name = get_mod_name(folder)
            zip_path = Path(mod_name).joinpath(file)
            zip_file_writer.write(abs_path, arcname=zip_path)

        zip_file_writer.close()

    except OSError:
        success = False
        message = Message("Failed to write zip archive", fatal=True)

    return (success, message)

if __name__ == "__main__":
    try:
        Application().run()
    except SystemExit as exit_code:
        exit(exit_code.code)
    except BaseException as exc:
        messagebox.showerror(
            title="Fatal Error",
            message="".join(format_exception(exc, limit=4))
        )
        exit(1)
