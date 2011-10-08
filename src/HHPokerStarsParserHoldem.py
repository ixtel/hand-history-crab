
import re
import HHConfig

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
			\#(?P<gameNo>\d+)\:\s\s
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
		""", re.X 
		)
	PatternTableHeader = re.compile(
		"""^Table\s \'(?P<tableName>[^\']+)\'\s
			(?P<maxPlayers>\d+)\-max\s
			Seat\s\#(?P<seatNoButton>\d+)\sis\sthe\sbutton
			\s*$
		""", re.X
		)
	
	@HHConfig.LineParserMethod(priority=1)
	def parseHandStart(self, data, events):
		if len(data) < 2:
			return
		event = HHConfig.EventHandStart()
		m = self.PatternGameHeaderCashGame.match(data[0]['line'])
		if m is None:
			return
		data.pop(0)
		m = self.PatternTableHeader.match(data[0]['line'])
		if m is None:
			return
		data.pop(0)
		d = m.groupdict()
		self._seatNoButton = int(d['seatNoButton'])
		events[0] = event
	
	
	PatternPlayer = re.compile(
		"""^Seat\s(?P<seatNo>\d+)\:\s
				(?P<name>.+?)\s
				\(
					[^\d\.]?(?P<stack>[\d\.]+)\sin\schips
				\)
				(?P<sitsOut>\s is\s sitting\s out)?
				\s*$
		""", re.X
		)
	PatternPlayerSitsOut = re.compile("""^(?P<name>.*?)\:\s (sits\s out | is\s sitting\s out)\s*$
		""", re.X
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
		""", re.X 
		)				
	@HHConfig.LineParserMethod(priority=50)
	def parsePlayerPostsSmallBlind(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerPostsSmallBlind.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerPostsSmallBlind(**m.groupdict())
		for item in items:
			data.remove(item)
		
	
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\sbig\sblind\s[^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X 
		)				
	@HHConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerPostsBigBlind.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerPostsBigBlind(**m.groupdict())
		for item in items:
			data.remove(item)
	
	
	PatternPlayerFolds = re.compile(
		"^(?P<name>.*?)\:\s folds\s*$", re.X
		)
	@HHConfig.LineParserMethod(priority=100)
	def parsePlayerFolds(self, data, events):
		items = []
		for item in data:
			m = self.PatternPlayerFolds.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerFolds(**m.groupdict())
		for item in items:
			data.remove(item)
		
	
	PatternEmptyLine = re.compile('^.*$')
	@HHConfig.LineParserMethod(priority=9999)
	def parseEmptyLines(self, lineBuffer, events):
		while lineBuffer:
			if self.PatternEmptyLine.match(lineBuffer.pop()['line']) is None:
				lineBuffer.push()	
		
	

if __name__ == '__main__':
	import cProfile as profile	
	from oo1 import hh
	hh = hh.split('\n')
	p = PokerStarsParserHoldemEN()
	for event in p.feed(hh):
		print event.toString()

	def test():
		for i in xrange(40000):
			for event in p.feed(hh):
				pass
				#print event.toString()

	##profile.run('test()')

	
