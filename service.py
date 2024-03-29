# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
import sys
import unicodedata
import urllib.error
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request
import urllib.request
import zipfile
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from ArgenteamUtilities import log, geturl

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmcvfs.translatePath(
    __addon__.getAddonInfo('path')
)
__profile__ = xbmcvfs.translatePath(
    __addon__.getAddonInfo('profile')
)
__resource__ = xbmcvfs.translatePath(
    os.path.join(__cwd__, 'resources', 'lib')
)
__temp__ = xbmcvfs.translatePath(
    os.path.join(__profile__, 'temp')
)
__temp__ = __temp__ + os.path.sep

sys.path.append(__resource__)

api_search_url = "https://argenteam.net/api/v1/search"
api_tvshow_url = "https://argenteam.net/api/v1/tvshow"
api_episode_url = "https://argenteam.net/api/v1/episode"
api_movie_url = "https://argenteam.net/api/v1/movie"
main_url = "https://argenteam.net/"


def append_subtitle(items):
    items.sort(key=lambda x: x['rating'], reverse=True)
    index = 0
    for item in items:
        index += 1
        list_item = xbmcgui.ListItem(
            label=item['lang'],
            label2=item['filename']
        )
        list_item.setArt({'icon': item['rating']})
        list_item.setArt({'thumb': item['image']})

        # listitem.setProperty("sync",  'true' if item["sync"] else 'false')
        list_item.setProperty(
            "hearing_imp",
            'true' if item["hearing_imp"] else 'false'
        )

        ## below arguments are optional, it can be used to pass any info needed
        ## in download function
        ## anything after "action=download&" will be sent to addon
        ## once user clicks listed subtitle to downlaod

        ## correción link de descarga de http://www. a https://
        link_temp = item['link'].replace("http://www.", "https://", 1)

        url = ("plugin://%s/?action=download&actionsortorder=%s&link=%s"
               "&filename=%s&id=%s") % (
                  __scriptid__,
                  str(index).zfill(2),
                  link_temp,
                  item['filename'],
                  item['id']
              )

        ## add it to list, this can be done as many times as needed
        ## for all subtitles found
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]),
            url=url,
            listitem=list_item,
            isFolder=False
        )


def search_movie(movie_id):
    url = api_movie_url + "?id=" + str(movie_id)
    content, response_url = geturl(url)

    return search_common(content)


def search_tvshow(result):
    # log(__name__, "Search tvshow = %s" % tvshow)

    subs = []

    if result['type'] == "tvshow":
        url = api_tvshow_url + "?id=" + str(result['id'])
        content, response_url = geturl(url)
        content = content.replace("null", '""')
        result_json = json.loads(content)

        for season in result_json['seasons']:
            for episode in season['episodes']:
                subs.extend(search_episode(episode['id']))

    elif result['type'] == "episode":
        subs.extend(search_episode(result['id']))

    return subs


def search_episode(episode_id):
    url = api_episode_url + "?id=" + str(episode_id)
    content, response_url = geturl(url)

    return search_common(content)


def search_common(content):
    if content is not None:
        log(__name__, "Resultados encontrados...")
        # object_subtitles = find_subtitles(content)
        items = []
        result = json.loads(content)

        if "releases" in result:
            for release in result['releases']:
                for subtitle in release['subtitles']:
                    item = {}
                    item['lang'] = "Spanish"
                    item['filename'] = urllib.parse.unquote_plus(
                        subtitle['uri'].split("/")[-1]
                    )
                    item['rating'] = str(subtitle['count'])
                    item['image'] = 'es'
                    item['id'] = subtitle['uri'].split("/")[-2]
                    item['link'] = subtitle['uri']

                    # Check for Closed Caption
                    if "-CC" in item['filename']:
                        item['hearing_imp'] = True
                    else:
                        item['hearing_imp'] = False

                    items.append(item)

        return items


def search_filename(filename, languages):
    title, year = xbmc.getCleanMovieTitle(filename)
    log(__name__, "clean title: \"%s\" (%s)" % (title, year))
    try:
        yearval = int(year)
    except ValueError:
        yearval = 0
    if title and yearval > 1900:
        search_string = title + "+" + year
        search_argenteam_api(search_string)
    else:
        match = re.search(
            r'\WS(?P<season>\d\d)E(?P<episode>\d\d)',
            title,
            flags=re.IGNORECASE
        )
        if match is not None:
            tvshow = title[:match.start('season') - 1].strip()
            season = match.group('season').lstrip('0')
            episode = match.group('episode').lstrip('0')
            search_string = "%s S%#02dE%#02d" % (
                tvshow,
                int(season),
                int(episode)
            )
            search_argenteam_api(search_string)
        else:
            search_argenteam_api(filename)


