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

## Run eyecatching

Activate virtual environment:

`cd eyecatching`

`. venv/bin/activate`

`eyecatching http://www.example.com`