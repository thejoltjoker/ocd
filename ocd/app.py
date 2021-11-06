#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
app.py
Organize files based on type etc.
"""
import argparse
import logging
import hashlib
import json
import shutil
import string
import random
from ocd import INVALID_CHARACTERS, DEFAULT_RULES, LOGGING_CONFIG, OPERATIONS, TARGETS
from logging.config import dictConfig
from pathlib import Path

try:
    import xxhash
except ImportError:
    xxhash = None

# Setup logging
dictConfig(LOGGING_CONFIG)
logger = logging.getLogger()


def replace_characters(input_string: str, rules=None):
    """Replace characters based on table"""
    # Get rules
    if not rules:
        rules = get_rules()
    char_table = rules.get('characters', {})

    output_string = input_string

    for k, v in char_table.items():
        output_string = output_string.replace(k, v)
        output_string = output_string.replace(k.upper(), v.upper())
    return output_string


def remove_characters(input_string: str):
    """Remove illegal characters"""
    return ''.join(c for c in input_string if c not in INVALID_CHARACTERS)


def clean_string(input_string):
    """Fix a filename"""
    # Try and replace illegal characters
    output_string = replace_characters(input_string)

    # Remove remaining illegal characters
    output_string = remove_characters(output_string)

    return output_string


# def rename(root, name):
#     """Rename a file or a folder with correct characters"""
#     inc = 1
#     converted_name = clean_string(name)
#     old_path = os.path.join(root, name)
#     new_path = os.path.join(root, converted_name)
#
#     while True:
#         if old_path != new_path and os.path.exists(new_path):
#             print(f'{os.path.basename(new_path)} exists, incrementing')
#             new_name = f'{os.path.splitext(converted_name)[0]}_{inc:03d}{os.path.splitext(converted_name)[-1]}'
#             new_path = os.path.join(root, new_name)
#             inc += 1
#         else:
#             # os.rename(old_path, new_path)
#             break
#
#     return old_path, new_path


def run_jobs(rules=None):
    """Get jobs from rules

    Args:
        rules: dict with rules

    Returns:
        list: list of dicts with job info
    """
    # Get rules
    if not rules:
        rules = get_rules()
    jobs = get_jobs(rules)

    for job in jobs:
        run_job(**job)


def get_job_attributes(job):
    # Check if the job has the necessary parameters and set defaults
    # Name is required
    if not job.get('name'):
        return None

    # Check path
    if not job.get('source'):
        logging.warning(f'No path given')
        return None
    else:
        source_path = Path(job.get('source'))
        if not source_path.exists():
            logging.warning(f'Source path {source_path} does not exist')
            return None
        job['source'] = source_path

    # Check destination path
    job['destination'] = Path(job.get('destination', job.get('source')))

    # Check operation
    if not job.get('operation'):
        job['operation'] = 'move'
    elif job.get('operation') not in OPERATIONS:
        logging.warning(f'Operation {job.get("operation")} not recognized')
        return None

    # Check target
    if not job.get('target'):
        job['target'] = 'both'
    elif job.get('target') not in TARGETS:
        logging.warning(f'Target {job.get("target")} not recognized')
        return None

    # Check subdirs
    if not job.get('subdirs'):
        job['subdirs'] = False

    # Check grouping settings
    if not job.get('group'):
        job['group'] = True

    # Check filename settings
    if not job.get('filename'):
        job['filename'] = True

    # Check verification settings
    if not job.get('verify'):
        job['verify'] = False

    # Check cleanup settings
    if not job.get('cleanup'):
        job['cleanup'] = True

    return job


def folders_paths(paths):
    """Return a list of only folders from a list of paths"""
    folders = [x for x in paths if x.is_dir()]
    return folders


def files_paths(paths):
    """Return a list of only files from a list of paths"""
    files = [x for x in paths if x.is_file()]
    return files


def run_job(**job):
    # Get attributes and check if the job is valid
    job = get_job_attributes(job)
    if not job:
        logging.info(f'Job failed: {job.get("name")}')
        return None

    logging.info(f'Running job: {job["name"]}')

    # Setup paths
    job_source = job['source']
    job_dest = job['destination']
    paths = get_paths(job['source'], pattern=job['pattern'], subdirs=job['subdirs'])
    files = files_paths(paths)
    folders = folders_paths(paths)
    if job['target'] == 'files' or job['target'] == 'both':
        organize_files(job, files)
    if job['target'] == 'folders' or job['target'] == 'both':
        organize_folders(job, folders)


def job_prefix(job):
    prefixes = {
        'copy': 'cp',
        'move': 'mv',
        'delete': 'del',
        'dryrun': 'dry'
    }
    p = prefixes.get(job["operation"], job["operation"][0:1])
    return f'[{job["name"]} @ {p.upper()}]'


def organize_files(job, files):
    for n, f in enumerate(files):
        prefix = job_prefix(job)
        logging.info(f'{prefix} Processing {n + 1} of {len(files)} files')

        # Setup file dicts
        source_file = {'path': f}
        destination_file = {'path': job['destination']}

        # Get group
        if job['group']:
            group = group_from_path(f)
            if group:
                destination_file['path'] = destination_file['path'] / group

        # Clean filename
        if job['filename']:
            filename = clean_string(f.name)
            destination_file['path'] = destination_file['path'] / filename
        else:
            destination_file['path'] = destination_file['path'] / source_file['path'].name

        # Perform operation
        if job['operation'] == 'dryrun':
            logging.info(f'{prefix} {source_file["path"]} -> {destination_file["path"]}')
        elif job['operation'] == 'copy':
            logging.info(f'{prefix} {source_file["path"]} -> {destination_file["path"]}')
            copy(source_file['path'], destination_file['path'], job['verify'])
        elif job['operation'] == 'move':
            logging.info(f'{prefix} {source_file["path"]} -> {destination_file["path"]}')
            move(source_file['path'], destination_file['path'], job['verify'])
        elif job['operation'] == 'delete':
            logging.info(f'{prefix} {source_file["path"]} -> 🗑')


def organize_folders(job, folders):
    for n, f in enumerate(folders):
        prefix = job_prefix(job)
        logging.info(f'{prefix} Processing {n + 1} of {len(folders)} folders')

        # Setup file dicts
        source_folder = {'path': f}
        destination_folder = {'path': job['destination']}

        # Clean foldername
        if job['filename']:
            foldername = clean_string(f.name)
            destination_folder['path'] = destination_folder['path'] / foldername
        else:
            destination_folder['path'] = destination_folder['path'] / source_folder['path'].name

        # Perform operation
        if job['cleanup']:
            if is_empty_dir(source_folder['path']):
                logging.info(f'{prefix} {source_folder["path"]} -> 🗑')

        if job['operation'] == 'delete':
            logging.info(f'{prefix} {source_folder["path"]} -> 🗑')
            delete(source_folder['path'])
        elif job['operation'] == 'copy':
            logging.info(f'{prefix} {source_folder["path"]} -> {destination_folder["path"]}')
            copy(source_folder['path'], destination_folder['path'])
        elif job['operation'] == 'move':
            logging.info(f'{prefix} {source_folder["path"]} -> {destination_folder["path"]}')
            move(source_folder['path'], destination_folder['path'])
        elif job['operation'] == 'dryrun':
            logging.info(f'{prefix} {source_folder["path"]} -> 🗑')


def is_empty_dir(path: Path):
    if path.iterdir():
        return False
    return True


def group_from_path(path: Path):
    # Returns a file type group from the given path
    extensions = get_extensions()
    if path.suffix:
        return extensions.get(path.suffix.lower().lstrip('.'), 'other')
    logging.debug(f'{path} suffix is "{path.suffix}"')
    return None


#
#
# File operations
#
def get_paths(path: Path, pattern='*', subdirs=False):
    """Get all files in a directory and/or its subdirectories,
    based ona given pattern.

    Args:
        path: root path to scan
        pattern: the filename pattern
        subdirs: whether to search in subdirectories or not

    Returns:
        list: list of Path objects
    """
    if subdirs:
        pattern = f'**/{pattern}'

    return [x for x in path.glob(pattern)]


def verify_checksums(path_a, path_b):
    """Compare the checksum of two files"""
    hash_a = get_checksum(path_a)
    hash_b = get_checksum(path_b)
    if hash_a == hash_b:
        return True
    return False


def get_checksum(path: Path):
    """Return the checksum for a file"""
    if xxhash:
        h = xxhash.xxh3_64()
    else:
        logging.info('xxhash not available. Try "pip install xxhash"')
        h = hashlib.md5()

    # Load file in chunks
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(16384), b""):
            h.update(chunk)

    return h.hexdigest()


def copy(source: Path, destination: Path, verify=False):
    # TODO: Check if destination file exists
    if destination.exists():
        return False
    shutil.copy2(source, destination)
    if verify:
        if verify_checksums(source, destination):
            logging.debug(f'{source} -> {destination} | Successful, verified')
            return True
        else:
            logging.warning(f'{source} -> {destination} | Failed, mismatching checksums')
            return False

    # Check if destination exists and return True
    if destination.exists():
        logging.debug(f'{source} -> {destination} | Successful')
        return True
    logging.warning(f'{source} -> {destination} | Failed')
    return False


def move(source: Path, destination: Path, verify=False):
    # TODO: Check if destination file exists
    if destination.exists():
        return False
    # Create destination dir
    destination.parent.mkdir(parents=True, exist_ok=True)

    # Copy file
    shutil.copy2(source, destination)
    if verify:
        if verify_checksums(source, destination):
            logging.debug(f'{source} -> {destination} | Successful, verified')
            delete(source)
            return True
        else:
            logging.warning(f'{source} -> {destination} | Failed, mismatching checksums')
            return False

    # Check if destination exists and return True
    if destination.exists():
        logging.debug(f'{source} -> {destination} | Successful')
        delete(source)
        return True
    logging.warning(f'{source} -> {destination} | Failed')
    return False


def delete(path: Path):
    if path.is_file():
        path.unlink()
    else:
        path.rmdir()


# def delete_empty_folders(path):
#     path = Path(path)
#     folders = [x for x in path.rglob('*') if x.is_dir()]
#     for f in folders:
#         if len(list(f.iterdir())) == 0:
#             f.rmdir()
#
#
# def delete_node_modules(path):
#     path = Path(path)
#     # for root, dirs, files in os.walk("dir"):
#     #     print(root, dirs, files)
#     folders = [x for x in path.rglob('*') if x.is_dir()]
#     for f in folders:
#         if 'node_modules' in f.name:
#             print(f.resolve())
#
#
# def list_files_dirs(path, pattern='*', subdirs=False):
#     """List all files and folders
#
#     Args:
#         path: path to the root to search
#         pattern: file search pattern
#         subdirs: whether or not to search subdirectories
#
#     Returns:
#         list: list of files and folders
#     """
#     path = Path(path)
#     if subdirs:
#         return [x for x in path.rglob(pattern)]
#     return [x for x in path.iterdir() if pattern in x]


