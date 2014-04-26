Simple Quote system using SQLite that can be enabled/disabled per channel.

Public commands:
	addquote [--channel <#channel>] <text> ->
		Adds a new quote in #channel database.

	delquote [--channel <#channel>] <id> ->
		Delete the quote number 'id' of #channel.
		Can be only done creator of the quote in the first 5 minutes or by an admin.

	findquote [--channel <#channel>] [<id>] ->
		Search quotes in the #channel database containing 'text'.

	quote [--channel <#channel>] [<id>] ->
		Get a random quote or the quote number 'id' from #channel database.

	quoteinfo [--channel <#channel>] <id> ->
		Shows the info of the quote number 'id' of #channel.
		It shows who stored it and when.

Config:
	supybot.plugins.Quotes.enabled (default: True) ->
		Enable the Quote system.
