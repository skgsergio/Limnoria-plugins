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

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Minecraft')
except:
    _ = lambda x:x

def configure(advanced):
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Minecraft', True)

    if yn(_("""Do you want to use list mode instead colorful mode?
             (colorful mode uses color per service, list mode prints
              two list, one with the onlines other with the offlines)"""), default=False):
        Minecraft.listMode.setValue(True)

    if not yn(_("""Do you want the plugin banner to be bold?"""), default=True):
        Minecraft.boldBanner.setValue(False)

Minecraft = conf.registerPlugin('Minecraft')
conf.registerChannelValue(Minecraft, 'listMode',
    registry.Boolean(False, _("""Use two lists of services (online and offline) to output
    minimal colors.""")))

conf.registerChannelValue(Minecraft, 'boldBanner',
    registry.Boolean(True, _("""Use bold plugin banner.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
