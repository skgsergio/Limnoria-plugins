Gets Minecraft/Mojang servers status (login, sesion, auth, ...).
Gets info from a Minecraft server (users, name, ...).

Public commands:
	mcstatus, mcs ->
		Gets Minecraft/Mojang servers status (login, sesion, auth, ...).

	minecraft, mc + <host|host:port> ->
		Gets info from a Minecraft server (users, name, ...).

Config:
	supybot.plugins.Minecraft.listMode (default: False) ->
		Use two lists of services (online and offline) to output minimal colors.

		Example when True (only Online and Offline have colors, green and red):
			[Minecraft Status] Online: Web, ..., Session server - Offline: Skin Server

		Example when False (all elements have color, green if online and red if offline):
			[Minecraft Status] Web | ... | Session server

	supybot.plugins.Minecraft.boldBanner (default: True) ->
		Use bold banner (the "Minecraft Status" part in the previous examples).
