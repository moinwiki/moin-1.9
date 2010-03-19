# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OpenID authorization

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.util.moinoid import MoinOpenIDStore
from MoinMoin import user
from MoinMoin.auth import BaseAuth
from openid.consumer import consumer
from openid.yadis.discover import DiscoveryFailure
from openid.fetchers import HTTPFetchingError
from MoinMoin.widget import html
from MoinMoin.auth import CancelLogin, ContinueLogin
from MoinMoin.auth import MultistageFormLogin, MultistageRedirectLogin
from MoinMoin.auth import get_multistage_continuation_url
from werkzeug import url_encode

class OpenIDAuth(BaseAuth):
    login_inputs = ['openid_identifier']
    name = 'openid'
    logout_possible = True
    auth_attribs = ()

    def __init__(self, modify_request=None,
                       update_user=None,
                       create_user=None,
                       forced_service=None,
                       idselector_com=None):
        BaseAuth.__init__(self)
        self._modify_request = modify_request or (lambda x, c: None)
        self._update_user = update_user or (lambda i, u, c: None)
        self._create_user = create_user or (lambda i, u, c: None)
        self._forced_service = forced_service
        self._idselector_com = idselector_com
        if forced_service:
            self.login_inputs = ['special_no_input']

    def _handle_user_data(self, request, u):
        create = not u
        if create:
            # pass in a created but unsaved user object
            u = user.User(request, auth_method=self.name,
                          auth_username=request.session['openid.id'],
                          auth_attribs=self.auth_attribs)
            # invalid name
            u.name = ''
            u = self._create_user(request.session['openid.info'], u, request.cfg)

        if u:
            self._update_user(request.session['openid.info'], u, request.cfg)

            # just in case the wiki admin screwed up
            if (not user.isValidName(request, u.name) or
                (create and user.getUserId(request, u.name))):
                return None

            if not hasattr(u, 'openids'):
                u.openids = []
            if not request.session['openid.id'] in u.openids:
                u.openids.append(request.session['openid.id'])

            u.save()

            del request.session['openid.id']
            del request.session['openid.info']

        return u

    def _get_account_name(self, request, form, msg=None):
        # now we need to ask the user for a new username
        # that they want to use on this wiki
        # XXX: request nickname from OP and suggest using it
        # (if it isn't in use yet)
        logging.debug("running _get_account_name")
        _ = request.getText
        form.append(html.INPUT(type='hidden', name='oidstage', value='2'))
        table = html.TABLE(border='0')
        form.append(table)
        td = html.TD(colspan=2)
        td.append(html.Raw(_("""Please choose an account name now.
If you choose an existing account name you will be asked for the
password and be able to associate the account with your OpenID.""")))
        table.append(html.TR().append(td))
        if msg:
            td = html.TD(colspan='2')
            td.append(html.P().append(html.STRONG().append(html.Raw(msg))))
            table.append(html.TR().append(td))
        td1 = html.TD()
        td1.append(html.STRONG().append(html.Raw(_('Name'))))
        td2 = html.TD()
        td2.append(html.INPUT(type='text', name='username'))
        table.append(html.TR().append(td1).append(td2))
        td1 = html.TD()
        td2 = html.TD()
        td2.append(html.INPUT(type='submit', name='submit',
                              value=_('Choose this name')))
        table.append(html.TR().append(td1).append(td2))

    def _get_account_name_inval_user(self, request, form):
        _ = request.getText
        msg = _('This is not a valid username, choose a different one.')
        return self._get_account_name(request, form, msg=msg)

    def _associate_account(self, request, form, accountname, msg=None):
        _ = request.getText

        form.append(html.INPUT(type='hidden', name='oidstage', value='3'))
        table = html.TABLE(border='0')
        form.append(table)
        td = html.TD(colspan=2)
        td.append(html.Raw(_("""The username you have chosen is already
taken. If it is your username, enter your password below to associate
the username with your OpenID. Otherwise, please choose a different
username and leave the password field blank.""")))
        table.append(html.TR().append(td))
        if msg:
            td.append(html.P().append(html.STRONG().append(html.Raw(msg))))
        td1 = html.TD()
        td1.append(html.STRONG().append(html.Raw(_('Name'))))
        td2 = html.TD()
        td2.append(html.INPUT(type='text', name='username', value=accountname))
        table.append(html.TR().append(td1).append(td2))
        td1 = html.TD()
        td1.append(html.STRONG().append(html.Raw(_('Password'))))
        td2 = html.TD()
        td2.append(html.INPUT(type='password', name='password'))
        table.append(html.TR().append(td1).append(td2))
        td1 = html.TD()
        td2 = html.TD()
        td2.append(html.INPUT(type='submit', name='submit',
                              value=_('Associate this name')))
        table.append(html.TR().append(td1).append(td2))

    def _handle_verify_continuation(self, request):
        _ = request.getText
        oidconsumer = consumer.Consumer(request.session,
                                        MoinOpenIDStore(request))
        query = {}
        for key in request.values.keys():
            query[key] = request.values.get(key)
        current_url = get_multistage_continuation_url(request, self.name,
                                                      {'oidstage': '1'})
        info = oidconsumer.complete(query, current_url)
        if info.status == consumer.FAILURE:
            logging.debug(_("OpenID error: %s.") % info.message)
            return CancelLogin(_('OpenID error: %s.') % info.message)
        elif info.status == consumer.CANCEL:
            logging.debug(_("OpenID verification canceled."))
            return CancelLogin(_('Verification canceled.'))
        elif info.status == consumer.SUCCESS:
            logging.debug(_("OpenID success. id: %s") % info.identity_url)
            request.session['openid.id'] = info.identity_url
            request.session['openid.info'] = info

            # try to find user object
            uid = user.getUserIdByOpenId(request, info.identity_url)
            if uid:
                u = user.User(request, id=uid, auth_method=self.name,
                              auth_username=info.identity_url,
                              auth_attribs=self.auth_attribs)
            else:
                u = None

            # create or update the user according to the registration data
            u = self._handle_user_data(request, u)
            if u:
                return ContinueLogin(u)

            # if no user found, then we need to ask for a username,
            # possibly associating an existing account.
            logging.debug("OpenID: No user found, prompting for username")
            #request.session['openid.id'] = info.identity_url
            return MultistageFormLogin(self._get_account_name)
        else:
            logging.debug(_("OpenID failure"))
            return CancelLogin(_('OpenID failure.'))

    def _handle_name_continuation(self, request):
        _ = request.getText
        if not 'openid.id' in request.session:
            return CancelLogin(_('No OpenID found in session.'))

        newname = request.form.get('username', '')
        if not newname:
            return MultistageFormLogin(self._get_account_name)
        if not user.isValidName(request, newname):
            return MultistageFormLogin(self._get_account_name_inval_user)
        uid = None
        if newname:
            uid = user.getUserId(request, newname)
        if not uid:
            # we can create a new user with this name :)
            u = user.User(request, auth_method=self.name,
                          auth_username=request.session['openid.id'],
                          auth_attribs=self.auth_attribs)
            u.name = newname
            u = self._handle_user_data(request, u)
            return ContinueLogin(u)
        # requested username already exists. if they know the password,
        # they can associate that account with the openid.
        assoc = lambda req, form: self._associate_account(req, form, newname)
        return MultistageFormLogin(assoc)

    def _handle_associate_continuation(self, request):
        if not 'openid.id' in request.session:
            return CancelLogin(_('No OpenID found in session.'))

        _ = request.getText
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if not password:
            return self._handle_name_continuation(request)
        u = user.User(request, name=username, password=password,
                      auth_method=self.name,
                      auth_username=request.session['openid.id'],
                      auth_attribs=self.auth_attribs)
        if u.valid:
            self._handle_user_data(request, u)
            return ContinueLogin(u, _('Your account is now associated to your OpenID.'))
        else:
            msg = _('The password you entered is not valid.')
            assoc = lambda req, form: self._associate_account(req, form, username, msg=msg)
            return MultistageFormLogin(assoc)

    def _handle_continuation(self, request):
        _ = request.getText
        oidstage = request.values.get('oidstage')
        if oidstage == '1':
            logging.debug('OpenID: handle verify continuation')
            return self._handle_verify_continuation(request)
        elif oidstage == '2':
            logging.debug('OpenID: handle name continuation')
            return self._handle_name_continuation(request)
        elif oidstage == '3':
            logging.debug('OpenID: handle associate continuation')
            return self._handle_associate_continuation(request)
        logging.debug('OpenID error: unknown continuation stage')
        return CancelLogin(_('OpenID error: unknown continuation stage'))

    def _openid_form(self, request, form, oidhtml):
        _ = request.getText
        txt = _('OpenID verification requires that you click this button:')
        # create JS to automatically submit the form if possible
        submitjs = """<script type="text/javascript">
<!--//
document.getElementById("openid_message").submit();
//-->
</script>
"""
        return ''.join([txt, oidhtml, submitjs])

    def login(self, request, user_obj, **kw):
        continuation = kw.get('multistage')

        if continuation:
            return self._handle_continuation(request)

        # openid is designed to work together with other auths
        if user_obj and user_obj.valid:
            return ContinueLogin(user_obj)

        openid_id = kw.get('openid_identifier')

        # nothing entered? continue...
        if not self._forced_service and not openid_id:
            return ContinueLogin(user_obj)

        _ = request.getText

        # user entered something but the session can't be stored
        if not request.cfg.cookie_lifetime[0]:
            return ContinueLogin(user_obj,
                                 _('Anonymous sessions need to be enabled for OpenID login.'))

        oidconsumer = consumer.Consumer(request.session,
                                        MoinOpenIDStore(request))

        try:
            fserv = self._forced_service
            if fserv:
                if isinstance(fserv, str) or isinstance(fserv, unicode):
                    oidreq = oidconsumer.begin(fserv)
                else:
                    oidreq = oidconsumer.beginWithoutDiscovery(fserv)
            else:
                oidreq = oidconsumer.begin(openid_id)
        except HTTPFetchingError:
            return ContinueLogin(None, _('Failed to resolve OpenID.'))
        except DiscoveryFailure:
            return ContinueLogin(None, _('OpenID discovery failure, not a valid OpenID.'))
        else:
            if oidreq is None:
                return ContinueLogin(None, _('No OpenID.'))

            self._modify_request(oidreq, request.cfg)

            return_to = get_multistage_continuation_url(request, self.name,
                                                        {'oidstage': '1'})
            trust_root = request.url_root
            if oidreq.shouldSendRedirect():
                redirect_url = oidreq.redirectURL(trust_root, return_to)
                return MultistageRedirectLogin(redirect_url)
            else:
                form_html = oidreq.formMarkup(trust_root, return_to,
                    form_tag_attrs={'id': 'openid_message'})
                mcall = lambda request, form:\
                    self._openid_form(request, form, form_html)
                ret = MultistageFormLogin(mcall)
                return ret

    def login_hint(self, request):
        _ = request.getText
        msg = u''
        if self._idselector_com:
            msg = self._idselector_com
        msg += _("If you do not have an account yet, you can still log in "
                 "with your OpenID and create one during login.")
        return msg
