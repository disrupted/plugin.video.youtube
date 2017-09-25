import re
import json
import requests

from youtube_plugin.youtube.provider import Provider
from youtube_plugin.kodion.impl import Context


def get_core_components():
    provider = Provider()
    context = Context(plugin_id='plugin.video.youtube')
    client = provider.get_client(context=context)

    return provider, context, client


def get_player_config(client, url):
    headers = {'Host': 'www.youtube.com',
               'Connection': 'keep-alive',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
               'Accept': '*/*',
               'DNT': '1',
               'Referer': 'https://www.youtube.com',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}

    params = {'hl': client._language,
              'gl': client._region}

    if client._access_token:
        params['access_token'] = client._access_token

    result = requests.get(url, params=params, headers=headers, verify=client._verify, allow_redirects=True)
    html = result.text

    _player_config = '{}'
    lead = 'ytplayer.config = '
    tail = ';ytplayer.load'
    pos = html.find(lead)
    if pos >= 0:
        html2 = html[pos + len(lead):]
        pos = html2.find(tail)
        if pos:
            _player_config = html2[:pos]

    try:
        player_config = json.loads(_player_config)
    except:
        player_config = dict()

    return player_config


def resolve(video_id, sort=True):
    """

    :param video_id: video id / video url
    :param sort: sort results by quality highest->lowest
    :type video_id: str
    :type sort: bool
    :return: all video items (resolved urls and metadata) for the given video id
    :rtype: list of dict
    """
    provider, context, client = get_core_components()
    streams = None

    if not video_id.startswith('http'):
        streams = client.get_video_streams(context=context, video_id=video_id)
    else:
        if 'v=' in video_id:
            v_id = re.search('v=(?P<video_id>[^&]+)', video_id)
            if v_id:
                streams = client.get_video_streams(context=context, video_id=v_id.group('video_id'))

        if streams is None:
            player_config = get_player_config(client, video_id)
            streams = client.get_video_streams(context=context, player_config=player_config)

    if sort:
        streams = sorted(streams, key=lambda x: x.get('sort', 0), reverse=True)

    return streams