# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Simple Registration Extension for OpenID authorization

    @copyright: 2009 Canonical, Inc.
    @license: GNU GPL, see COPYING for details.
"""
#from MoinMoin.util.moinoid import MoinOpenIDStore
from MoinMoin import user
from MoinMoin.auth import BaseAuth
from MoinMoin.auth.openidrp import OpenIDAuth
#from openid.consumer import consumer
#from openid.yadis.discover import DiscoveryFailure
#from openid.fetchers import HTTPFetchingError
#from MoinMoin.widget import html
#from MoinMoin.auth import CancelLogin, ContinueLogin
#from MoinMoin.auth import MultistageFormLogin, MultistageRedirectLogin
#from MoinMoin.auth import get_multistage_continuation_url

from openid.extensions.sreg import *
from MoinMoin import i18n
from datetime import datetime, timedelta
from pytz import timezone
import pytz

OpenIDAuth.auth_attribs = ('name', 'email', 'aliasname', 'language', 'tz_offset')

openidrp_sreg_required = ['nickname', 'email', 'timezone']
openidrp_sreg_optional = ['fullname', 'language']
openidrp_sreg_username_field = 'nickname'

def openidrp_sreg_modify_request(oidreq, cfg):
    oidreq.addExtension(SRegRequest(required=cfg.openidrp_sreg_required,
                                    optional=cfg.openidrp_sreg_optional))

def openidrp_sreg_create_user(info, u, cfg):
    sreg = _openidrp_sreg_extract_values(info)
    if sreg and sreg[cfg.openidrp_sreg_username_field] != '':
        u.name = sreg[cfg.openidrp_sreg_username_field]
    return u

def openidrp_sreg_update_user(info, u, cfg):
    sreg = _openidrp_sreg_extract_values(info)
    if sreg:
        u.name = sreg[cfg.openidrp_sreg_username_field]
        if sreg['email'] != '':
            u.email = sreg['email']
        if sreg['language'] != '':
            u.language = sreg['language']
        if sreg['timezone'] != '':
            u.tz_offset = sreg['timezone']
        if sreg['fullname'] != '':
            u.fullname = sreg['fullname']

def _openidrp_sreg_extract_values(info):
    # Pull SREG data here instead of asking user
    sreg_resp = SRegResponse.fromSuccessResponse(info)
    sreg = {'nickname': '', 'email': '', 'fullname': '',
            'dob': '0000-00-00', 'gender': '', 'postcode': '',
            'country': '', 'language': '', 'timezone': ''}
    if sreg_resp:
        if sreg_resp.get('nickname'):
            sreg['nickname'] = sreg_resp.get('nickname')
        if sreg_resp.get('fullname'):
            sreg['fullname'] = sreg_resp.get('fullname')
        if sreg_resp.get('email'):
            sreg['email'] = sreg_resp.get('email')
        # Language must be a valid value
        # check the MoinMoin list, or restrict to first 2 chars
        if sreg_resp.get('language'):
            # convert unknown codes to 2 char format
            langs = i18n.wikiLanguages().items()
            sreg['language'] = sreg_resp.get('language')
            lang_found = False
            for lang in langs:
                if lang[0] == sreg['language']:
                    lang_found = True
            if not lang_found:
                if langs[sreg['language'][0:2]]:
                    sreg['language'] = sreg['language'][0:2]
        # Timezone must be converted to offset in seconds
        if sreg_resp.get('timezone'):
            user_tz = timezone(sreg_resp.get('timezone').encode('ascii'))
            if user_tz:
                user_utcoffset = user_tz.utcoffset(datetime.utcnow())
                sreg['timezone'] = user_utcoffset.days * 24 * 60 * 60 + user_utcoffset.seconds
            else:
                sreg['timezone'] = 0
    return sreg

