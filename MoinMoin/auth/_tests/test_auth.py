# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.auth and session tests

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py.test
py.test.skip("broken due to test Config refactoring, fix later")

import StringIO, urllib

from MoinMoin.server.server_wsgi import WsgiConfig
from MoinMoin.request import request_wsgi
from MoinMoin._tests import wikiconfig


class AuthTest:
    """ test misc. auth methods """
    PAGES = ['FrontPage', 'MoinMoin', 'HelpContents', 'WikiSandBox', ] # must all exist!

    def setup_class(cls):
        """ Stuff that should be run to init the state of this test class

        Some test needs specific config values, or they will fail.
        """
        config = WsgiConfig() # you MUST create an instance

    def teardown_class(cls):
        """ Stuff that should run to clean up the state of this test class

        """
        pass

    def setup_env(self, **kw):
        default_environ = {
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '80',
            'SCRIPT_NAME': '',
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'REMOTE_ADDR': '10.10.10.10',
            'HTTP_HOST': 'localhost',
            #'HTTP_COOKIE': '',
            #'HTTP_ACCEPT_LANGUAGE': '',
        }
        env = {}
        env.update(default_environ)
        env.update(kw)
        if 'wsgi.input' not in env:
            env['wsgi.input'] = StringIO.StringIO()
        return env

    def process_request(self, environ):
        request = request_wsgi.Request(environ)
        save_user = request.user # keep a reference, request.finish does "del request.user"
        request.run()
        request.user = save_user
        return request # request.status, request.headers, request.output()


class TestNoAuth(AuthTest):
    def testNoAuth(self):
        """ run a simple request, no auth, just check if it succeeds """
        environ = self.setup_env()
        request = self.process_request(environ)

        # anon user?
        assert not request.user.valid

        # check if the request resulted in normal status, result headers and content
        assert request.status == '200 OK'
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
                assert 'public' in v
                has_cc = True
            elif k == 'Set-Cookie':
                cookie = v
        assert has_ct
        assert has_v
        # XXX BROKEN?:
        #assert has_cc # cache anon user's content
        output = request.output()
        assert '</html>' in output

class TestAnonSession(AuthTest):
    class Config(wikiconfig.Config):
        anonymous_session_lifetime = 1

    def testAnonSession(self):
        """ run some requests, no auth, check if anon sessions work """
        cookie = ''
        trail_expected = []
        first = True
        for pagename in self.PAGES:
            environ = self.setup_env(PATH_INFO='/%s' % pagename,
                                     HTTP_COOKIE=cookie)
            request = self.process_request(environ)

            # anon user?
            assert not request.user.valid

            # Do we have a session?
            assert request.session

            # check if the request resulted in normal status, result headers and content
            assert request.status == '200 OK'
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
            # XX BROKEN
            #assert not has_cc # do not cache anon user's (with session!) content
            output = request.output()
            assert '</html>' in output

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
    class Config(wikiconfig.Config):
        from MoinMoin.auth.http import HTTPAuth
        auth = [HTTPAuth(autocreate=True)]

    def testHttpAuthSession(self):
        """ run some requests with http auth, check whether session works """
        username = u'HttpAuthTestUser'
        cookie = ''
        trail_expected = []
        first = True
        for pagename in self.PAGES:
            environ = self.setup_env(AUTH_TYPE='Basic', REMOTE_USER=str(username),
                                     PATH_INFO='/%s' % pagename,
                                     HTTP_COOKIE=cookie)
            request = self.process_request(environ)

            # Login worked?
            assert request.user.valid
            assert request.user.name == username

            # Do we have a session?
            assert request.session

            # check if the request resulted in normal status, result headers and content
            assert request.status == '200 OK'
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
            output = request.output()
            assert '</html>' in output

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
                formdata = urllib.urlencode({
                    'name': username.encode('utf-8'),
                    'password': password.encode('utf-8'),
                    'login': 'login',
                })
                environ = self.setup_env(PATH_INFO='/%s' % pagename,
                                         HTTP_CONTENT_TYPE='application/x-www-form-urlencoded',
                                         HTTP_CONTENT_LENGTH='%d' % len(formdata),
                                         QUERY_STRING='action=login', REQUEST_METHOD='POST',
                                         **{'wsgi.input': StringIO.StringIO(formdata)})
            else: # not first page, use session cookie
                environ = self.setup_env(PATH_INFO='/%s' % pagename,
                                         HTTP_COOKIE=cookie)
            request = self.process_request(environ)

            # Login worked?
            assert request.user.valid
            assert request.user.name == username

            # Do we have a session?
            assert request.session

            # check if the request resulted in normal status, result headers and content
            assert request.status == '200 OK'
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
            output = request.output()
            assert '</html>' in output

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

