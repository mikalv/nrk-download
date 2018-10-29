import re
import logging
import sys

import requests
try:
    # Python 3
    from urllib.parse import unquote
except ImportError:
    # Python 2
    from urllib import unquote

from . import config


# Module wide logger
LOG = logging.getLogger(__name__)


def _api_url(path):
    if path.startswith('/mediaelement'):
        # This is the Granitt API
        # AKA Nrk.Programspiller.Backend.WebAPI
        #
        # http://v8.psapi.nrk.no  Now requires a key
        #
        base_url = 'http://nrkpswebapi2ne.cloudapp.net'
    elif path.startswith('/series'):
        # This is the Snapshot API
        # AKA Nrk.PsApi
        base_url = 'http://psapi3-webapp-prod-we.azurewebsites.net'
    else:
        LOG.error("No baseurl defined for %s", path)
        sys.exit(1)
    return base_url + path


def get_mediaelement(element_id):
    """
    Get information about an element ID

    :param element_id: The elementid you want information on
    :return: A dictionary with the JSON information
    """
    LOG.info("Getting json-data on media element %s", element_id)
    r = requests.get(_api_url('/mediaelement/{:s}'.format(element_id)))
    r.raise_for_status()
    json = r.json()

    # Extract download URLs for media and subtitles
    json['media_urls'] = []
    json['subtitle_urls'] = []
    if json.get('mediaAssets', None):
        for media in json.get('mediaAssets'):
            url = media.get('url', None)
            subtitle_url = media.get('webVttSubtitlesUrl', None)

            if url:
                # Download URL starts with /i instead of /z, and has master.m3u8 at the end
                url = re.sub(r'\.net/z/', '.net/i/', url)
                url = re.sub(r'manifest\.f4m$', 'master.m3u8', url)
                json['media_urls'].append(url)
            if subtitle_url:
                # ffmpeg struggles with downloading from https URLs
                subtitle_url = unquote(subtitle_url)
                subtitle_url = re.sub(r'^https', 'http', subtitle_url)
                json['subtitle_urls'].append(subtitle_url)

    return json


def get_series(series_id):
    """
    Get information on a TV-series

    :param series_id: str
    :return: json
    """
    LOG.info("Getting json-data on series %s", series_id)
    r = requests.get(_api_url('/series/{:s}'.format(series_id)))
    r.raise_for_status()
    json = r.json()
    json['title'] = re.sub(r'\s+', ' ', json['title'])

    return json


def get_episode_ids_of_series_season(series_id, season_id):
    LOG.info("Getting json-data with episode ids of series %s, season %s", series_id, season_id)
    r = requests.get(_api_url("/series/{}/seasons/{}/episodes".format(series_id, season_id)))
    r.raise_for_status()
    json = r.json()
    episode_ids = [episode['id'] for episode in reversed(json)]
    return episode_ids