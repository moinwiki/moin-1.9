"""
Execute a shell command with timeout.

@copyright: 2016 Thomas Waldmann <tw@waldmann-edv.de>
@license: GNU GPL, see COPYING for details.
"""

import os
import signal
import subprocess
from threading import Timer


def exec_cmd(cmd, stdin=None, timeout=None):
    """
    Execute a shell <cmd>, send <stdin> to it, kill it after <timeout> if it
    is still running. Return stdout, stderr, rc.
    """
    def preexec_fn():
        if not subprocess.mswindows:
            os.setsid()  # start a new session

    def kill_it(p):
        if not subprocess.mswindows:
            # kills all the processes of the session,
            # includes the shell + process started by shell
            os.killpg(p.pid, signal.SIGKILL)
        else:
            p.kill()

    p = subprocess.Popen(cmd, shell=True,
                         close_fds=not subprocess.mswindows,
                         bufsize=1024,
                         preexec_fn=preexec_fn,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if timeout is None:
        stdout, stderr = p.communicate(stdin)
    else:
        timer = Timer(timeout, kill_it, [p, ])
        try:
            timer.start()
            stdout, stderr = p.communicate(stdin)
        finally:
            timer.cancel()
    return stdout, stderr, p.returncode


if __name__ == '__main__':
    # expected output:
    # ('', '', -9)               --> no stdout, stderr output, killed by SIGKILL (signal 9)
    # ('20s gone\n', '', 0)      --> some output on stdout, no stderr, rc = 0 (did not get killed)
    print exec_cmd("python", "import time ; time.sleep(20) ; print 'timeout does not work!' ;", timeout=10)
    print exec_cmd("python", "import time ; time.sleep(20) ; print '20s gone' ;")
