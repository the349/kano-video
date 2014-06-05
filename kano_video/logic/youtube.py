#!/usr/bin/env python

# Copyright (C) 2014 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#

import sys
import os
from shutil import rmtree
from kano.utils import requests_get_json, run_cmd

tmp_dir = '/tmp/kano-video'
last_search_count = 0


def page_to_index(page, max_results=10):
    return ((page - 1) * max_results) + 1


def get_last_search_count():
    global last_search_count

    return last_search_count


def search_youtube_by_keyword(keyword=None, popular=False, max_results=10, start_index=1, parent_control=False):
    url = 'http://gdata.youtube.com/feeds/api/videos'
    params = {
        'v': 2,
        'vq': keyword,
        'racy': 'exclude',
        'orderby': 'relevance',
        'alt': 'json',
        'max-results': max_results,
        'start-index': start_index
    }
    if popular:
        params['orderby'] = 'viewCount'

    if parent_control == True:
        params['safeSearch'] = 'strict'

    success, error, data = requests_get_json(url, params=params)

    if not success:
        return None
    if 'feed' in data and 'entry' in data['feed']:
        global last_search_count
        last_search_count = data['feed']['openSearch$totalResults']['$t']

        return data['feed']['entry']


def search_youtube_by_user(username, parent_control=False):
    url = 'http://gdata.youtube.com/feeds/api/users/{}/uploads'.format(username)
    params = {
        'v': 2,
        'alt': 'json',
        'orderby': 'viewCount',
        'max-results': 10
    }

    if parent_control == True:
        params['safeSearch'] = 'strict'

    success, error, data = requests_get_json(url, params=params)
    if not success:
        return None
    if 'feed' in data and 'entry' in data['feed']:
        global last_search_count
        last_search_count = data['feed']['openSearch$totalResults']['$t']

        return data['feed']['entry']


def parse_youtube_entries(entries):
    if os.path.exists(tmp_dir):
        rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    my_entries = list()
    for e in entries:
        # Small thumbnail
        for thumb in e['media$group']['media$thumbnail']:
            if thumb['width'] == 120 and thumb['height'] == 90:
                thumbnail = thumb['url']
                break

        # Big thumbnail
        for thumb in e['media$group']['media$thumbnail']:
            if thumb['width'] == 480 and thumb['height'] == 360:
                bigthumb = thumb['url']
                break

        author = e['author'][0]['name']['$t'].encode('utf-8')
        title = e['title']['$t'].encode('utf-8')
        description = e['media$group']['media$description']['$t'].encode('utf-8')

        video_url = e['media$group']['media$content'][0]['url']
        duration  = e['media$group']['media$content'][0]['duration']

        duration_min = duration / 60
        duration_sec = duration % 60

        # On youtube version 2, eventually the viewCount key is not returned
        try:
            viewcount = int (e['yt$statistics']['viewCount'])
        except:
            viewcount = 0

        entry_data = {
            'author': author,
            'title': title,
            'description': description,
            'video_url': video_url,
            'duration': duration,
            'duration_min': duration_min,
            'duration_sec': duration_sec,
            'viewcount': viewcount,
            'thumbnail': thumbnail,
            'big_thumb': bigthumb
        }
        my_entries.append(entry_data)
    return my_entries


def get_video_file_url(video_url):
    cmd = 'youtube-dl -g {}'.format(video_url)
    o, e, _ = run_cmd(cmd)
    if e:
        return False, e
    return True, o.strip()