# -*- coding: utf-8 -*-

import logging
import re
import time
import BaseHTTPServer
import urlparse
import os
import rutracker
import json
import math
from imdb import IMDb

HOST_NAME_DEFAULT = '0.0.0.0'
PORT_NUMBER_DEFAULT = 9000

try:
    from config import HOST_NAME, PORT_NUMBER
except ImportError:
    HOST_NAME, PORT_NUMBER = HOST_NAME_DEFAULT, PORT_NUMBER_DEFAULT

logger = logging.getLogger()
logger.setLevel(logging.INFO)

rutracker_engine = rutracker.rutracker()
imdb_engine = IMDb()


class SearchRequest(object):
    def __init__(self, search_query, imdb_id, year):
        self.search_query = search_query
        self.imdb_id = imdb_id
        self.year = year


class SearchResult(object):
    def __init__(self, search_dict, imdb_id):
        self.cat = search_dict['cat']
        self.desc_link = search_dict['desc_link']
        self.engine_url = search_dict['engine_url']
        self.leech = search_dict['leech']
        self.link = search_dict['link']
        self.name = search_dict['name']
        self.seeds = search_dict['seeds']
        self.size = search_dict['size']
        self.imdb_id = imdb_id if imdb_id.startswith('tt') else 'tt' + imdb_id

        self.id = rutracker.id_by_dl_link(self.link)
        self.down_link = 'http://{}:{}/?tid={}'.format('leugenea.io.bysh.me', PORT_NUMBER, self.id)

    def to_cp_dict(self):
        if 'bdrip' in self.name.lower() and (
                            '720p' in self.name.lower() or '1080p' in self.name.lower() or '2160p' in self.name.lower()):
            self.name = re.sub('[bB][dD][rR]ip', '', self.name)
        if 'web-dl' in self.name.lower() or 'webdl' in self.name.lower() and (
                            '720p' in self.name.lower() or '1080p' in self.name.lower() or '2160p' in self.name.lower()):
            self.name = re.sub('[wW][eE][bB]-?[dD][lL]', '', self.name)
        res = {
            'release_name': self.name,
            'torrent_id': self.id,
            'details_url': self.desc_link,
            'download_url': self.down_link,
            'imdb_id': self.imdb_id,
            'freeleech': True,
            'type': 'movie',
            'size': int(math.ceil(int(self.size) / float(2 ** 20))),
            'leechers': int(self.leech),
            'seeders': int(self.seeds),
        }
        return res


def remove_short_words(movie_name):
    spl = movie_name.split()
    spl = [s for s in spl if len(s) > 3]
    return ' '.join(spl)


def imdb_to_search_request(imdb_id):
    if imdb_id.startswith('tt'):
        imdb_id = imdb_id[2:]
    movie = imdb_engine.get_movie(imdb_id)
    search = u'{} {}'.format(remove_short_words(movie['title']), movie['year'])
    return [SearchRequest(search, imdb_id, movie['year'])]


def search_to_search_requests(search_unquoted):
    imdb_results = imdb_engine.search_movie(search_unquoted)
    res = [
        SearchRequest(u'{} {}'.format(remove_short_words(movie['title']), movie['year']), movie.getID(), movie['year'])
        for movie in imdb_results]
    return res


def search_requests_to_search_results(search_requests):
    res = []
    for sreq in search_requests:
        cur_search_results = rutracker_engine.search(sreq.search_query)
        res += [SearchResult(sr, sreq.imdb_id) for sr in cur_search_results]
    res.sort(key=lambda sr: 1.0 * int(sr.seeds) + 0.5 * int(sr.leech), reverse=True)
    return res


def search_results_to_json(search_results):
    result_dict = dict()
    result_dict['results'] = []
    result_dict['total_results'] = len(search_results)

    for sr in search_results:
        result_dict['results'].append(sr.to_cp_dict())

    return json.dumps(result_dict)


class RuTrackerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urlparse.urlparse(self.path).query
        query_components = urlparse.parse_qs(query)
        print(query_components)
        if 'tid' in query_components:
            tid = query_components['tid'][0]
            logging.info('Got query for torrent {}'.format(tid))
            mimetype = 'application/x-bittorrent'
            tf_path = os.path.join(rutracker.cache_dir, rutracker.get_torrentfilename_by_id(tid))
            if not os.path.exists(tf_path):
                logging.info('Getting torrent file')
                rutracker_engine.download_torrent_by_id(query_components['tid'][0])
            tf = open(tf_path)
            self.send_response(200)
            time.sleep(0.5)
            self.send_header('Content-type', mimetype)
            time.sleep(0.5)
            self.end_headers()
            time.sleep(0.5)
            self.wfile.write(tf.read())
            time.sleep(0.5)
            logging.info('Torrent file sent')
            tf.close()
        elif 'imdbid' in query_components or 'search' in query_components:
            if 'imdbid' in query_components:
                logging.info('Requesting info for IMDb id {}'.format(query_components['imdbid'][0]))
                search_requests = imdb_to_search_request(query_components['imdbid'][0])
            else:
                s = query_components['search'][0]
                logging.info('Requesting info for search {}'.format(s))
                search_requests = search_to_search_requests(s)
            logging.info(
                'Got {} search requests, taking first {}'.format(len(search_requests), min(len(search_requests), 5)))
            search_requests = search_requests[:3]

            logging.info('Searching on RuTracker for results...')
            search_results = search_requests_to_search_results(search_requests)
            logging.info('Got {} results'.format(len(search_results)))

            ret_json = search_results_to_json(search_results)
            self.send_response(200)
            time.sleep(0.5)
            self.send_header("Content-type", "application/json")
            time.sleep(0.5)
            self.end_headers()
            time.sleep(0.5)
            self.wfile.write(ret_json)
            time.sleep(0.5)
            logging.info('Search results sent')
        else:
            logging.info('Unknown query')
            ret_json = json.dumps({'error': 'Unknown query: {}'.format(query)})
            self.send_response(200)
            time.sleep(0.5)
            self.send_header("Content-type", "application/json")
            time.sleep(0.5)
            self.end_headers()
            time.sleep(0.5)
            self.wfile.write(ret_json)


if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), RuTrackerHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
