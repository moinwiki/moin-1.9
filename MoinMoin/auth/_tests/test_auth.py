# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.auth and session tests

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import py.test

from MoinMoin.web.request import TestRequest, evaluate_request
from MoinMoin import wsgiapp
from MoinMoin._tests import wikiconfig


class AuthTest:
    """ test misc. auth methods """
    PAGES = ['FrontPage', 'MoinMoin', 'HelpContents', 'WikiSandBox', ] # must all exist!

    def setup_class(cls):
        """ Stuff that should be run to init the state of this test class

        Some test needs specific config values, or they will fail.
        """

    def teardown_class(cls):
        """ Stuff that should run to clean up the state of this test class

        """

    def run_request(self, **params):
        request = TestRequest(**params)
        #XXX: config passing hack
        request.given_config = getattr(self, 'Config', wikiconfig.Config)
        context = wsgiapp.init(request)
        wsgiapp.run(context)
        return context


class TestNoAuth(AuthTest):
    def testNoAuth(self):
        """ run a simple request, no auth, just check if it succeeds """
        request = self.run_request()

        # anon user?
        assert not request.user.valid

        appiter, status, headers = evaluate_request(request.request)
        # check if the request resulted in normal status, result headers and content
        assert status[:3] == '200'
        has_ct = has_v = has_cc = False
        for k, v in headers:
            if k == 'Content-Type':
                assert v.startswith('text/html')
                has_ct = True
            elif k == 'Vary':
                assert 'Cookie' in v
                assert 'Accept-Language' in v
                has_v = True
            elif k == 'Cache-Control':
                assert 'public' in v
                has_cc = True
            elif k == 'Set-Cookie':
                cookie = v
        assert has_ct
        assert has_v
        # XXX BROKEN?:
        #assert has_cc # cache anon user's content
        assert '</html>' in ''.join(appiter)

class TestAnonSession(AuthTest):
    class Config(wikiconfig.Config):
        cookie_lifetime = 1, 12

    def testAnonSession(self):
        """ run some requests, no auth, check if anon sessions work """
        cookie = ''
        trail_expected = []
        first = True
        for pagename in self.PAGES:
            environ_overrides = {'HTTP_COOKIE': cookie}
            request = self.run_request(path='/%s' % pagename,
                                       environ_overrides=environ_overrides)

            # anon user?
            assert not request.user.valid

            # Do we have a session?
            assert request.session is not None

            appiter, status, headers = evaluate_request(request.request)
            # check if the request resulted in normal status, result headers and content
            assert status[:3] == '200'
            has_ct = has_v = has_cc = False
            for k, v in headers:
                if k == 'Content-Type':
                    assert v.startswith('text/html')
                    has_ct = True
                elif k == 'Vary':
                    assert 'Cookie' in v
                    assert 'Accept-Language' in v
                    has_v = True
                elif k == 'Cache-Control':
                    assert 'private' in v
                    assert 'must-revalidate' in v
                    has_cc = True
                elif k == 'Set-Cookie':
                    cookie = v
            assert has_ct
            assert has_v
            # XX BROKEN
            #assert not has_cc # do not cache anon user's (with session!) content
            assert '</html>' in ''.join(appiter)

            # The trail is only ever saved on the second page display
            # because otherwise anonymous sessions would be created
            # for every request, even if it never sent a cookie!
            # Hence, skip over the first request and only verify
            # the trail for the second and following.
            if first:
                first = False
                continue

            assert not request.session.is_new

            trail_expected.append(unicode(pagename))

            # Requested pagenames get into trail?
            assert 'trail' in request.session
            trail = request.session['trail']
            assert trail == trail_expected