#
#
# Rules
#
def add_characters_to_rules(rules_path=None, **characters):
    """Get rules from rules.json"""
    path = get_rules_path(rules_path)

    if not path.is_file():
        logging.error(f'Creating rules file in {path.parent}')
        return None

    # Load rules from file
    with path.open('r') as f:
        rules = json.load(f)

    # Append new rules
    for k, v in characters.items():
        logging.debug(f'Adding "{k} = {v}" to rules')
        if not rules.get('characters'):
            rules['characters'] = {}
        rules['characters'][k] = [v]

    _write_rules(path, rules)


def init_rules(path: Path):
    """Initialize a rules file with default rules

    Args:
        path: path to store the file
    """
    # Get default rules
    default = DEFAULT_RULES

    # Check if given rules path exists, otherwise load defaults
    if path.is_file():
        rules = _load_rules(path)

        # Add default values if the keys don't exist
        for k in default.keys():
            if not rules.get(k):
                rules[k] = default[k]
    else:
        rules = default

    # Create parent folder if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write rules to file
    _write_rules(path, rules)

    return rules


def get_rules_path(path=None):
    if path:
        path = Path(path)
    else:
        path = Path(__file__).parent / 'rules.json'
    return path


def _write_rules(path, rules):
    # Write to file
    with path.open('w', encoding='utf8') as json_file:
        json.dump(rules, json_file, ensure_ascii=False)


