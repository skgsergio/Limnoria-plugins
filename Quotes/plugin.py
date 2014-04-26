###
# Copyright (c) 2014, Sergio Conde
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

import os
import sys
import time
from datetime import datetime
import sqlite3

import supybot.ircdb as ircdb
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Quotes')
except ImportError:
    _ = lambda x:x

class SqliteQuotesDB(object):
    def __init__(self, filename):
        self.dbs = ircutils.IrcDict()
        self.filename = filename

    def close(self):
        for db in (self.dbs.itervalues() if sys.version_info[0] < 3 else self.dbs.values()):
            db.close()

    def _getDb(self, channel):
        filename = plugins.makeChannelFilename(self.filename, channel)

        if filename in self.dbs:
            return self.dbs[filename]

        if os.path.exists(filename):
            db = sqlite3.connect(filename, check_same_thread=False)
            db.text_factory = str
            self.dbs[filename] = db
            return db

        db = sqlite3.connect(filename, check_same_thread=False)
        db.text_factory = str
        self.dbs[filename] = db

        cur = db.cursor()
        cur.execute("""CREATE VIRTUAL TABLE quotes USING fts4(
        text TEXT,
        nick TEXT,
        ts INTEGER
        )""")
        db.commit()

        return db

    def getQuoteById(self, channel, qid):
        db = self._getDb(channel)
        cur = db.cursor()
        cur.execute("""SELECT rowid, text, nick, ts FROM quotes WHERE rowid = ? LIMIT 1""", (qid,))
        return cur.fetchone()

    def getQuoteRandom(self, channel):
        db = self._getDb(channel)
        cur = db.cursor()
        cur.execute("""SELECT rowid, text, nick, ts FROM quotes ORDER BY RANDOM() LIMIT 1""")
        return cur.fetchone()

    def searchQuote(self, channel, text):
        db = self._getDb(channel)
        cur = db.cursor()
        cur.execute("""SELECT rowid FROM quotes WHERE text MATCH ?""", (text,))
        return [str(i[0]) for i in cur.fetchall()]

    def insertQuote(self, channel, text, nick, ts):
        db = self._getDb(channel)
        cur = db.cursor()
        cur.execute("""INSERT INTO quotes (text, nick, ts) VALUES (?, ?, ?)""", (text, nick, ts,))
        db.commit()
        return cur.lastrowid

    def delQuoteById(self, channel, qid):
        db = self._getDb(channel)
        cur = db.cursor()
        cur.execute("""DELETE FROM quotes WHERE rowid = ?""", (qid,))
        db.commit()

QuotesDB = plugins.DB('Quotes', {'sqlite3': SqliteQuotesDB})