def search_argenteam_api(search_string):
    url = api_search_url + "?q=" + urllib.parse.quote_plus(search_string)
    content, response_url = geturl(url)
    response = json.loads(content)
    subs = []

    if response['total'] > 0:
        for result in response['results']:
            if result['type'] == "tvshow" or result['type'] == "episode":
                subs.extend(search_tvshow(result))
            elif result['type'] == "movie":
                subs.extend(search_movie(result['id']))

    append_subtitle(subs)


def search(item):
    filename = os.path.splitext(os.path.basename(item['file_original_path']))[0]
    log(__name__, "Search_argenteam='%s', filename='%s', addon_version=%s" % (
        item,
        filename,
        __version__)
        )

    if item['mansearch']:
        search_string = urllib.parse.unquote(item['mansearchstr'])
        search_argenteam_api(search_string)
    elif item['tvshow']:
        search_string = "%s S%#02dE%#02d" % (
            item['tvshow'].replace("(US)", ""),
            int(item['season']),
            int(item['episode'])
        )
        search_argenteam_api(search_string)
    elif item['title'] and item['year']:
        search_string = item['title'] + " " + item['year']
        search_argenteam_api(search_string)
    else:
        search_filename(filename, item['3let_language'])


def download(id, url, filename, search_string=""):
    subtitle_list = []
    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass"]

    ## Cleanup temp dir, we recomend you download/unzip your subs
    ## in temp folder and pass that to XBMC to copy and activate
    if xbmcvfs.exists(__temp__):
        shutil.rmtree(__temp__)
    xbmcvfs.mkdirs(__temp__)

    filename = os.path.join(__temp__, filename + ".zip")
    req = urllib.request.Request(url, headers={"User-Agent": "Kodi-Addon"})
    sub = urllib.request.urlopen(req).read()
    with open(filename, "wb") as subFile:
        subFile.write(sub)
    subFile.close()

    xbmc.sleep(500)
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(__temp__)

    for file in xbmcvfs.listdir(__temp__)[1]:
        file = os.path.join(__temp__, file)
        if os.path.splitext(file)[1] in exts:
            if search_string and file.lower().find(search_string.lower()) == -1:
                continue
            log(__name__, "=== returning subtitle file %s" % file)
            subtitle_list.append(file)

    return subtitle_list


def normalizeString(str_to_normalize):
    return unicodedata.normalize(
        'NFKD', str_to_normalize
    )


def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param


params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    item['temp'] = False
    item['rar'] = False
    item['mansearch'] = False
    item['year'] = xbmc.getInfoLabel("VideoPlayer.Year")
    item['season'] = str(xbmc.getInfoLabel("VideoPlayer.Season"))
    item['episode'] = str(xbmc.getInfoLabel("VideoPlayer.Episode"))
    item['tvshow'] = normalizeString(
        xbmc.getInfoLabel("VideoPlayer.TVshowtitle")
    )
    item['title'] = normalizeString(
        xbmc.getInfoLabel("VideoPlayer.OriginalTitle")
    )
    item['file_original_path'] = urllib.parse.unquote(
        xbmc.Player().getPlayingFile()
    )
    item['3let_language'] = []

    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']
        print(params['searchstring'])

    for lang in urllib.parse.unquote(params['languages']).split(","):
        item['3let_language'].append(
            xbmc.convertLanguage(lang, xbmc.ISO_639_2)
        )

    if item['title'] == "":
        # no original title, get just Title
        item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))

    # Check if season is "Special"
    if item['episode'].lower().find("s") > -1:
        item['season'] = "0"
        item['episode'] = item['episode'][-1:]

    if item['file_original_path'].find("http") > -1:
        item['temp'] = True

    elif item['file_original_path'].find("rar://") > -1:
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(
            item['file_original_path'][6:]
        )

    elif item['file_original_path'].find("stack://") > -1:
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    search(item)

elif params['action'] == 'download':
    ## we pickup all our arguments sent from def Search()
    if 'find' in params:
        subs = download(params["link"], params["find"])
    else:
        subs = download(params["id"], params["link"], params["filename"])
    ## we can return more than one subtitle for multi CD versions,
    ## for now we are still working out how to handle that
    ## in XBMC core
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(
            handle=int(sys.argv[1]),
            url=sub,
            listitem=listitem,
            isFolder=False
        )

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC
