# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utility functions for the web-layer

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import log
logging = log.getLogger(__name__)

def check_spider(useragent, cfg):
    """ Simple check if useragent is a spider bot
    
    @param useragent: werkzeug.useragents.UserAgent
    @param cfg: wikiconfig instance
    """
    is_spider = False
    if useragent and cfg.cache.ua_spiders:
        is_spider = cfg.cache.ua_spiders.search(str(useragent)) is not None
    return is_spider

def handle_auth_form(user_obj):
    logging.warning("handle_auth_form needs to be implemented yet.")
    return user_obj
