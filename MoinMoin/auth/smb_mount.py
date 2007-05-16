# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - auth plugin for (un)mounting a smb share

    (u)mount a SMB server's share for username (using username/password for
    authentication at the SMB server). This can be used if you need access
    to files on some share via the wiki, but needs more code to be useful.

    @copyright: 2006 MoinMoin:ThomasWaldmann
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.auth import BaseAuth, CancelLogin, ContinueLogin

class SMBMount(BaseAuth):
    """ auth plugin for (un)mounting an smb share """
    def __init__(self, smb_dir_user, smb_mountpoint_fn, smb_domain, smb_server,
                 smb_share, smb_dir_mode, smb_file_mode, smb_iocharset,
                 smb_log, smb_coding, verbose=False):
        BaseAuth.__init__(self)
        self.verbose = verbose
        self.smb_dir_user = smb_dir_user
        self.smb_mountpoint_fn = smb_mountpoint_fn
        self.smb_domain = smb_domain
        self.smb_server = smb_server
        self.smb_share = smb_share
        self.smb_dir_mode = smb_dir_mode
        self.smb_file_mode = smb_file_mode
        self.smb_iocharset = smb_iocharset
        self.smb_log = smb_log
        self.smb_coding = smb_coding

    def do_smb(self, request, username, password, login):
        verbose = self.verbose
        if verbose: request.log("SMBMount login=%s logout=%s: got name=%s" % (login, not login, username))

        import os, pwd, subprocess
        web_username = self.smb_dir_user
        web_uid = pwd.getpwnam(web_username)[2] # XXX better just use current uid?

        if not login: # logout -> we don't have username in form
            username = user_obj.name # so we take it from previous auth method

        mountpoint = self.smb_mountpoint_fn(username)
        if login:
            cmd = u"sudo mount -t cifs -o user=%(user)s,domain=%(domain)s,uid=%(uid)d,dir_mode=%(dir_mode)s,file_mode=%(file_mode)s,iocharset=%(iocharset)s //%(server)s/%(share)s %(mountpoint)s >>%(log)s 2>&1"
        else:
            cmd = u"sudo umount %(mountpoint)s >>%(log)s 2>&1"

        cmd = cmd % {
            'user': username,
            'uid': web_uid,
            'domain': self.smb_domain,
            'server': self.smb_server,
            'share': self.smb_share,
            'mountpoint': mountpoint,
            'dir_mode': self.smb_dir_mode,
            'file_mode': self.smb_file_mode,
            'iocharset': self.smb_iocharset,
            'log': self.smb_log,
        }
        env = os.environ.copy()
        if login:
            try:
                if not os.path.exists(mountpoint):
                    os.makedirs(mountpoint) # the dir containing the mountpoint must be writeable for us!
            except OSError:
                pass
            env['PASSWD'] = password.encode(self.smb_coding)
        subprocess.call(cmd.encode(self.smb_coding), env=env, shell=True)

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')
        if user_obj and user_obj.valid:
            do_smb(request, username, password, True)
        return ContinueLogin(user_obj)

    def logout(self, request, user_obj, **kw):
        if user_obj and not user_obj.valid:
            do_smb(request, None, None, False)
        return user_obj, True
