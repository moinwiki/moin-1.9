#!/usr/bin/env python

import os
from sys import argv

# Define the starting directory.

startdir = ""

if len(argv) == 2:
    startdir = os.path.join(argv[1])
else:
    startdir = os.path.join("..") # MoinMoin

# Define a blacklist.

blacklist = ["_tests",
             os.path.join("script", "old"),
             "support",
             os.path.join("filter", "EXIF.py"),
             os.path.join("web", "static", "htdocs"),
            ]

# Define an output file for the filenames.

outname_in = "POTFILES.in"
outname_final = "POTFILES"

# Functions.

def get_files((files, prefix, blacklist), d, names):

    """
    Store pathnames in 'files', removing 'prefix', excluding those mentioned
    in the 'blacklist', building such pathnames from the directory 'd' and
    the given 'names'.
    """

    for name in names:
        if name.endswith(".py"):
            path = os.path.join(d, name)

            # Strip the prefix.
            if path.startswith(prefix):
                path = path[len(prefix):]

            # Test for exact blacklist matches.
            if path in blacklist:
                continue

            # Test for directory blacklist matches.
            found = 0
            for blackitem in blacklist:
                if path.startswith(blackitem):
                    found = 1
                    break

            if not found:
                files.append(path)

def find_files(startdir, blacklist):
    "Find files under 'startdir' excluding those in the 'blacklist'."

    # Calculate the prefix from the start directory.
    prefix = os.path.join(startdir, "")

    # Start with an empty list of files.

    files = []
    os.path.walk(startdir, get_files, (files, prefix, blacklist))
    return files

if __name__ == "__main__":

    # Find those files using the module defaults.
    files = find_files(startdir, blacklist)

    # Write the names out.
    outfile = open(outname_in, "w")
    try:
        for file in files:
            outfile.write(file + "\n")
    finally:
        outfile.close()

    # Write the processed list out, ready for other purposes.
    outfile = open(outname_final, "w")
    outfile.write("POTFILES = \\\n")
    try:
        for file in files[:-1]:
            outfile.write("\t" + os.path.join(startdir, file) + " \\\n")
        if files[-1]:
            file = files[-1]
            outfile.write("\t" + os.path.join(startdir, file) + "\n")
    finally:
        outfile.close()

# vim: tabstop=4 expandtab shiftwidth=4
