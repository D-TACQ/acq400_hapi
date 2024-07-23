"""Determine the current version of the package"""

import subprocess

# must run from git repo top level (check if .git/ exists?)

def get_version():
    proc = subprocess.Popen(['git', 'describe', '--tags'], stdout=subprocess.PIPE)
    return proc.stdout.readline().decode().strip().replace('-', '+', 1)

