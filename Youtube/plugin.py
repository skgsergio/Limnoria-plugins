###
# Copyright (c) 2013, Sergio Conde
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import sys
import json
from datetime import timedelta
from dateutil import parser, tz

import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.callbacks as callbacks

if sys.version_info[0] < 3:
    from urlparse import urlparse, parse_qs
    from urllib2 import urlopen
else:
    from urllib.parse import urlparse, parse_qs
    from urllib.request import urlopen

try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Youtube')
except:
    _ = lambda x: x
    internationalizeDocstring = lambda x: x


@internationalizeDocstring
class Youtube(callbacks.PluginRegexp):
    """Listens for Youtube URLs and retrieves video info."""
    threaded = True
    regexps = ['youtubeSnarfer']

    _apiUrl = 'http://gdata.youtube.com/feeds/api/videos/{}?v=2&alt=jsonc'

    def _youtubeId(self, value):
        query = urlparse(value)
        yid = None
        if query.hostname == 'youtu.be':
            yid = query.path[1:]
        elif query.hostname in ('www.youtube.com', 'youtube.com'):
            if query.path == '/watch':
                yid = parse_qs(query.query)['v'][0]
            elif (query.path[:7] == '/embed/'
                  or query.path[:3] == '/v/'):
                yid = query.path.split('/')[2]
        elif (query.hostname == 'm.youtube.com'
              and query.path == '/watch'):
            yid = parse_qs(query.query)['v'][0]
        elif (query.hostname == 'youtube.googleapis.com'
              and query.path[:3] == '/v/'):
            yid = query.path.split('/')[2]
        return yid

    def youtubeSnarfer(self, irc, msg, match):
        channel = msg.args[0]
        if not irc.isChannel(channel):
            return
        if self.registryValue('youtubeSnarfer', channel):
            ytid = self._youtubeId(match.group(0))
            if ytid:
                try:
                    apiReq = urlopen(self._apiUrl.format(ytid))
                except:
                    log.error("Couldn't connect to Youtube's API.")
                    apiReq = None

                if apiReq:
                    if sys.version_info[0] < 3:
                        apiRes = apiReq.read()
                    else:
                        cntCharset = apiReq.headers.get_content_charset()
                        apiRes = apiReq.read().decode(cntCharset)

                    apiRes = json.loads(apiRes)

                    if 'data' in apiRes:
                        vInfo = apiRes['data']

                        s = format("\x02YouTube\x02: %s", vInfo['title'])

                        if 'contentRating' in vInfo:
                            s += " \x02[NSFW]\x02"

                        if 'duration' in vInfo:
                            s += format(" - %s", str(timedelta(
                                seconds=int(vInfo['duration']))))

                        if 'viewCount' in vInfo:
                            s += format(_(" - %s views"),
                                        "{:,}".format(vInfo['viewCount']))

                        if not self.registryValue('useRating', channel):
                            if 'likeCount' in vInfo and 'ratingCount' in vInfo:
                                s += format(_(" - %s likes / %s dislikes"),
                                            vInfo['likeCount'],
                                            (int(vInfo['ratingCount']) -
                                             int(vInfo['likeCount'])))
                        else:
                            if 'rating' in vInfo:
                                s += format(_(" - %.1f/5.0 (%s ratings)"),
                                            vInfo['rating'],
                                            vInfo['ratingCount'])

                        if ('uploader' in vInfo
                            and self.registryValue('showUploader', channel)):
                            s += format(_(" - user: %s"),
                                        vInfo['uploader'])

                        if ('uploaded' in vInfo
                            and self.registryValue('showDate', channel)):
                            s += format(_(" - date: %s"),
                                        parser.parse(vInfo['uploaded'])
                                        .astimezone(tz.tzlocal()))

                        irc.reply(s, prefixNick=False)

    youtubeSnarfer = urlSnarfer(youtubeSnarfer)
    youtubeSnarfer.__doc__ = utils.web._httpUrlRe

Class = Youtube


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
