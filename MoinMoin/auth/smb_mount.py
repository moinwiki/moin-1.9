# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - auth plugin for (un)mounting a smb share

    (u)mount a SMB server's share for username (using username/password for
    authentication at the SMB server). This can be used if you need access
    to files on some share via the wiki, but needs more code to be useful.

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""


def smb_mount(request, **kw):
    """ auth plugin for (un)mounting an smb share """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')
    cfg = request.cfg
    verbose = cfg.smb_verbose
    if verbose: request.log("got name=%s login=%r logout=%r" % (username, login, logout))

    # we just intercept login to mount and logout to umount the smb share
    if login or logout:
        import os, pwd, subprocess
        web_username = cfg.smb_dir_user
        web_uid = pwd.getpwnam(web_username)[2] # XXX better just use current uid?
        if logout and user_obj: # logout -> we don't have username in form
            username = user_obj.name # so we take it from previous auth method (moin_cookie e.g.)
        mountpoint = cfg.smb_mountpoint % {
            'username': username,
        }
        if login:
            cmd = u"sudo mount -t cifs -o user=%(user)s,domain=%(domain)s,uid=%(uid)d,dir_mode=%(dir_mode)s,file_mode=%(file_mode)s,iocharset=%(iocharset)s //%(server)s/%(share)s %(mountpoint)s >>%(log)s 2>&1"
        elif logout:
            cmd = u"sudo umount %(mountpoint)s >>%(log)s 2>&1"

        cmd = cmd % {
            'user': username,
            'uid': web_uid,
            'domain': cfg.smb_domain,
            'server': cfg.smb_server,
            'share': cfg.smb_share,
            'mountpoint': mountpoint,
            'dir_mode': cfg.smb_dir_mode,
            'file_mode': cfg.smb_file_mode,
            'iocharset': cfg.smb_iocharset,
            'log': cfg.smb_log,
        }
        env = os.environ.copy()
        if login:
            try:
                if not os.path.exists(mountpoint):
                    os.makedirs(mountpoint) # the dir containing the mountpoint must be writeable for us!
            except OSError:
                pass
            env['PASSWD'] = password.encode(cfg.smb_coding)
        subprocess.call(cmd.encode(cfg.smb_coding), env=env, shell=True)
    return user_obj, True

