#!/bin/bash

# Example mail.py wrapper
# Set PYTHONPATH, umask and other stuff required by your mail view methods

PYTHONPATH="/opt/mailpy:/usr/local/envs/lib64/python2.7/site-packages"
export PYTHONPATH
VIRTUAL_ENV="/usr/local/envs"
export VIRTUAL_ENV

umask 022

/opt/mailpy/bin/mail.py "${@}"
