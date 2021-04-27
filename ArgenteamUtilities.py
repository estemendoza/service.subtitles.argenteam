# -*- coding: utf-8 -*-

import urllib.error
import urllib.parse
import urllib.request

import xbmc


def log(module, msg):
    xbmc.log(("### [%s] - %s" % (module, msg,)), level=xbmc.LOGDEBUG)


def geturl(url):
    log(__name__, "Getting url: %s" % url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Kodi-Addon"})
        response = urllib.request.urlopen(req)
        content = response.read()
        # Fix non-unicode characters in movie titles
        # strip_unicode = re.compile("([^-_a-zA-Z0-9!@#%&=,/'\";:~`\$\^\*\(\)\+\[\]\.\{\}\|\?<>\\]+|[^\s]+)")
        # content = strip_unicode.sub('', content)
        return_url = response.geturl()
    except:
        log(__name__, "Failed to get url: %s" % url)
        content = None
        return_url = None
    return content, return_url
