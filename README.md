# OCD

A command line tool for organizing and sorting files.

## Rules

### Jobs

Here are all the options that you can define in rules.json.

#### name*

_(*required, default: None )_

Name of the job.

#### source*

_(*required, default: None )_

Source path of the job

#### destination

_(default: source )_

Destination path

#### target

_(default: both )_

- files
- folders
- both

#### pattern

_(default: *)_

Search pattern for file operations.

#### operation

_(default: move )_

File operation to perform on files and folders matching the pattern.

- `copy`
    - Copy files
- `move`
    - Move files
- `dryrun`
    - Run a test without doing anything
- `delete`
    - Delete all things matching the pattern

#### subdirs

_(default: False)_

Search through subfolders

#### group

_(default: True)_

Group files into folders by type, otherwise suffix

#### rename

_(default: True)_

Remove illegal characters from filenames and replace characters from rules.json.

#### verify

_(default: False)_

Verify file transfers using checksum verification.

#### cleanup

_(default: True)_

Clean up empty folders and other unnecessary files.