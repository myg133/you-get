#!/usr/bin/env python

import getopt
import os
import platform
import sys
from .version import script_name, __version__
from .util import git, log

_options = [
    'help',
    'version',
    'gui',
    'force',
    'playlists',
]
_short_options = 'hVgfl'

_help = """Usage: {} [OPTION]... [URL]...
TODO
""".format(script_name)

def main(**kwargs):
    """Main entry point.
    you-get (legacy)
    """
    from .common import main
    main(**kwargs)

if __name__ == '__main__':
    main()
