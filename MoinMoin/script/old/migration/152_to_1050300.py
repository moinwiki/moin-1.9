#!/usr/bin/env python
"""
    Migration from moin 1.5.2 to moin 1.5.3

    We just make sure that there is a "meta" file in your data directory that
    stores the "revision" level of it (so future mig scripts can tell if they
    need to run or not [e.g. because you already have run them]).

    This is the last "old style" migration script.

    Steps for a successful migration:

        1. You do NOT need to stop your wiki for this mig script.

        2. Change directory to: .../MoinMoin/script/old/migration

        3. Run this script as a user who may write to the data_dir of your wiki
           and supply the pathes to the data_dir you want to migrate. If you
           have multiple wikis, you may specify multiple pathes on the command
           line:

           sudo -u www-data ./152_to_1050300.py /my/path/to/data

        4. That's it.
           Future mig scripts now can auto-detect the data_dir revision level.

    @copyright: 2006 Thomas Waldmann
    @license: GPL, see COPYING for details
"""
import sys, os

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../../../..')

def migrate(dirlist):
    errors = warnings = success = 0
    for dir in dirlist:
        if not (os.path.exists(os.path.join(dir, 'pages')) and
                os.path.exists(os.path.join(dir, 'user'))):
            print "Error: Skipping %s - does not look like a data_dir" % dir
            errors += 1
        else:
            fname = os.path.join(dir, 'meta')
            if os.path.exists(fname):
                print "Warning: There already is a meta file there, skipping %s" % dir
                warnings += 1
            else:
                try:
                    f = open(fname, 'w')
                    f.write("data_format_revision: 01050300\n") # 01050300 = 1.5.3(.0)
                    f.close()
                    success += 1
                except:
                    errors += 1
                    print "Error: Exception when migrating %s" % dir
    print "%d data_dirs successfully migrated, %d warnings, %d errors." % (success, warnings, errors)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        data_dirs = ['data', ]
    else:
        data_dirs = sys.argv[1:]
    migrate(data_dirs)

