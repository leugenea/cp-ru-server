# CouchPotato search provider server for russian trackers

This is server for providing search API for [CouchPotato](https://couchpota.to/) for some russian trackers like [RuTracker](https://rutracker.org/).

# Installation
## Python and PIP installation
All you need is Python 2.7 and PIP, you can grab one [here](https://www.python.org/downloads/release/python-2712/).
## Dependencies installation
To install dependencies, cd to repository's directory and run:
```sh
pip install -r requirements.txt
```

# Running
Copy file `config_example.py` to `config.py` and edit in config.py you login/password for RuTracker as well as host and port you want.
By default, server will listen on `0.0.0.0:9000`.
## Note
Your CouchPotato server **MUST** have access to your PC with this server to send search requests.
Also you should check if RuTracker is available from your network.

# How does it work?
* You run cp-ru-server on your PC/server/whatever
* You add custom search provider in CouchPotato settings like described [here](https://github.com/CouchPotato/CouchPotatoServer/wiki/CouchPotato-Torrent-Provider)
* As host you paste address of host and port
* When you search for a movie in CP:
  * CP server'll send search request to cp-ru-server instance
  * cp-ru-server will parse it and search on RuTracker for releases with such name and IMDB id
  * you'll see found releases as always
* When you want to add release to queue:
  * CP server'll send download request to cp-ru-server instance
  * as long as your client should be authorized on RuTracker for downloading, download links in JSON answers to CP are pointing cp-ru-server's address and port, but with different arguments
  * so on torrent file download request .torrent file for choosen release will be downloaded into `cache` subdirectory of current directory
  * aaaaand will be sent to CP server as a response

# What's working for now?
* Search on RuTracker, but with some limitations:
  * at least one of words should be at least 3 characters (because I remove short words (IMDB having [some issues with namings sometimes](http://www.imdb.com/find?q=alice+in+wonderland)))
  * I'm not sure if searching using russian letters is working
  * I'm not sure if searching for russian/USSR movies is working (because of Unicode and stuff), also see previous item

# I love this! But…
## … but I need more features / not this / not exactly this / I want to use [Sonarr](https://sonarr.tv/) / I want to use [Headphones](https://github.com/rembo10/headphones) (underline whatever applicable)
Great! I'm also want to add more features for this server, but I don't have much time for developing and debugging.
So, your issues/pull requests/suggestions are welcome!
For now this is my want list:
* fix searching using russian (Unicode) letters / fix searching for russian/USSR movies
* support for authorization using login/hash instead of login/password
* add more trackers (like [kinozal.tv](http://kinozal.tv))
* add support for proxies
* search for ability to download .torrent files directly from RuTracker
* code cleanup/refactoring

# Special thanks
RuTracker searcher/downloader based on external project by [Skymirrh](https://github.com/Skymirrh) located [here](https://github.com/Skymirrh/qBittorrent-rutracker-plugin).
