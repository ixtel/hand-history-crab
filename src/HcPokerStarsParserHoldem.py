import re
import HcConfig
import HcPokerStarsConfig
from HcLib.PokerTools import PtSeats
from HcLib.PokerTools import PtCard

#NOTES:
#
# PokerStars rake (thanks PokerStars nick): 
# -----------------------------------------
# pot total gives the rake to be taken, according to [http://www.pokerstars.com/poker/room/rake/].
# rake is then taken from each pot (starting from  the main pot) when the threshold is hit.
#
# example - assume 1c for each 20c (threshold) in the pot:
# mainPot = 14
# sidePot1 = 20
# sidePot2 = 66
# total = 100
# rake = 5
#
# * mainPot does not hit the threshold so 0c are taken (remainder 14c)
# * the first 6c of sidePot1 hit the threshold of 20c so 1c is taken (remainder 14c)
# * the first 6c of sidePot 2 hit the threshold so 1c is taken and there are 60c left
#   in the pot that are raked with 3c.
#
# so mainPot is raked 0c, sidePot1 1c and sidePot2 4c.
#
#************************************************************************************
# consts
#************************************************************************************
HcPokerStarsConfig.GameMapping = {
		"Hold'em": HcConfig.GameHoldem,
		}

HcPokerStarsConfig.GameLimitMapping = {
		"No Limit": HcConfig.GameLimitNoLimit,
		}

HcPokerStarsConfig.CurrencyMapping = {
		'USD': HcConfig.CurrencyDollar,
		}
	

