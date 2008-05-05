# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - some common code for testing

    @copyright: 2007 MoinMoin:KarolNowak,
                2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, shutil

from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin import caching, user
# Promoting the test user -------------------------------------------
# Usually the tests run as anonymous user, but for some stuff, you
# need more privs...

def become_valid(request, username=u"ValidUser"):
    """ modify request.user to make the user valid.
        Note that a valid user will only be in ACL special group "Known", if
        we have a user profile for this user as the ACL system will check if
        there is a userid for this username.
        Thus, for testing purposes (e.g. if you need delete rights), it is
        easier to use become_trusted().
    """
    request.user.name = username
    request.user.may.name = username
    request.user.valid = 1


def become_trusted(request, username=u"TrustedUser"):
    """ modify request.user to make the user valid and trusted, so it is in acl group Trusted """
    become_valid(request, username)
    request.user.auth_method = request.cfg.auth_methods_trusted[0]


def become_superuser(request):
    """ modify request.user so it is in the superuser list,
        also make the user valid (see notes in become_valid()),
        also make the user trusted (and thus in "Trusted" ACL pseudo group).

        Note: being superuser is completely unrelated to ACL rights,
              especially it is not related to ACL admin rights.
    """
    su_name = u"SuperUser"
    become_trusted(request, su_name)
    if su_name not in request.cfg.superuser:
        request.cfg.superuser.append(su_name)


# Creating and destroying test pages --------------------------------

def create_page(request, pagename, content, do_editor_backup=False):
    """ create a page with some content """
    # make sure there is nothing already there:
    nuke_page(request, pagename)
    # now create from scratch:
    page = PageEditor(request, pagename, do_editor_backup=do_editor_backup)
    page.saveText(content, 0)
    return page

def append_page(request, pagename, content, do_editor_backup=False):
    """ appends some conetent to an existing page """
    # reads the raw text of the existing page
    raw = Page(request, pagename).get_raw_body()
    # adds the new content to the old
    content = "%s\n%s\n"% (raw, content)
    page = PageEditor(request, pagename, do_editor_backup=do_editor_backup)
    page.saveText(content, 0)
    return page

def nuke_page(request, pagename):
    """ completely delete a page, everything in the pagedir """
    page = PageEditor(request, pagename, do_editor_backup=False)
    page.deletePage()
    # really get rid of everything there:
    fpath = page.getPagePath(check_create=0)
    shutil.rmtree(fpath, True)

def nuke_user(request, username):
    """ completely delete a user """
    user_dir = request.cfg.user_dir
    user_id = user.getUserId(request, username)
    # really get rid of the user
    fpath = os.path.join(user_dir, user_id)
    os.remove(fpath)
    # delete cache
    arena = 'user'
    key = 'name2id'
    caching.CacheEntry(request, arena, key, scope='wiki').remove()
