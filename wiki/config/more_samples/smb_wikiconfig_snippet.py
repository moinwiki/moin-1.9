    # This is a sample configuration snippet that shows how to use the smb
    # mount plugin. SMBMount is only useful for very special applications
    # (and requires more code to be useful).
    # If you don't understand it, you don't need it.

    from MoinMoin.auth.smb_mount import SMBMount

    smbmounter = SMBMount(
        # you may remove default values if you are happy with them
        # see man mount.cifs for details
        server='smb.example.org', # (no default) mount.cifs //server/share
        share='FILESHARE', # (no default) mount.cifs //server/share
        mountpoint_fn=lambda username: u'/mnt/wiki/%s' % username, # (no default) function of username to determine the mountpoint
        dir_user='www-data', # (no default) username to get the uid that is used for mount.cifs -o uid=...
        domain='DOMAIN', # (no default) mount.cifs -o domain=...
        dir_mode='0700', # (default) mount.cifs -o dir_mode=...
        file_mode='0600', # (default) mount.cifs -o file_mode=...
        iocharset='utf-8', # (default) mount.cifs -o iocharset=... (try 'iso8859-1' if default does not work)
        coding='utf-8', # (default) encoding used for username/password/cmdline (try 'iso8859-1' if default does not work)
        log='/dev/null', # (default) logfile for mount.cifs output
    )

    auth = [....., smbmounter] # you need a real auth object in the list before smbmounter

    smb_display_prefix = u"S:" # where //server/share is usually mounted for your windows users (display purposes only)

