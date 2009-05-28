# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Launchpad Teams Extension for OpenID authorization

    @copyright: 2009 Canonical, Inc.
    @license: GNU GPL, see COPYING for details.
"""
import re
import logging
import copy

#from MoinMoin.util.moinoid import MoinOpenIDStore
from MoinMoin import user
from MoinMoin.auth import BaseAuth
from MoinMoin.auth.openidrp import OpenIDAuth
#OpenIDSREGAuth
#from openid.consumer import consumer
#from openid.yadis.discover import DiscoveryFailure
#from openid.fetchers import HTTPFetchingError
#from MoinMoin.widget import html
#from MoinMoin.auth import CancelLogin, ContinueLogin
#from MoinMoin.auth import MultistageFormLogin, MultistageRedirectLogin
#from MoinMoin.auth import get_multistage_continuation_url

from openid.extensions.teams import TeamsRequest, TeamsResponse, supportsTeams
from MoinMoin import wikiutil
from MoinMoin.PageEditor import PageEditor, conflict_markers
from MoinMoin.Page import Page

def openidrp_teams_modify_request(oidreq, cfg):
    # Request Launchpad teams information, if configured
    # should also check supportsTeams() result
    #if teams_extension_avail and len(cfg.openidrp_authorized_teams) > 0:
    if len(cfg.openidrp_authorized_teams) > 0:
        oidreq.addExtension(TeamsRequest(cfg.openidrp_authorized_teams))

def openidrp_teams_create_user(info, u, cfg):
    # Check for Launchpad teams data in response
    teams = None
    #if teams_extension_avail and len(cfg.openidrp_authorized_teams) > 0:
    teams_response = TeamsResponse.fromSuccessResponse(info)
    teams = teams_response.is_member
    if teams:
        _save_teams_acl(u, teams, cfg)
    return u

def openidrp_teams_update_user(info, u, cfg):
    teams = None
    teams_response = TeamsResponse.fromSuccessResponse(info)
    teams = teams_response.is_member
    if teams:
        _save_teams_acl(u, teams, cfg)

# Take a list of Launchpad teams and add the user to the ACL pages
# ACL group names cannot have "-" in them, although team names do.
def _save_teams_acl(u, teams, cfg):
    logging.log(logging.INFO, "running save_teams_acl...")

    # remove any teams the user is no longer in
    if not hasattr(u, 'teams'):
        u.teams = []
    logging.log(logging.INFO, "old teams: " + str(u.teams)
        + "  new teams: " + str(teams))

    for t in u.teams:
        if not t in teams:
            logging.log(logging.INFO, "remove user from team: " + t)
            team = t.strip().replace("-", "")
            _remove_user_from_team(u, team, cfg)

    for t in teams:
        team = t.strip().replace("-", "")
        if not team:
            continue
        logging.log(logging.INFO, "Launchpad team: "  + team)
        _add_user_to_team(u, team, cfg)

    u.teams = teams
    u.save()

def _add_user_to_team(u, team, cfg):
    # use admin account to create or edit ACL page
    # http://moinmo.in/MoinDev/CommonTasks
    acl_request = u._request
    acl_request.user = user.User(acl_request, None, cfg.openidrp_acl_admin)
    pe = PageEditor(acl_request, team + cfg.openidrp_acl_page_postfix)
    acl_text = pe.get_raw_body()
    logging.log(logging.INFO, "ACL Page content: " + acl_text)
    # make sure acl command is first line of document
    # only the admin user specified in wikiconfig should
    # be allowed to change these acl files
    if not acl_text or acl_text == "" or acl_text[0] != "#":
        acl_text = "#acl Known:read All:\n" + acl_text
    # does ACL want uid, name, username, auth_username?
    p = re.compile(ur"^ \* %s" % u.name, re.MULTILINE)
    if not p.search(acl_text):
        logging.log(logging.INFO, "did not find user %s in acl, adding..." % u.name)
        acl_text += u" * %s\n" % u.name
        pe.saveText(acl_text, 0)

def _remove_user_from_team(u, team, cfg):
    acl_request = u._request
    acl_request.user = user.User(acl_request, None, cfg.openidrp_acl_admin)
    pe = PageEditor(acl_request, team + cfg.openidrp_acl_page_postfix)
    acl_text = pe.get_raw_body()
    logging.log(logging.INFO, "ACL Page content: " + acl_text)
    # does ACL want uid, name, username, auth_username?
    p = re.compile(ur"^ \* %s" % u.name, re.MULTILINE)
    if p.search(acl_text):
        logging.log(logging.INFO, "found user %s in acl, removing..." % u.name)
        acl_text = acl_text.replace(" * %s\n" % u.name, "")
        try:
            pe.saveText(acl_text, 0)
        except PageEditor.EmptyPage:
            pe.deletePage()

