# QuMoPa - Quake Mod Packager

QuMoPa is a single-file GUI application for packaging Quake mods as .zip
archives.  QuMoPa strips out any extraneous files (such as config.cfg, saves,
screenshots, etc.) and checks that the folder conforms to the Quake mod format.
This allows the archive to be easily extracted by users into their Quake engine
folders without problems.

## Windows Installation

This script requires a working installation of Python 3.x

You can obtain the Python installer from https://www.python.org

**Important:** When running the installer be sure the box labeled **Add
python.exe to PATH** is checked.

## Running

### Linux

Run `./qumopa.pyw`

### Windows

Double-click the `qumopa` file.

## Usage

QuMoPa will prompt you for a mod folder.  After selecting a folder, you will
be prompted for the file you want to save your zip archive.  If successful, a
new file will be created containing the mod files minus the extraneous bits.

## Troubleshooting

* Double-clicking the script does nothing, or opens a command prompt window and
immediately closes it
    * Re-run the installer, select "Modify", hit Next, check the "Add python to
    environment variables" box, and click Install