class TestHttpAuthSession(AuthTest):
    py.test.skip("We currently have no http auth code in moin. GivenAuth relies on the web server doing the http auth check.")
    class Config(wikiconfig.Config):
        from MoinMoin.auth.http import HttpAuth # does not exist (yet?)
        auth = [HttpAuth(autocreate=True)]

    def testHttpAuthSession(self):
        """ run some requests with http auth, check whether session works """
        username = u'HttpAuthTestUser'
        auth_info = u'%s:%s' % (username, u'testpass')
        auth_header = 'Basic %s' % auth_info.encode('base64')
        cookie = ''
        trail_expected = []
        first = True
        for pagename in self.PAGES:
            environ_overrides = {'HTTP_COOKIE': cookie,
                                 'HTTP_AUTHORIZATION': auth_header}
            request = self.run_request(path='/%s' % pagename,
                                       environ_overrides=environ_overrides)

            # Login worked?
            assert request.user.valid
            assert request.user.name == username

            # Do we have a session?
            assert request.session is not None

            appiter, status, headers = evaluate_request(request.request)
            # check if the request resulted in normal status, result headers and content
            assert status[:3] == '200'
            has_ct = has_v = has_cc = False
            for k, v in request.headers:
                if k == 'Content-Type':
                    assert v.startswith('text/html')
                    has_ct = True
                elif k == 'Vary':
                    assert 'Cookie' in v
                    assert 'Accept-Language' in v
                    has_v = True
                elif k == 'Cache-Control':
                    assert 'private' in v
                    assert 'must-revalidate' in v
                    has_cc = True
                elif k == 'Set-Cookie':
                    cookie = v
            assert has_ct
            assert has_v
            assert has_cc # do not cache logged-in user's content
            assert '</html>' in ''.join(appiter)

            # The trail is only ever saved on the second page display
            # because otherwise anonymous sessions would be created
            # for every request, even if it never sent a cookie!
            # Hence, skip over the first request and only verify
            # the trail for the second and following.
            if first:
                first = False
                continue

            trail_expected.append(unicode(pagename))

            # Requested pagenames get into trail?
            assert 'trail' in request.session
            trail = request.session['trail']
            assert trail == trail_expected

class TestMoinAuthSession(AuthTest):
    class Config(wikiconfig.Config):
        from MoinMoin.auth import MoinAuth
        auth = [MoinAuth()]

    def testMoinAuthSession(self):
        """ run some requests with MoinAuth, check whether session works """
        from MoinMoin.user import User
        username = u'MoinAuthTestUser'
        password = u'ßecretß'
        User(self.request, name=username, password=password).save() # create user
        trail_expected = []
        first = True
        for pagename in self.PAGES:
            if first:
                formdata = {
                    'name': username,
                    'password': password,
                    'login': 'login',
                }
                request = self.run_request(path='/%s' % pagename,
                                           query_string='login=login',
                                           method='POST', form_data=formdata)
            else: # not first page, use session cookie
                environ_overrides = {'HTTP_COOKIE': cookie}
                request = self.run_request(path='/%s' % pagename,
                                           environ_overrides=environ_overrides)

            # Login worked?
            assert request.user.valid
            assert request.user.name == username

            # Do we have a session?
            assert request.session is not None

            appiter, status, headers = evaluate_request(request.request)
            # check if the request resulted in normal status, result headers and content
            assert status[:3] == '200'
            has_ct = has_v = has_cc = False
            for k, v in request.headers:
                if k == 'Content-Type':
                    assert v.startswith('text/html')
                    has_ct = True
                elif k == 'Vary':
                    assert 'Cookie' in v
                    assert 'Accept-Language' in v
                    has_v = True
                elif k == 'Cache-Control':
                    assert 'private' in v
                    assert 'must-revalidate' in v
                    has_cc = True
                elif k == 'Set-Cookie':
                    cookie = v
            assert has_ct
            assert has_v
            assert has_cc # do not cache logged-in user's content
            assert '</html>' in ''.join(appiter)

            # The trail is only ever saved on the second page display
            # because otherwise anonymous sessions would be created
            # for every request, even if it never sent a cookie!
            # Hence, skip over the first request and only verify
            # the trail for the second and following.
            if first:
                first = False
                continue

            trail_expected.append(unicode(pagename))

            # Requested pagenames get into trail?
            assert 'trail' in request.session
            trail = request.session['trail']
            assert trail == trail_expected