#************************************************************************************
# parser implementation
#************************************************************************************
class PokerStarsParserHoldemEN(HcConfig.LineParserBase):
	
	Site = HcConfig.SitePokerStars
	Game = HcConfig.GameHoldem
	Language = HcConfig.LanguageEN
		
	def __init__(self, *args, **kws):
		HcConfig.LineParserBase.__init__(self, *args, **kws)
		self._seatNoButton = 0
	
	def feed(self, *args, **kws):
		self._seatNoButton = 0
		return HcConfig.LineParserBase.feed(self, *args, **kws)
		
	def stringToFloat(self, amount):
		return float(amount)
		
	#TODO: tourneyID
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
	
	@HcConfig.LineParserMethod(priority=1)
	def parseHandStart(self, data, handlers):
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
		d['site'] = self.site()
		d['game'] = HcPokerStarsConfig.GameMapping[d['game']]
		d['gameLimit'] = HcPokerStarsConfig.GameLimitMapping[d['gameLimit']]
		d['currency'] = HcPokerStarsConfig.CurrencyMapping[d['currency']]
		d['bigBlind'] = self.stringToFloat(d['bigBlind'])
		d['smallBlind'] = self.stringToFloat(d['smallBlind'])
		d['maxPlayers'] = int(d['maxPlayers'])
		d['timestamp'] = HcConfig.timestampFromDate(
								HcConfig.TimeZoneET,
								d.pop('year'), 
								d.pop('month'), 
								d.pop('day'), 
								d.pop('hour'), 
								d.pop('minute'), 
								d.pop('second'), 
								)
		handlers[0] = (self.hand.handleHandStart, d)
	
	
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
	@HcConfig.LineParserMethod(priority=10)
	def parsePlayer(self, data, handlers):
		
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
			players.append(d)
			playerNames.append(d['name'])
			handlers[item['lineno']] = (self.hand.handlePlayer, d)
		for item in items:
			data.remove(item)
		
		# determine seat names
		players =  players[self._seatNoButton-1:] + players[:self._seatNoButton-1]
		for buttonOrder, seatName in enumerate(PtSeats.Seats.SeatNames[len(players)]):
			player = players[buttonOrder]
			player['seatName'] = seatName
			player['buttonOrder'] = buttonOrder +1
				
		# find all players sitting out
		items = []
		for item in data:
			m = self.PatternPlayerSitsOut.match(item['line'])
			if m is not None:
				d = m.groupdict()
				if d['name'] not in playerNames:
					# assume cash game (see notes above)
					d['sitsOut'] = True
					handlers[item['lineno']] = (self.handHandlePlayer, d)
					items.append(item)
				else:
					handlers[item['lineno']] = (self.handHandlePlayerSitsOut, d)
		for item in items:
			data.remove(item)
	
	
	PatternPlayerPostsSmallBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\ssmall\sblind\s[^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=45)
	def parsePlayerPostsSmallBlind(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerPostsSmallBlind.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerPostsSmallBlind, d)
				break
		for item in items:
			data.remove(item)
			
	
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\sbig\sblind\s[^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerPostsBigBlind.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerPostsBigBlind, d)
		for item in items:
			data.remove(item)
	
	
	PatternPreflop = re.compile("""^^\*\*\*\sHOLE\sCARDS\s\*\*\*$\s*$""")				
	@HcConfig.LineParserMethod(priority=100)
	def parsePreflop(self, data, handlers):
		for item in data:
			m = self.PatternPreflop.match(item['line'])
			if m is not None:
				handlers[item['lineno']] = (self.hand.handlePreflop, {})
				data.remove(item)
				break
		
	PatternPlayerHoleCards = re.compile(
		"^Dealt\s to\s (?P<name>.*?)\s \[(?P<card1>[23456789TJQKA][cdhs])\s(?P<card2>[23456789TJQKA][cdhs])\]\s*$", 
		re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=150)
	def parsePlayerPlayerHoleCards(self, data, handlers):
		for item in data:
			m = self.PatternPlayerHoleCards.match(item['line'])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (PtCard.Card(d.pop('card1')), PtCard.Card(d.pop('card2')))
				handlers[item['lineno']] = (self.hand.handlePlayerHoleCards, d)
				data.remove(item)
				break
	
	
	PatternPlayerChecks = re.compile(
		"^(?P<name>.*?)\:\s checks\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerChecks(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerChecks.match(item['line'])
			if m is not None:
				items.append(item)
				handlers[item['lineno']] = (self.hand.handlePlayerChecks, m.groupdict())
		for item in items:
			data.remove(item)
	
	
	PatternPlayerFolds = re.compile(
		"^(?P<name>.*?)\:\s folds\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerFolds(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerFolds.match(item['line'])
			if m is not None:
				items.append(item)
				handlers[item['lineno']] = (self.hand.handlePlayerFolds, m.groupdict())
		for item in items:
			data.remove(item)
				
	
	PatternPlayerBets = re.compile(
		"^(?P<name>.*?)\:\s bets\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerBets(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerBets.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerBets, d)
		for item in items:
			data.remove(item)
		
	
	PatternPlayerRaises = re.compile(
		"^(?P<name>.*?)\:\s raises\s .*? to\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerRaises(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerRaises.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerRaises, d)
		for item in items:
			data.remove(item)
	
	
	PatternPlayerCalls = re.compile(
		"^(?P<name>.*?)\:\s calls\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerCalls(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerCalls.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerCalls, d)
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
	@HcConfig.LineParserMethod(priority=200)
	def parsFlop(self, data, handlers):
		for item in data:
			m = self.PatternFlop.match(item['line'])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (
						PtCard.Card(d.pop('card1')), 
						PtCard.Card(d.pop('card2')), 
						PtCard.Card(d.pop('card3'))
						)
				handlers[item['lineno']] = (self.hand.handleFlop, d)
				data.remove(item)
				break
	
	
	PatternTurn = re.compile("""^\*\*\*\sTURN\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	)				
	@HcConfig.LineParserMethod(priority=200)
	def parsTurn(self, data, handlers):
		for item in data:
			m = self.PatternTurn.match(item['line'])
			if m is not None:
				d = m.groupdict()
				d['card'] = PtCard.Card(d['card'])
				handlers[item['lineno']] = (self.hand.handleTurn, d)
				data.remove(item)
				break
	
	
	PatternRiver = re.compile("""^\*\*\*\sRIVER\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	)				
	@HcConfig.LineParserMethod(priority=200)
	def parsRiver(self, data, handlers):
		for item in data:
			m = self.PatternRiver.match(item['line'])
			if m is not None:
				d = m.groupdict()
				d['card'] = PtCard.Card(d['card'])
				handlers[item['lineno']] = (self.hand.handleRiver, d)
				data.remove(item)
				break
	
	PatternShowDown = re.compile("""^^\*\*\*\sSHOW\sDOWN\s\*\*\*\s*$""")				
	@HcConfig.LineParserMethod(priority=300)
	def parseShowDown(self, data, handlers):
		for item in data:
			m = self.PatternShowDown.match(item['line'])
			if m is not None:
				handlers[item['lineno']] = (self.hand.handleShowDown, {})
				data.remove(item)
				break
	
	
	
	
	PatternEmptyLine = re.compile('^\s*$')
	@HcConfig.LineParserMethod(priority=9999)
	def parseEmptyLines(self, data, handlers):
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
	p = PokerStarsParserHoldemEN(HcConfig.HandHoldemDebug())
	hand = p.feed(hh)

	def test():
		for i in xrange(20000):
			hand = p.feed(hh)
			
			

	##profile.run('test()')

	
