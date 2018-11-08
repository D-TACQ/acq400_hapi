#!/usr/bin/python

from subprocess import call

call(['mate-terminal', '--window-with-profile=Default', '--title="pgmwashere"',
       '-e', 'sleep 100'])
