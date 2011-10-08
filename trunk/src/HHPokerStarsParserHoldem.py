
import re
import HHConfig


GameMapping = {
		"Hold'em": HHConfig.GameHoldem,
		}

GameLimitMapping = {
		"No Limit": HHConfig.GameLimitNoLimit,
		}

CurrencyMapping = {
		'USD': HHConfig.CurrencyDollar,
		}	
	

#************************************************************************************
# parser implementation
#************************************************************************************
class PokerStarsParserHoldemEN(HHConfig.LineParserBase):
	
	Site = HHConfig.SitePokerStars
	Game = HHConfig.GameHoldem
	Language = HHConfig.LanguageEN
		
	def __init__(self, *args, **kws):
		HHConfig.LineParserBase.__init__(self, *args, **kws)
		self._seatNoButton = 0
	
	def feed(self, *args, **kws):
		self._seatNoButton = 0
		return HHConfig.LineParserBase.feed(self, *args, **kws)
		
	def stringToFloat(self, amount):
		return float(amount)
		
	PatternGameHeaderCashGame = re.compile(
		"""^PokerStars\s Game\s
			\#(?P<handID>\d+)\:\s\s
			(?P<game>Hold\'em)\s
			(?P<gameLimit>No\sLimit)\s
			\(
				[^\d\.]?(?P<smallBlind>[\d\.]+)\/
				[^\d\.]?(?P<bigBlind>[\d\.]+)
				\s?
				(?P<currency>[A-Z]+)?
			\)
			\s-\s
			.*
			\[
				(?P<year>\d+)\/
				(?P<month>\d+)\/
				(?P<day>\d+)\s
				(?P<hour>\d+)\:
				(?P<minute>\d+)\:
				(?P<second>\d+)
				.*
			\]\s*$
		""", re.X|re.I
		)
	PatternTableHeader = re.compile(
		"""^Table\s \'(?P<tableName>[^\']+)\'\s
			(?P<maxPlayers>\d+)\-max\s
			Seat\s\#(?P<seatNoButton>\d+)\sis\sthe\sbutton
			\s*$
		""", re.X|re.I
		)
	
	@HHConfig.LineParserMethod(priority=1)
	def parseHandStart(self, data, events):
		if len(data) < 2:
			return
		
		m = self.PatternGameHeaderCashGame.match(data[0]['line'])
		if m is None:
			return
		data.pop(0)
		d = m.groupdict()
		m = self.PatternTableHeader.match(data[0]['line'])
		if m is None:
			return
		data.pop(0)
		d.update(m.groupdict())
		self._seatNoButton = int(d.pop('seatNoButton'))
		d['game'] = GameMapping[d['game']]
		d['gameLimit'] = GameLimitMapping[d['gameLimit']]
		d['currency'] = CurrencyMapping[d['currency']]
		d['bigBlind'] = self.stringToFloat(d['bigBlind'])
		d['smallBlind'] = self.stringToFloat(d['smallBlind'])
		d['timestamp'] = HHConfig.timestampFromDate(
								d.pop('year'), 
								d.pop('month'), 
								d.pop('day'), 
								d.pop('hour'), 
								d.pop('minute'), 
								d.pop('second'), 
								) + 18000	# ET + 5 hours == UTC
		events[0] = HHConfig.EventHandStart(**d)
	
	
	PatternPlayer = re.compile(
		"""^Seat\s(?P<seatNo>\d+)\:\s
				(?P<name>.+?)\s
				\(
					[^\d\.]?(?P<stack>[\d\.]+)\sin\schips
				\)
				(?P<sitsOut>\s is\s sitting\s out)?
				\s*$
		""", re.X|re.I
		)
	PatternPlayerSitsOut = re.compile("""^(?P<name>.*?)\:\s (sits\s out | is\s sitting\s out)\s*$
		""", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=10)
	def parsePlayer(self, data, events):
		
		# cash game: stars does not report a player sitting out initially (seatNo, stackSize)
		# so we have to check for players sitting out that are not seated.
		# 1) check if we are parsing a cash game hand (events[0])
		# 2) find all players seated
		# 3) find all sitting out events
		# 4) report as player all players seated + sitting out players that are not seated
		#
		# stars uses "sits out" and "is sitting out" in this spot. no idea
		# what the distintion is about.
		
		# find players
		items = []
		players = []
		playerNames = []
		for item in data:
			m = self.PatternPlayer.match(item['line'])
			if m is None:
				break
			items.append(item)
			d = m.groupdict()
			d['seatNo'] = int(d['seatNo'])
			d['stack'] = self.stringToFloat(d['stack'])
			d['sitsOut'] = bool(d['sitsOut'])
			eventPlayer =  HHConfig.EventPlayer(**d)
			events[item['lineno']] = eventPlayer
			players.append(eventPlayer)
			playerNames.append(d['name'])
		for item in items:
			data.remove(item)
		
		# determine seat names
		players =  players[self._seatNoButton-1:] + players[:self._seatNoButton-1]
		for buttonOrder, seatName in enumerate(HHConfig.Seats.SeatNames[len(players)]):
			player = players[buttonOrder]
			player.seatName = seatName
			player.buttonOrder = buttonOrder +1
				
		# find all players sitting out
		items = []
		for item in data:
			m = self.PatternPlayerSitsOut.match(item['line'])
			if m is not None:
				items.append(item)
				playerName = m.group('name')
				if playerName not in playerNames:
					# assume cash game (see notes above)
					events[item['lineno']] = HHConfig.EventPlayer(name=playerName, sitsOut=True)
				else:
					events[item['lineno']] = HHConfig.EventPlayerSitsOut(name=playerName)
		for item in items:
			data.remove(item)
					
	
	PatternPlayerPostsSmallBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\ssmall\sblind\s[^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HHConfig.LineParserMethod(priority=45)
	def parsePlayerPostsSmallBlind(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerPostsSmallBlind.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[item['lineno']] = HHConfig.EventPlayerPostsSmallBlind(**d)
		for item in items:
			data.remove(item)
		
	
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\sbig\sblind\s[^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HHConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerPostsBigBlind.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[item['lineno']] = HHConfig.EventPlayerPostsBigBlind(**d)
		for item in items:
			data.remove(item)
	
	
	PatternPreflop = re.compile("""^^\*\*\*\sHOLE\sCARDS\s\*\*\*$\s*$""")				
	@HHConfig.LineParserMethod(priority=100)
	def parsePreflop(self, data, events):
		for item in data:
			m = self.PatternPreflop.match(item['line'])
			if m is not None:
				events[item['lineno']] = HHConfig.EventPreflop()
				data.remove(item)
				break
		
	PatternPlayerHoleCards = re.compile(
		"^Dealt\s to\s (?P<name>.*?)\s \[(?P<card1>[23456789TJQKA][cdhs])\s(?P<card2>[23456789TJQKA][cdhs])\]\s*$", 
		re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=150)
	def parsePlayerPlayerHoleCards(self, data, events):
		for item in data:
			m = self.PatternPlayerHoleCards.match(item['line'])
			if m is not None:
				d = m.groupdict()
				event = HHConfig.EventPlayerHoleCards(name=d['name'], cards=(d['card1'], d['card2']))
				events[item['lineno']] = event
				data.remove(item)
				break
	
	
	PatternPlayerChecks = re.compile(
		"^(?P<name>.*?)\:\s checks\s*$", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=160)
	def parsePlayerChecks(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerChecks.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerChecks(**m.groupdict())
		for item in items:
			data.remove(item)
	
	
	PatternPlayerFolds = re.compile(
		"^(?P<name>.*?)\:\s folds\s*$", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=160)
	def parsePlayerFolds(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerFolds.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerFolds(**m.groupdict())
		for item in items:
			data.remove(item)
				
	
	PatternPlayerBets = re.compile(
		"^(?P<name>.*?)\:\s bets\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=160)
	def parsePlayerBets(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerBets.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[item['lineno']] = HHConfig.EventPlayerBets(**d)
		for item in items:
			data.remove(item)
	
	
	
	PatternPlayerRaises = re.compile(
		"^(?P<name>.*?)\:\s raises\s .*? to\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=160)
	def parsePlayerRaises(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerRaises.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[item['lineno']] = HHConfig.EventPlayerRaises(**d)
		for item in items:
			data.remove(item)
	
	
	PatternPlayerCalls = re.compile(
		"^(?P<name>.*?)\:\s calls\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HHConfig.LineParserMethod(priority=160)
	def parsePlayerCalls(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerCalls.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[item['lineno']] = HHConfig.EventPlayerCalls(**d)
		for item in items:
			data.remove(item)
	
	
	PatternFlop = re.compile("""^\*\*\*\sFLOP\s\*\*\*\s
	\[
		(?P<card1>[23456789TJQKA][cdhs])\s
		(?P<card2>[23456789TJQKA][cdhs])\s
		(?P<card3>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	
	)				
	@HHConfig.LineParserMethod(priority=200)
	def parsFlop(self, data, events):
		for item in data:
			m = self.PatternFlop.match(item['line'])
			if m is not None:
				d = m.groupdict()
				events[item['lineno']] = HHConfig.EventFlop(cards=(d['card1'], d['card2'], d['card3']))
				data.remove(item)
				break
	
	
	PatternTurn = re.compile("""^\*\*\*\sTURN\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	
	)				
	@HHConfig.LineParserMethod(priority=200)
	def parsTurn(self, data, events):
		for item in data:
			m = self.PatternTurn.match(item['line'])
			if m is not None:
				d = m.groupdict()
				events[item['lineno']] = HHConfig.EventTurn(card=d['card'])
				data.remove(item)
				break
	
	
	PatternRiver = re.compile("""^\*\*\*\sRIVER\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	
	)				
	@HHConfig.LineParserMethod(priority=200)
	def parsRiver(self, data, events):
		for item in data:
			m = self.PatternRiver.match(item['line'])
			if m is not None:
				d = m.groupdict()
				events[item['lineno']] = HHConfig.EventRiver(card=d['card'])
				data.remove(item)
				break
	
	
	
	PatternEmptyLine = re.compile('^\s*$')
	@HHConfig.LineParserMethod(priority=9999)
	def parseEmptyLines(self, data, events):
		items = []
		for item in data:
			if self.PatternEmptyLine.match(item['line']) is not None:
				items.append(item)	
		for item in items:
			data.remove(item)
	

if __name__ == '__main__':
	import cProfile as profile	
	from oo1 import hh
	hh = hh.split('\n')
	p = PokerStarsParserHoldemEN()
	for event in p.feed(hh):
		print event.toString()

	def test():
		for i in xrange(20000):
			for event in p.feed(hh):
				pass
				#print event.toString()

	##profile.run('test()')

	
