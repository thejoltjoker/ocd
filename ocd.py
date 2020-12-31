#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
file_organizer.py
Organize files based on type etc.
"""

import shutil
import hashlib
import argparse
from pathlib import Path
import logging
from logging.config import dictConfig
from datetime import datetime
from pprint import pformat

try:
    import xxhash

    HASHER = xxhash.xxh3_64
except ModuleNotFoundError:
    HASHER = hashlib.md5
GROUPS = {'book': ['epub', 'mobi'],
          'dynamic': ['pl', 'jsp', 'asp', 'php', 'cgi', 'shtml'],
          'encoded': ['bin', 'enc', 'hex', 'hqx', 'mim', 'mime', 'uue'],
          'compressed': ['7z', 'alz', 'deb', 'gz', 'pkg', 'pup', 'rar', 'rpm', 'sea', 'sfx', 'sit', 'sitx', 'tar.gz',
                         'tgz', 'war', 'zip', 'zipx'],
          'configuration': ['cfg', 'clg', 'dbb', 'ini', 'keychain', 'prf', 'prx', 'psf', 'rdf', 'reg', 'thmx', 'vmx',
                            'wfc'],
          'backup': ['asd', 'bak', 'bkp', 'bup', 'dba', 'dbk', 'fbw', 'gho', 'nba', 'old', 'ori', 'sqb', 'tlg', 'tmp'],
          'database': ['accdb', 'db', 'dsn', 'mdb', 'mdf', 'pdb', 'sql', 'sqlite'],
          'developer': ['as', 'asc', 'c', 'cbl', 'cc', 'class', 'cp', 'cpp', 'cs', 'csproj', 'dev', 'dtd', 'f', 'fs',
                        'fsproj', 'fsx', 'ftl', 'gem', 'h', 'hpp', 'ise', 'ism', 'java', 'm', 'ocx', 'pas', 'pod',
                        'pro',
                        'py', 'r', 'rb', 'sh', 'src', 'tcl', 'trx', 'v', 'vbproj', 'vcproj', 'vtm', 'xcodeproj'],
          'web': ['html', 'htm', 'php', 'alx', 'asax', 'asmx', 'aspx', 'atom', 'att', 'axd', 'chm', 'dwt'],
          'video': ['mp4', 'qt', 'wmv', 'avi', 'mpg', 'mov', 'mpeg', 'flv', 'mkv', 'mod', 'm2ts', '3gp', 'dat', 'mov',
                    'avi', 'qt', 'smi', 'sml', 'smil', 'flc', 'fli', 'vfw', 'mpeg', 'mpg', 'm15', 'm1u',
                    'm1a', 'm75', 'mls', 'mp2', 'mpm', 'mp', 'rm', 'wmv', 'flv', 'swf'],
          'image': ['jpg', 'arw', 'gif', 'psd', 'jpeg', 'dng', 'cr2', 'arw', 'tif', 'tiff', 'png', 'gpr',
                    'bmp', 'exr', 'sr2', 'arw', 'bmp', 'gif', 'jpeg', 'jpg', 'pcx', 'png'],
          'photoshop': ['psd', 'psb'],
          'illustrator': ['ai'],
          'diskimage': ['dmg', 'iso', 'mdf', 'nrg', 'nri', 'pvm', 'toast', 'vcd', 'vmdk'],
          'disc': ['iso', 'bin', 'dmg', 'toast', 'vcd'],
          'luts': ['cube', 'mga'],
          '3d': ['abc', 'obj', 'ma', 'mb', '3ds', 'fbx', 'fbx', 'obj', 'ma', 'mb'],
          'archives': ['zip', 'tar', 'gz', 'rar', '7z', '7zip', 'arj', 'z'],
          'document': ['doc', 'gdoc', 'xls', 'docx', 'xlsx', 'pdf', 'txt', 'md', 'pptx', 'ppt', 'odt', 'doc', 'docx',
                       'wbk', 'xls', 'xlsx', 'ppt', 'pptx', 'oft', 'pub', 'msg', 'one', 'xsf', 'xsn',
                       'grv', 'mpp', 'mpt', 'acl', 'pip', 'thmx', 'aw', 'bld', 'blg', 'bvp', 'cdd', 'cdf', 'contact',
                       'csv', 'dat', 'dif', 'dmsp', 'efx', 'epw', 'exif', 'exp', 'fdb', 'fxp', 'gbr', 'gpi',
                       'hdf', 'id2', 'lib', 'mat', 'mcd', 'menc', 'mw', 'ndx', 'not', 'notebook', 'out', 'ovf', 'pdx',
                       'pfc', 'pps', 'ppsx', 'pptm', 'prj', 'qbw', 'sdf', 'svf', 'tar', 'tsv', 'vcf', 'vdb', 'vxml',
                       'windowslivecontact', 'wlmp', 'xfd', 'xml', 'xsl', 'xslt', 'lit', 'log', 'lst', 'odt', 'opml',
                       'pages', 'rtf', 'sig', 'tex', 'txt', 'wpd', 'wps', 'pdf'],
          'audio': ['mp3', 'wav', 'flac', 'opus', 'wma', 'aif', 'mpa', 'ogg', 'aiff', 'mid', 'aac', 'gsm', 'sd2', 'qcp',
                    'kar', 'smf', 'midi', 'mid', 'ulw', 'snd', 'aifc', 'aif', 'aiff', 'm3url', 'm3u',
                    'wav', 'rm', 'au', 'ram', 'mp3', 'wmv'],
          'app': ['exe', 'app', 'apk', 'msi'],
          'executable': ['exe', 'cmd', 'bat', 'com', 'msi', 'app'],
          'fonts': ['ttf', 'otf'],
          'plugin': ['8bi', 'arx', 'crx', 'plugin', 'vst', 'xll'],
          'system': ['bashrc', 'cab', 'cpl', 'cur', 'dll', 'dmp', 'drv', 'hlp', 'ico', 'key', 'lnk', 'msp', 'prf',
                     'profile', 'scf', 'scr', 'sys']
          }
# Setup logging
logging_level = logging.INFO
logging_config = dict(
    version=1,
    formatters={
        "f": {"format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"}
    },
    handlers={
        "h": {"class": "logging.StreamHandler",
              "formatter": "f",
              "level": logging_level}
    },
    root={
        "handlers": ["h"],
        "level": logging_level,
    },
)

dictConfig(logging_config)

logger = logging.getLogger()


class Organizer:
    def __init__(self, source, destination=None, exclude=None, group=False, delete_empty=False):
        # Variables
        self.source = Path(source)
        self.group = group

        # Set destination folder
        if destination is None:
            self.destination = self.source.parent / f"{self.source.stem}_sorted"
        else:
            self.destination = Path(destination)

        # Create exclude filter
        self.exclude = []
        if isinstance(exclude, list):
            self.exclude.extend(exclude)
        elif isinstance(exclude, str):
            self.exclude.append(exclude)

        # Get file list
        self.filelist = FileList(self.source, exclude=self.exclude)

    def organize(self, mode="move"):
        """Organize files"""
        for n, source in self.filelist.files.items():
            destination = File(self.destination / source.group / source.myear / source.path.name)

            # Create destination folder
            destination.path.parent.mkdir(parents=True, exist_ok=True)

            # Move or copy file
            if not destination.path.is_file():
                if mode == "move":
                    move(source, destination)
                elif mode == "copy":
                    copy(source, destination)
            logging.info(f"{source.path} -> {destination.path}")


class File:
    def __init__(self, path):
        self.path = Path(path)

    @property
    def exists(self):
        return self.path.exists()

    @property
    def mtime(self):
        return self.path.stat().st_mtime

    @property
    def myear(self):
        return str(datetime.fromtimestamp(self.mtime).year)

    @property
    def checksum(self):
        return get_checksum(self.path)

    @property
    def group(self):
        suffix = self.path.suffix.strip(".")
        for k, v in GROUPS.items():
            if suffix in v:
                return k
        return suffix.strip(".")


class FileList:
    def __init__(self, path, exclude=None):
        self.path = Path(path)
        self.files = None

        self.exclude = []
        if isinstance(exclude, list):
            self.exclude.extend(exclude)
        elif isinstance(exclude, str):
            self.exclude.append(exclude)

        # Update file list
        self.update()

    def update(self):
        self.update_files()

    def update_files(self):
        """Get list of files in a folder and its subfolders"""
        # Get file list
        files = [x for x in self.path.rglob("*") if x.is_file()]
        logging.info(f"A total of {len(files)} files found")
        logging.info("Getting file information and filtering files")
        # Remove exlude files and create File objects
        self.files = {n: File(x) for n, x in enumerate(files) if x.name not in self.exclude}
        logging.info(f"{len(files) - len(self.files)} files filtered out")
        return self.files


def get_checksum(path: Path):
    """Return the checksum for a file"""
    h = HASHER
    return h(path.read_bytes()).hexdigest()


def move(source: File, destination: File, verify=True):
    destination.path.write_bytes(source.path.read_bytes())
    if verify:
        if source.checksum == destination.checksum:
            source.path.unlink()
            return True
        else:
            logging.error(f'{source.path.name} failed')
            return False
    return True


def copy(source: File, destination: File, verify=True):
    destination.path.write_bytes(source.path.read_bytes())
    if verify:
        if source.checksum == destination.checksum:
            return True
        else:
            logging.error(f'{source.path.filename} failed')
            return False
    return True


def cli():
    """Command line interface"""
    # Create the parser
    parser = argparse.ArgumentParser(description="Organize files")

    # Add the arguments
    parser.add_argument("source",
                        type=str,
                        help="The source folder")

    parser.add_argument("-d", "--destination",
                        type=str,
                        help="The destination folder",
                        action="store")

    parser.add_argument("-e", "--exclude",
                        help="List of files to exclude",
                        action="store")

    parser.add_argument("-g", "--group",
                        help="List of files to exclude",
                        action="store_true")

    parser.add_argument("--dryrun",
                        help="Run the script without actually changing any files",
                        action="store_true")

    # Execute the parse_args() method
    args = parser.parse_args()

    # Run offloader
    organizer = Organizer(source=args.source,
                          destination=args.destination,
                          exclude=args.exclude,
                          group=args.group)

    organizer.organize(mode="move")


if __name__ == '__main__':
    cli()
