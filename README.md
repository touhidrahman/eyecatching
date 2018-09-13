# eyecatching
Python CLI tool to compare webapp frontend using Perceptual Image Hashing

## Prerequisite
* Linux OS (tested in Ubuntu, should work in other distro)
* Firefox
* Chrome

## Installation and Setup

Only for first time:

`sudo pip install virtualenv` or `sudo easy_install virtualenv` or `sudo apt install python-virtualenv`

`cd eyecatching`

`virtualenv venv`

`. venv/bin/activate`

`pip install --editable .`

`eyecatching firstrun`

## Run eyecatching

Activate virtual environment:

`cd eyecatching`

`. venv/bin/activate`

List of commands you can use:

`eyecatching --help`

You can see help for subcommands using:

`eyecatching [subcommand] --help`

## Example:
Run comparison test using *linear* approach:
`eyecatching linear http://www.example.com`

Run comparison test using *recursive* approach:
`eyecatching recursive http://www.example.com`

Check shifts of objects inside images (alpha):
`eyecatching shift image1.png image2.png`

Compare two images without taking screenshot:
`eyecatching compare linear image1.png image2.png`
`eyecatching compare recursive image1.png image2.png`

Get screenshot for a URL (at present only chrome and firefox):
`eyecatching screenshot http://example.com`

Remove old input/output files:
`eyecatching reset`