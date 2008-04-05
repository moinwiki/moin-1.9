    # TODO: needs to get fixed for 1.7 auth objects

    smb_server = "smb.example.org" # smb server name
    smb_domain = 'DOMAIN' # smb domain name
    smb_share = 'FILESHARE' # smb share we mount
    smb_mountpoint = u'/mnt/wiki/%(username)s' # where we mount the smb filesystem
    smb_display_prefix = u"S:" # where //server/share is usually mounted for your windows users (display purposes only)
    smb_dir_user = "wwwrun" # owner of the mounted directories
    smb_dir_mode = "0700" # mode of the mounted directories
    smb_file_mode = "0600" # mode of the mounted files
    smb_iocharset = "iso8859-1" # "UTF-8" > cannot access needed shared library!
    smb_coding = 'iso8859-1' # coding used for encoding the commandline for the mount command
    smb_verbose = True # if True, put SMB debug info into log
    smb_log = "/dev/null" # where we redirect mount command output to

