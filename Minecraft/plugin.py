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

from __future__ import unicode_literals
import sys
import json
import socket
import struct

import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
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
    _ = PluginInternationalization('Minecraft')
except:
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

@internationalizeDocstring
class Minecraft(callbacks.Plugin):
    """Gets Minecraft/Mojang servers status (login, sesion, auth, ...).
    Gets info from a Minecraft server (users, name, ...)."""
    threaded = True

    _statusURL = 'http://status.mojang.com/check'

    _mcColors = ["\x0300,\xa7f", "\x0301,\xa70", "\x0302,\xa71", "\x0303,\xa72",
                 "\x0304,\xa7c", "\x0305,\xa74", "\x0306,\xa75", "\x0307,\xa76",
                 "\x0308,\xa7e", "\x0309,\xa7a", "\x0310,\xa73", "\x0311,\xa7b",
                 "\x0312,\xa71", "\x0313,\xa7d", "\x0314,\xa78", "\x0315,\xa77",
                 "\x02,\xa7l", "\x0310,\xa79", "\x09,\xa7o", "\x13,\xa7m",
                 "\x0f,\xa7r", "\x15,\xa7n"]

    def _parseMcStyle(self, msg):
        for c in self._mcColors:
            rep = c.split(',')
            msg = msg.replace(rep[1], rep[0])
        return msg.replace('\xa7k', '')

    def _toLenAndUtf16(self, string):
        return bytes(struct.pack(str('!h'), len(string))) + bytes(string.encode('utf-16be'))

    def mc(self, irc, msg, args, server):
        """<host|host:port>
        Asks for Minecraft server information. Host can be a domain or an IP."""
        if ":" in server:
            host, port = server.split(":", 1)
            try:
                port = int(port)
            except:
                port = -1
        else:
            host = server
            port = 25565

        if port < 0 or port > 65565:
            irc.error(_("Invalid port."))
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((host, port))

                # Minecraft Handshake: For more info see http://wiki.vg/Server_List_Ping
                sock.send(b'\xfe\x01\xfa')
                sock.send(self._toLenAndUtf16('MC|PingHost'))
                sock.send(bytes(struct.pack(str('!h'), 7 + 2*len(host))))
                sock.send(bytes(struct.pack(str('!b'), 78)))
                sock.send(self._toLenAndUtf16(host))
                sock.send(bytes(struct.pack(str('!I'), port)))

                response = sock.recv(1)
                if response != b'\xff':
                    irc.error(_("Server error or not a Minecraft server."))
                    return

                length = struct.unpack(str('!h'), sock.recv(2))[0]
                values = sock.recv(length * 2).decode('utf-16be')

                data = values.split('\x00')
                if len(data) == 1: # 1.8-Beta to 1.3
                    data = values.split('\xa7')
                    message = format(_("%s - %s/%s players"),
                                     data[0], data[1], data[2])
                else: # 1.4 to 1.6 (1.7 it's supported too, it have a protocol but supports old)
                    message = format(_("%s\x0f - %s - %s/%s players"),
                                     data[3], data[2], data[4], data[5])

                sock.close()
                irc.reply(self._parseMcStyle(message), prefixNick=False)
            except:
                irc.error(_("Couldn't connect to server."))

    mc = minecraft = wrap(mc, ['something'])

    def mcstatus(self, irc, msg, args):
        """takes no arguments
        Shows the status of the Minecraft/Mojang servers."""

        try:
            statusReq = urlopen(self._statusURL)
        except:
            statusReq = None

        if statusReq:
            if sys.version_info[0] < 3:
                statusRes = statusReq.read()
            else:
                statusRes = statusReq.read().decode(statusReq.headers.get_content_charset())

            statusRes = json.loads(statusRes)

            status = { 'online': [], 'offline': [] }
            for i in statusRes:
                service = list(i.keys())[0]

                if self.registryValue('shortNames'):
                    service = service.replace('mojang', 'mj').replace('minecraft', 'mc')

                if list(i.values())[0] == 'green':
                    status['online'].append(service)
                else:
                    status['offline'].append(service)

            online = ', '.join(status['online'])
            offline = ', '.join(status['offline'])

            irc.reply(format(_("[Minecraft Status] %s%s%s%s%s"),
                             '\x0303Online\x03: ' if len(online) > 0 else '',
                             online if len(online) > 0 else '',
                             ' - ' if len(online) > 0 and len(offline) > 0 else '',
                             '\x0304Offline\x03: ' if len(offline) > 0 else '',
                             offline if len(offline) > 0 else ''
                         ), prefixNick=False)
        else:
            irc.reply(_("[Minecraft Status] Status checker is down! Maybe other Minecraft/Mojang services are affected too."), prefixNick=False)

    mcs = mcstatus = wrap(mcstatus)

Class = Minecraft


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
