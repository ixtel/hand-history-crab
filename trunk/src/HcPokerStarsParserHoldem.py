import re
import HcConfig
import HcPokerStarsConfig
from HcLib.PokerTools import PtSeats


#TODO: stars did introduced currency a while ago. what to do with older hands?
#TODO:stars does not show ante in game header

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
	#PokerStars Game #53149898401: Tournament #334519833, 2000+110 Hold'em No Limit - Level I (10/20) - 2010/11/23 17:22:30 CET [2010/11/23 11:22:30 ET]
	PatternGameHeaderTourney = re.compile(
		"""^PokerStars\s Game\s
			\#(?P<handID>\d+)\:\s
			Tournament\s \#(?P<tourneyID>\d+),\s
			[^\d\.]?(?P<tourneyBuyIn>[\d\.]+)\+[^\d\.]?(?P<tourneyRake>[\d\.]+)\s
			((?P<currency>[A-Z]+)\s)?
			(?P<game>Hold\'em)\s
			(?P<gameLimit>No\sLimit)\s
			\-\s Level\s[IVXLCDM]+\s
			\(
				[^\d\.]?(?P<smallBlind>[\d\.]+)\/
				[^\d\.]?(?P<bigBlind>[\d\.]+)
				\s?
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
		if m is not None:
			d = m.groupdict()
		if m is None:
			m = self.PatternGameHeaderTourney.match(data[0]['line'])
			if m is not None:
				d = m.groupdict()
				d['tourneyBuyIn'] = float(d['tourneyBuyIn'])
				d['tourneyRake'] = float(d['tourneyRake'])
		if m is None:
			return False
		data.pop(0)
		
		m = self.PatternTableHeader.match(data[0]['line'])
		if m is None:
			return False
		data.pop(0)
		d.update(m.groupdict())
		self._seatNoButton = int(d.pop('seatNoButton'))
		d['site'] = self.site()
		d['game'] = HcPokerStarsConfig.GameMapping[d['game']]
		d['gameLimit'] = HcPokerStarsConfig.GameLimitMapping[d['gameLimit']]
		currency = '' if d['currency'] is None else d['currency']
		d['currency'] = HcPokerStarsConfig.CurrencyMapping[currency]
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
		return True
	
	
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
	PatternPlayerSitsOut = re.compile(
	"""^(?P<name>.*?)\:?\s (sits\s out | is\s sitting\s out)\s*$""", 
	re.X|re.I
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
					handlers[item['lineno']] = (self.hand.handlePlayer, d)
				else:
					#TODO: report to hand?
					handlers[item['lineno']] = (self.hand.handlePlayerSitsOut, d)
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#playerXYZ will be allowed to play after the button
	PatternPlayerAllowedToPlay = re.compile(
		"""^(?P<name>.*?)\s will\s be\s allowed\s to\s play\s .* \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=40)
	def parsePlayerPlayerAllowedToPlay(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerAllowedToPlay.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	PatternPlayerPostsSmallBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s blind\s [^\d\.]?(?P<amount>[\d\.]+)\s*$
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
		return True
			
	
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s big\s blind\s [^\d\.]?(?P<amount>[\d\.]+)\s*$
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
		return True
	
	
	PatternPlayerPostsAnte = re.compile(
		"""^(?P<name>.*?)\:\sposts\s the\s ante\s [^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostAnte(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerPostsAnte.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerPostsAnte, d)
		for item in items:
			data.remove(item)
		return True
	
	
	
	#TODO: report amount total or small/big blind?
	PatternPlayerPostsBuyIn = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s &\s big\s blinds\s [^\d\.]?(?P<amount>[\d\.]+)\s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBuyIn(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerPostsBuyIn.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handlePlayerPostsBuyIn, d)
		for item in items:
			data.remove(item)
		return True
		
	
	PatternPreflop = re.compile("""^^\*\*\*\sHOLE\sCARDS\s\*\*\*$\s*$""")				
	@HcConfig.LineParserMethod(priority=100)
	def parsePreflop(self, data, handlers):
		for item in data:
			m = self.PatternPreflop.match(item['line'])
			if m is not None:
				handlers[item['lineno']] = (self.hand.handlePreflop, {})
				data.remove(item)
				break
		return True
		
		
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
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				handlers[item['lineno']] = (self.hand.handlePlayerHoleCards, d)
				data.remove(item)
				break
		return True
	
	
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
		return True
	
	
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
		return True
				
	
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
		return True
		
	
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
		return True
	
	
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
		return True
	
	
	#TODO: pass to hand?
	PatternPlayerBustedTourney = re.compile(
		"^(?P<name>.*?)\s finished\s the\s tournament\s in\s .* \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerBustedTourney(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerBustedTourney.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: convert text to unicode?
	PatternPlayerChats = re.compile(
		"^(?P<name>.*?)\s said,\s \"(?P<text>.*)\" \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerChats(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerChats.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				handlers[item['lineno']] = (self.hand.handlePlayerChats, d)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerDisconnected = re.compile(
		"^(?P<name>.*?)\s is\s disconnected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerDisconnected(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerDisconnected.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerReconnects = re.compile(
		"^(?P<name>.*?)\s is\s connected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerReconnects(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerReconnects.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerTimedOut = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerTimedOut(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerTimedOut.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerReturns = re.compile(
		"^(?P<name>.*?)\s has\s returned \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerReturns(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerReturns.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerTimedOutWhileDisconnected = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out\s while\s (being\s)? disconnected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerTimedOutWhileDisconnected(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerTimedOutWhileDisconnected.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	#TODO: pass to hand or not? player removed for missing blinds
	# "player" was removed from the table for failing to post
	PatternPlayerRemoved = re.compile(
		"^(?P<name>.*?)\s was\s removed\s from\s the\s table\s .* \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerRemoved(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerRemoved.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
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
				d['cards'] = (d.pop('card1'), d.pop('card2'), d.pop('card3'))
				handlers[item['lineno']] = (self.hand.handleFlop, d)
				data.remove(item)
				break
		return True
	
	
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
				handlers[item['lineno']] = (self.hand.handleTurn, d)
				data.remove(item)
				break
		return True
	
	
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
				handlers[item['lineno']] = (self.hand.handleRiver, d)
				data.remove(item)
				break
		return True
		
		
	PatternShowDown = re.compile("""^^\*\*\*\sSHOW\sDOWN\s\*\*\*\s*$""")				
	@HcConfig.LineParserMethod(priority=300)
	def parseShowDown(self, data, handlers):
		for item in data:
			m = self.PatternShowDown.match(item['line'])
			if m is not None:
				handlers[item['lineno']] = (self.hand.handleShowDown, {})
				data.remove(item)
				break
		return True
	
	
	PatternPlayerShows = re.compile(
		"""^(?P<name>.*?)\:\s shows\s 
		\[
			(?P<card1>[23456789TJQKA][cdhs])\s 
			(?P<card2>[23456789TJQKA][cdhs])
		\]\s
		\(.+\)\s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerShows(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerShows.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				handlers[item['lineno']] = (self.hand.handlePlayerShows, d)
		for item in items:
			data.remove(item)
		return True
	
		
	PatternPlayerMucks = re.compile(
		"^(?P<name>.*?)\:\s mucks\s hand\s*$", re.X|re.I
		)
	#NOTE: funny enough, stars reports "(button) (small blind)" in heads up pots
	PatternPlayerMucked = re.compile(
		"""^Seat\s [\d]+\:\s (?P<name>.+?)\s 
		\(button\)? (\((small\sblind|big\sblind|button)\)\s)? 
		mucked\s \[(?P<card1>[23456789TJQKA][cdhs])\s(?P<card2>[23456789TJQKA][cdhs])\]
		\s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerMucks(self, data, handlers):
		items = []
		players = {}
		for item in data:
			m = self.PatternPlayerMucks.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['cards'] = None
				players[d['name']] = (d, item['lineno'])
		for item in items:
			data.remove(item)
			
		# try to find hole cards player mucked
		items = []
		for item in data:
			m = self.PatternPlayerMucked.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				players[d['name']][0]['cards'] = (d.pop('card1'), d.pop('card2'))
		for item in items:
			data.remove(item)
			
		for name, (d, lineno) in players.items():
			handlers[item['lineno']] = (self.hand.handlePlayerMucks, d)
		return True	
		
		
	PatternPlayerCollected = re.compile(
		"^(?P<name>.*?)\s collected\s [^\d\.]?(?P<amount>[\d\.]+)\s from\s (?P<pot>(pot | main\s pot | side\s pot)) \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=400)
	def parsePlayerWins(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerCollected.match(item['line'])
			if m is not None:
				items.append(item)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				pot = d.pop('pot').lower()
				#TODO: side pot number?
				if pot == 'pot':
					d['potNo'] = 0
				elif pot == 'main pot':
					d['potNo'] = 0
				elif pot == 'side pot':
					d['potNo'] = 1
				else:
					return False
				handlers[item['lineno']] = (self.hand.handlePlayerWins, d)
		for item in items:
			data.remove(item)
		return True
				
	
	#TODO: stars does not put names in quotes. no idea if player names may end with spaces.
	# if so we are in trouble here. there is no way to tell "player\s" apart from "player\s\s",
	# even if we keep a lokkup of player names. hope stars has done the right thing.
	PatternUncalledBet = re.compile(
		"^Uncalled\s bet\s \([^\d\.]?(?P<amount>[\d\.]+)\)\s returned\s to\s (?P<name>.*?) \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=400)
	def parseUncalledBet(self, data, handlers):
		for item in data:
			m = self.PatternUncalledBet.match(item['line'])
			if m is not None:
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				handlers[item['lineno']] = (self.hand.handleUncalledBet, d)
				data.remove(item)
				# logic says there can only be one uncalled bet per hand
				break
		return True
		
	
	PatternPlayerDoesNotShowHand = re.compile(
		"""^(?P<name>.*?)\:\s doesn\'t\s show\s  hand \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerDoesNotShowHand(self, data, handlers):
		for item in data:
			m = self.PatternPlayerDoesNotShowHand.match(item['line'])
			if m is not None:
				data.remove(item)
				# logic says there can only be one "player does not show hand" per hand
				break
		return True
		
	
	PatternPlayerLeavesTable = re.compile(
		"""^(?P<name>.*?)\s leaves\s the\s table \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerLeavesTable(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerLeavesTable.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True	
	
	
	PatternPlayerJoinsTable = re.compile(
		"""^(?P<name>.*?)\s joins\s the\s table\s at\s seat\s \#\d+ \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerJoinsTable(self, data, handlers):
		items = []
		for item in data:
			m = self.PatternPlayerJoinsTable.match(item['line'])
			if m is not None:
				items.append(item)
		for item in items:
			data.remove(item)
		return True
	
	
	
	# clean up handlers
		
	PatternSummary = re.compile("""^^\*\*\*\sSUMMARY\s\*\*\*\s*$""")				
	@HcConfig.LineParserMethod(priority=9998)
	def parseSummary(self, data, handlers):
		for i, item in enumerate(data):
			m = self.PatternSummary.match(item['line'])
			if m is not None:
				# drop summary, we don't need it
				while i < len(data):
					data.pop(i)
				break	
		return True
	
		
	PatternEmptyLine = re.compile('^\s*$')
	@HcConfig.LineParserMethod(priority=9999)
	def parseEmptyLines(self, data, handlers):
		items = []
		for item in data:
			if self.PatternEmptyLine.match(item['line']) is not None:
				items.append(item)	
		for item in items:
			data.remove(item)
		return True
	

if __name__ == '__main__':
	import cProfile as profile	
	from oo1 import hh
	hh = hh.split('\n')
	p = PokerStarsParserHoldemEN(hand=HcConfig.HandHoldemDebug())
	hand = p.feed(hh)

	def test():
		for i in xrange(20000):
			hand = p.feed(hh)
			
			

	##profile.run('test()')

	