def _load_rules(path: Path):
    # Read from file
    with path.open('r') as json_file:
        return json.load(json_file)


def set_rules(rules_path=None, jobs=None, groups=None, characters=None):
    """Get rules from rules.json"""
    if characters is None:
        characters = {}
    if groups is None:
        groups = {}
    if jobs is None:
        jobs = []

    if rules_path:
        path = Path(rules_path)
    else:
        path = Path(__file__).parent / 'rules.json'

    if not path.is_file():
        logging.error(f'Creating rules file in {path.parent}')
        path.write_text('{}')

    with path.open('r') as f:
        old_rules = json.load(f)


def get_rules(rules_path=None):
    """Get rules from rules.json"""
    path = get_rules_path(rules_path)

    if not path.is_file():
        logging.info(f'Creating rules file in {path.parent}')
        init_rules(path)

    return _load_rules(path)


def get_jobs(rules=None):
    """Get jobs from rules

    Args:
        rules: dict with rules

    Returns:
        list: list of dicts with job info
    """
    if not rules:
        rules = get_rules()

    return rules.get('jobs', [])


def get_groups(rules=None):
    """Get groups from rules

        Args:
            rules: dict with rules

        Returns:
            dict: groups and filetypes
        """
    # Get rules
    if not rules:
        rules = get_rules()

    return rules.get('groups', {})


def get_extensions(rules=None):
    """Get groups from rules

        Args:
            rules: dict with rules

        Returns:
            dict: groups and filetypes
        """
    # Get rules
    if not rules:
        rules = get_rules()

    # Convert group rules to dict that's easier to parse
    output = {}
    for group, extensions in rules.get('groups', {}).items():
        for ext in extensions:
            output[ext] = group

    return output


def generate_string(length=5):
    letters = []
    for i in range(length):
        l = string.ascii_letters[random.randint(0, len(string.ascii_letters) - 1)]
        letters.append(l)
    return ''.join(letters)


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

    parser.add_argument("-g", "--group",
                        help="Group files by type",
                        action="store_true")

    parser.add_argument("--group-prefix",
                        dest='gprefix',
                        help="Add prefix to group folder",
                        action="store")

    parser.add_argument("--dryrun",
                        help="Run the script without actually changing any files",
                        action="store_true")

    # Execute the parse_args() method
    args = parser.parse_args()

    # Run offloader
    # organizer = Organizer(source=args.source,
    #                       destination=args.destination,
    #                       group=args.group,
    #                       group_prefix=args.gprefix)
    #
    # organizer.organize(mode="move")


if __name__ == '__main__':
    # cli()
    run_jobs()