class Quotes(callbacks.Plugin):
    """Simple quote system"""
    def __init__(self, irc):
        self.__parent = super(Quotes, self)
        self.__parent.__init__(irc)
        self.db = QuotesDB()

    def die(self):
        self.__parent.die()
        self.db.close()

    def addquote(self, irc, msg, args, optlist, text):
        """[--channel <#channel>] <text>
        Inserts a quote in the database. If it gives an error saying '"x"
        is not valid command' try again with the text between quotes ("text").
        If --channel is supplied the quote is stored in that channel database."""
        channel = msg.args[0]
        for (option, arg) in optlist:
            if option == 'channel':
                if not ircutils.isChannel(arg):
                    irc.error(format(_('%s is not a valid channel.'), arg), Raise=True)
                channel = arg

        qid = self.db.insertQuote(channel, text, msg.nick, int(time.time()))
        irc.reply(format(_("Quote inserted with id: %s"), qid))

    addquote = wrap(addquote, [getopts({'channel': 'somethingWithoutSpaces'}), 'text'])

    def delquote(self, irc, msg, args, optlist, qid):
        """[--channel <#channel>] <id>
        Delete the quote number 'id', only by the creator of the quote in
        the first 5 minutes or by an admin. If --channel is supplied the
        quote is fetched from that channel database."""
        channel = msg.args[0]
        for (option, arg) in optlist:
            if option == 'channel':
                if not ircutils.isChannel(arg):
                    irc.error(format(_('%s is not a valid channel.'), arg), Raise=True)
                channel = arg

        q = self.db.getQuoteById(channel, qid)

        if q != None:
            if ircdb.checkCapability(msg.prefix, 'admin'):
                self.db.delQuoteById(channel, qid)
                irc.replySuccess()
            elif (time.time() - 300) <= q[3]:
                if q[2].lower() == msg.nick.lower():
                    self.db.delQuoteById(channel, qid)
                    irc.replySuccess()
                else:
                    irc.error(format(_("This quote only can be deleted by %s or an admin."), q[2]))
            else:
                irc.error(format(_("Too late, it has already passed 5 minutes. Ask an admin."), qid, channel))
        else:
            irc.error(format(_("No such quote %s in %s's database."), qid, channel))

    delquote = wrap(delquote, [getopts({'channel': 'somethingWithoutSpaces'}), 'int'])

    def quote(self, irc, msg, args, optlist, qid):
        """[--channel <#channel>] [<id>]
        Get a random quote or the quote number 'id'. If --channel is supplied
        the quote is fetched from that channel database."""
        channel = msg.args[0]
        for (option, arg) in optlist:
            if option == 'channel':
                if not ircutils.isChannel(arg):
                    irc.error(format(_('%s is not a valid channel.'), arg), Raise=True)
                channel = arg

        if qid != None:
            q = self.db.getQuoteById(channel, qid)
        else:
            q = self.db.getQuoteRandom(channel)

        if q != None:
            irc.reply(format("#%s: %s", q[0], q[1]), noLengthCheck=True)
        elif qid != None:
            irc.error(format(_("No such quote %s in %s's database."), qid, channel))
        else:
            irc.error(format(_("There is no quotes in %s's database."), channel))

    quote = wrap(quote, [getopts({'channel': 'somethingWithoutSpaces'}), optional('int')])

    def findquote(self, irc, msg, args, optlist, text):
        """[--channel <#channel>] [<id>]
        Search quotes containing 'text'. If --channel is supplied
        the quote is fetched from that channel database."""
        channel = msg.args[0]
        for (option, arg) in optlist:
            if option == 'channel':
                if not ircutils.isChannel(arg):
                    irc.error(format(_('%s is not a valid channel.'), arg), Raise=True)
                channel = arg

        qlist = self.db.searchQuote(channel, text)

        if len(qlist) > 0:
            irc.reply(format("Quotes containing '%s': %s", text, ', '.join(qlist)))
            for i in qlist[-3:]:
                q = self.db.getQuoteById(channel, i)
                irc.reply(format("#%s: %s", q[0], q[1]), noLengthCheck=True)
        else:
            irc.error(format(_("There is no quote that contains '%s'"), text))

    findquote = wrap(findquote, [getopts({'channel': 'somethingWithoutSpaces'}), 'text'])

    def quoteinfo(self, irc, msg, args, optlist, qid):
        """[--channel <#channel>] <id>
        Shows the info of the quote number 'id'. If --channel is supplied
        the quote is fetched from that channel database."""
        channel = msg.args[0]
        for (option, arg) in optlist:
            if option == 'channel':
                if not ircutils.isChannel(arg):
                    irc.error(format(_('%s is not a valid channel.'), arg), Raise=True)
                channel = arg

        q = self.db.getQuoteById(channel, qid)

        if q != None:
            irc.reply(format("#%s: Quote stored by %s (%s)", q[0], q[2],
                             datetime.fromtimestamp(q[3]).strftime("%Y-%m-%d %H:%M:%S")))
        else:
            irc.error(format(_("No such quote %s in %s's database."), qid, channel))

    quoteinfo = wrap(quoteinfo, [getopts({'channel': 'somethingWithoutSpaces'}), 'int'])

Class = Quotes


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
