# Bootstrap setuptools
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
setup(
    name = 'flup',
    version = '1.0.1',
    packages = find_packages(),
    zip_safe = True,
    
    entry_points = """
    [paste.server_factory]
    ajp = flup.server.ajp:factory
    fcgi = flup.server.fcgi:factory
    scgi = flup.server.scgi:factory
    ajp_thread = flup.server.ajp:factory
    fcgi_thread = flup.server.fcgi:factory
    scgi_thread = flup.server.scgi:factory
    ajp_fork = flup.server.ajp_fork:factory
    fcgi_fork = flup.server.fcgi_fork:factory
    scgi_fork = flup.server.scgi_fork:factory
    """,
    
    author = 'Allan Saddi',
    author_email = 'allan@saddi.com',
    description = 'Random assortment of WSGI servers',
    license = 'BSD',
    url='http://www.saddi.com/software/flup/',
    classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    )
