# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - botbouncer.com verifier for OpenID login

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import user
from MoinMoin.auth import BaseAuth, CancelLogin, ContinueLogin, MultistageRedirectLogin
from urllib import urlopen, quote_plus

class BotBouncer(BaseAuth):
    name = 'botbouncer'

    def __init__(self, apikey):
        BaseAuth.__init__(self)
        self.apikey = apikey

    def login(self, request, user_obj, **kw):
        if kw.get('multistage'):
            uid = request.session.get('botbouncer.uid', None)
            if not uid:
                return CancelLogin(None)
            openid = request.session['botbouncer.id']
            del request.session['botbouncer.id']
            del request.session['botbouncer.uid']
            user_obj = user.User(request, uid, auth_method='openid',
                                 auth_username=openid)

        if not user_obj or not user_obj.valid:
            return ContinueLogin(user_obj)

        if user_obj.auth_method != 'openid':
            return ContinueLogin(user_obj)

        openid_id = user_obj.auth_username

        _ = request.getText

        try:
            url = "http://botbouncer.com/api/info?openid=%s&api_key=%s" % (
                           quote_plus(openid_id), self.apikey)
            data = urlopen(url).read().strip()
        except IOError:
            return CancelLogin(_('Could not contact botbouncer.com.'))

        data = data.split(':')
        if len(data) != 2 or data[0] != 'verified':
            return CancelLogin('botbouncer.com verification failed, probably invalid API key.')

        if data[1].lower() == 'true':
            # they proved they are human already
            return ContinueLogin(user_obj)

        # tell them to verify at bot bouncer first
        request.session['botbouncer.id'] = openid_id
        request.session['botbouncer.uid'] = user_obj.id

        goto = "http://botbouncer.com/captcha/queryuser?return_to=%%return_form&openid=%s" % (
            quote_plus(request.session['botbouncer.id']))
        return MultistageRedirectLogin(goto)
