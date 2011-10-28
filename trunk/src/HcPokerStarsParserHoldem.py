 # -*- coding: UTF-8 -*-

import re
import HcConfig
from HcLib.PokerTools import PtSeats


#TODO: stars did introduced currency a while ago. what to do with older hands?
#TODO:stars does not show ante in game header
#TODO: seen player buying in posting 1) BB 2) SB 3) BB + SB have to check this
#      and add a eventHandler to Hand() ..something like handlePlayerBuysIn(). 

#************************************************************************************
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
#************************************************************************************
# consts
#************************************************************************************
CurrencySymbols = u'$€£'

GameMapping = {
		"Hold'em": HcConfig.GameHoldem,
		}

GameLimitMapping = {
		"no limit": HcConfig.GameLimitNoLimit,
		"pot limit": HcConfig.GameLimitPotLimit,
		"fixed limit": HcConfig.GameLimitFixedLimit,
		}

CurrencyMapping = {
		'': HcConfig.CurrencyNone,
		'$': HcConfig.CurrencyUSD,
		u'€': HcConfig.CurrencyEUR,
		u'£':  HcConfig.CurrencyGBP,
		
		}



#************************************************************************************
# parser implementation
#************************************************************************************
class PokerStarsParserHoldemENCashGame2(HcConfig.LineParserBase):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='2',
			)
			
	def __init__(self, *args, **kws):
		HcConfig.LineParserBase.__init__(self, *args, **kws)
		self._seatNoButton = 0
		
	def feed(self, *args, **kws):
		self._seatNoButton = 0
		return HcConfig.LineParserBase.feed(self, *args, **kws)
		
	def stringToFloat(self, amount):
		return float(amount)
		
	# PokerStars Home Game #0123456789: {HomeGameName}  Hold'em No Limit ($0.00/$0.00 USD) - 0000/00/00 00:00:00 TZ [0000/00/00 00:00:00 TZ]
	# PokerStars Home Game #0123456789: Hold'em No Limit ($0.00/$0.00 USD) - 0000/00/00 00:00:00 TZ [0000/00/00 00:00:00 TZ]
	PatternGameHeader = re.compile(
		"""^PokerStars\s Game \s
			\#(?P<handID>\d+)\:\s+
			(?P<game>Hold\'em)\s
			(?P<gameLimit>(No\sLimit|Pot\sLimit|Fixed\sLimit))\s
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
			(\(Play\s Money\)\s)?
			Seat\s\#(?P<seatNoButton>\d+)\sis\sthe\sbutton
			\s*$
		""", re.X|re.I
		)
	
	@HcConfig.LineParserMethod(priority=1)
	def parseGameHeader(self, lines, eventHandler, events):
		if len(lines) < 2:
			return False
		
		
		m = self.PatternGameHeader.match(lines[0]['chars'])
		if m is None:
			return False
		d = m.groupdict()
		m = self.PatternTableHeader.match(lines[1]['chars'])
		if m is None:
			lines.pop(0)
			return False
		d.update(m.groupdict())
		
		self._seatNoButton = int(d.pop('seatNoButton'))
		d['site'] = self.ID['site']
		d['game'] = GameMapping[d['game']]
		d['gameLimit'] = GameLimitMapping[d['gameLimit'].lower()]
		#NOTE: stars added currency to header at some point, but this is pretty useless
		# for parsing old hand histories, so we parse currency symbols directly
		line = lines[0]['chars']
		currency = CurrencyMapping['']
		for symbol in CurrencySymbols:
			if symbol in line:
				currency = CurrencyMapping[symbol]
				break
		d['currency'] = currency
		d['bigBlind'] = self.stringToFloat(d['bigBlind'])
		d['smallBlind'] = self.stringToFloat(d['smallBlind'])
		d['maxPlayers'] = int(d['maxPlayers'])
		d['time'] = HcConfig.timeFromDate(
								(int(d.pop('year')), 
								int(d.pop('month')), 
								int(d.pop('day')), 
								int(d.pop('hour')), 
								int(d.pop('minute')), 
								int(d.pop('second'))),
								timeZone=HcConfig.TimeZoneET, 
								)
		
		lines.pop(0)
		lines.pop(0)
		events[0] = (eventHandler.handleHandStart, d)
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
	def parsePlayer(self, lines, eventHandler, events):
		
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
		oldLines = []
		players = []
		playerNames = []
		for line in lines:
			m = self.PatternPlayer.match(line['chars'])
			if m is None:
				#NOTE: we can not break here because other formats may have other player flags
				continue
			oldLines.append(line)
			d = m.groupdict()
			d['seatNo'] = int(d['seatNo'])
			d['stack'] = self.stringToFloat(d['stack'])
			d['sitsOut'] = bool(d['sitsOut'])
			players.append(d)
			playerNames.append(d['name'])
			events[line['index']] = (eventHandler.handlePlayer, d)
			#NOTE: we can handle only so much players, so let ParserBase deal with remainder
			if len(players) > len(PtSeats.Seats.SeatNames):
				break
		for line in oldLines:
			lines.remove(line)
				
		# determine seat names
		players =  players[self._seatNoButton-1:] + players[:self._seatNoButton-1]
		for buttonOrder, seatName in enumerate(PtSeats.Seats.SeatNames[len(players)]):
			player = players[buttonOrder]
			player['seatName'] = seatName
			player['buttonOrder'] = buttonOrder +1
				
		# find all players sitting out
		oldLines = []
		for line in lines:
			m = self.PatternPlayerSitsOut.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				if d['name'] not in playerNames:
					# assume cash game (see notes above)
					d['sitsOut'] = True
					events[line['index']] = (eventHandler.handlePlayer, d)
				else:
					#TODO: report to hand?
					events[line['index']] = (eventHandler.handlePlayerSitsOut, d)
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#playerXYZ will be allowed to play after the button
	PatternPlayerAllowedToPlay = re.compile(
		"""^(?P<name>.*?)\s will\s be\s allowed\s to\s play\s .* \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=40)
	def parsePlayerPlayerAllowedToPlay(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerAllowedToPlay.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: for some strange reason found a HH where a player posts only the small blinds
	# guess buy in rules have changed at some point
	PatternPlayerPostsSmallBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s blind\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=45)
	def parsePlayerPostsSmallBlind(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerPostsSmallBlind.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerPostsSmallBlind, d)
		for line in oldLines:
			lines.remove(line)
		return True
			
	
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s big\s blind\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerPostsBigBlind.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerPostsBigBlind, d)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	PatternPlayerPostsAnte = re.compile(
		"""^(?P<name>.*?)\:\sposts\s the\s ante\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostAnte(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerPostsAnte.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerPostsAnte, d)
		for line in oldLines:
			lines.remove(line)
		return True
		
	
	#TODO: report amount total or small/big blind?
	PatternPlayerPostsBuyIn = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s &\s big\s blinds\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBuyIn(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerPostsBuyIn.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerPostsBuyIn, d)
		for line in oldLines:
			lines.remove(line)
		return True
		
	
	PatternPreflop = re.compile("""^^\*\*\*\sHOLE\sCARDS\s\*\*\*$\s*$""")				
	@HcConfig.LineParserMethod(priority=100)
	def parsePreflop(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternPreflop.match(line['chars'])
			if m is not None:
				events[line['index']] = (eventHandler.handlePreflop, {})
				lines.remove(line)
				break
		return True
		
		
	PatternPlayerHoleCards = re.compile(
		"^Dealt\s to\s (?P<name>.*?)\s \[(?P<card1>[23456789TJQKA][cdhs])\s(?P<card2>[23456789TJQKA][cdhs])\]\s*$", 
		re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=150)
	def parsePlayerPlayerHoleCards(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternPlayerHoleCards.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				events[line['index']] = (eventHandler.handlePlayerHoleCards, d)
				lines.remove(line)
				break
		return True
	
	
	PatternPlayerChecks = re.compile(
		"^(?P<name>.*?)\:\s checks\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerChecks(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerChecks.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				events[line['index']] = (eventHandler.handlePlayerChecks, m.groupdict())
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	PatternPlayerFolds = re.compile(
		"^(?P<name>.*?)\:\s folds\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerFolds(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerFolds.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				events[line['index']] = (eventHandler.handlePlayerFolds, m.groupdict())
		for line in oldLines:
			lines.remove(line)
		return True
				
	
	PatternPlayerBets = re.compile(
		"^(?P<name>.*?)\:\s bets\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)? \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerBets(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerBets.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerBets, d)
		for line in oldLines:
			lines.remove(line)
		return True
		
	
	PatternPlayerRaises = re.compile(
		"^(?P<name>.*?)\:\s raises\s .*? to\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerRaises(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerRaises.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerRaises, d)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	PatternPlayerCalls = re.compile(
		"^(?P<name>.*?)\:\s calls\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerCalls(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerCalls.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handlePlayerCalls, d)
		for line in oldLines:
			lines.remove(line)
		return True
	
	#TODO: convert text to unicode?
	PatternPlayerChats = re.compile(
		"^(?P<name>.*?)\s said,\s \"(?P<text>.*)\" \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerChats(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerChats.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				events[line['index']] = (eventHandler.handlePlayerChats, d)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerDisconnected = re.compile(
		"^(?P<name>.*?)\s is\s disconnected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerDisconnected(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerDisconnected.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerReconnects = re.compile(
		"^(?P<name>.*?)\s is\s connected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerReconnects(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerReconnects.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerTimedOut = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerTimedOut(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerTimedOut.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerReturns = re.compile(
		"^(?P<name>.*?)\s has\s returned \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerReturns(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerReturns.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not?
	PatternPlayerTimedOutWhileDisconnected = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out\s while\s (being\s)? disconnected \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerTimedOutWhileDisconnected(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerTimedOutWhileDisconnected.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
	
	#TODO: pass to hand or not? player removed for missing blinds
	# "player" was removed from the table for failing to post
	PatternPlayerRemoved = re.compile(
		"^(?P<name>.*?)\s was\s removed\s from\s the\s table\s .* \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerRemoved(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerRemoved.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
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
	def parsFlop(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternFlop.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'), d.pop('card3'))
				events[line['index']] = (eventHandler.handleFlop, d)
				lines.remove(line)
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
	def parsTurn(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternTurn.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				events[line['index']] = (eventHandler.handleTurn, d)
				lines.remove(line)
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
	def parsRiver(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternRiver.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				events[line['index']] = (eventHandler.handleRiver, d)
				lines.remove(line)
				break
		return True
		
		
	PatternShowDown = re.compile("""^^\*\*\*\sSHOW\sDOWN\s\*\*\*\s*$""")				
	@HcConfig.LineParserMethod(priority=300)
	def parseShowDown(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternShowDown.match(line['chars'])
			if m is not None:
				events[line['index']] = (eventHandler.handleShowDown, {})
				lines.remove(line)
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
	def parsePlayerShows(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerShows.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				events[line['index']] = (eventHandler.handlePlayerShows, d)
		for line in oldLines:
			lines.remove(line)
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
	def parsePlayerMucks(self, lines, eventHandler, events):
		oldLines = []
		players = {}
		for line in lines:
			m = self.PatternPlayerMucks.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['cards'] = None
				players[d['name']] = (d, line['index'])
		for line in oldLines:
			lines.remove(line)
			
		# try to find hole cards player mucked
		oldLines = []
		for line in lines:
			m = self.PatternPlayerMucked.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				players[d['name']][0]['cards'] = (d.pop('card1'), d.pop('card2'))
		for line in oldLines:
			lines.remove(line)
			
		for name, (d, lineno) in players.items():
			events[line['index']] = (eventHandler.handlePlayerMucks, d)
		return True	
		
		
	PatternPlayerCollected = re.compile(
		"""^(?P<name>.*?)\s collected\s [^\d\.]?(?P<amount>[\d\.]+)\s from\s 
		(?P<pot>(
			pot |
			main\s pot |
			side\s pot(\-(?P<potNo>[\d])+)?)
		) \s*$""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=400)
	def parsePlayerWins(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerCollected.match(line['chars'])
			if m is not None:
				oldLines.append(line)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				pot = d.pop('pot').lower()
				#TODO: side pot number?
				if pot == 'pot':
					d['potNo'] = 0
				elif pot == 'main pot':
					d['potNo'] = 0
				elif pot.startswith('side pot'):
					d['potNo'] = 1 if d['potNo'] is None else int(d['potNo'])
				else:
					# clear lines up to err line
					while lines:
						if lines[0]['lineno'] < line['index']:
							lines.pop(0)
					return False
				events[line['index']] = (eventHandler.handlePlayerWins, d)
		for line in oldLines:
			lines.remove(line)
		return True
				
	
	#TODO: stars does not put names in quotes. no idea if player names may end with spaces.
	# if so we are in trouble here. there is no way to tell "player\s" apart from "player\s\s",
	# even if we keep a lokkup of player names. hope stars has done the right thing.
	PatternUncalledBet = re.compile(
		"^Uncalled\s bet\s \([^\d\.]?(?P<amount>[\d\.]+)\)\s returned\s to\s (?P<name>.*?) \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=400)
	def parseUncalledBet(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternUncalledBet.match(line['chars'])
			if m is not None:
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line['index']] = (eventHandler.handleUncalledBet, d)
				lines.remove(line)
				# logic says there can only be one uncalled bet per hand
				break
		return True
		
	
	PatternPlayerDoesNotShowHand = re.compile(
		"""^(?P<name>.*?)\:\s doesn\'t\s show\s  hand \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerDoesNotShowHand(self, lines, eventHandler, events):
		for line in lines:
			m = self.PatternPlayerDoesNotShowHand.match(line['chars'])
			if m is not None:
				lines.remove(line)
				# logic says there can only be one "player does not show hand" per hand
				break
		return True
		
	
	PatternPlayerLeavesTable = re.compile(
		"""^(?P<name>.*?)\s leaves\s the\s table \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerLeavesTable(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerLeavesTable.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True	
	
	
	PatternPlayerJoinsTable = re.compile(
		"""^(?P<name>.*?)\s joins\s the\s table\s at\s seat\s \#\d+ \s*$
		""", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=450)
	def parsePlayerJoinsTable(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerJoinsTable.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
		
	# clean up events
		
	PatternSummary = re.compile("""^^\*\*\*\sSUMMARY\s\*\*\*\s*$""")				
	@HcConfig.LineParserMethod(priority=9998)
	def parseSummary(self, lines, eventHandler, events):
		for i, line in enumerate(lines):
			m = self.PatternSummary.match(line['chars'])
			if m is not None:
				# drop summary, we don't need it
				while i < len(lines):
					lines.pop(i)
				break	
		return True
	
		
	PatternEmptyLine = re.compile('^\s*$')
	@HcConfig.LineParserMethod(priority=9999)
	def parseEmptyLines(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			if self.PatternEmptyLine.match(line['chars']) is not None:
				oldLines.append(line)	
		for line in oldLines:
			lines.remove(line)
		return True

#************************************************************************************
#
#************************************************************************************
class PokerStarsParserHoldemENCashGameHomeGame2(PokerStarsParserHoldemENCashGame2):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopeHomeGame,
			site=HcConfig.SitePokerStars,
			version='2',
			)
	
	PatternGameHeader = re.compile(
		"""^PokerStars\s Home\s Game\s
			\#(?P<handID>\d+)\:\s+
			\{(?P<homeGameID>.+?)\}\s+
			(?P<game>Hold\'em)\s
			(?P<gameLimit>(No\sLimit|Pot\sLimit|Fixed\sLimit))\s
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
		""", re.X|re.I)
		
#************************************************************************************
#
#************************************************************************************
# older header - no local date/time in header
class PokerStarsParserHoldemENCashGame1(PokerStarsParserHoldemENCashGame2):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='1',
			) 
		
	# PokerStars Game #0123456789:  Hold'em No Limit ($0.00/$0.00) - 0000/00/00 00:00:00 TZ
	PatternGameHeader = re.compile(
		"""^PokerStars\s Game\s
			\#(?P<handID>\d+)\:\s+
			(?P<game>Hold\'em)\s
			(?P<gameLimit>(No\sLimit|Pot\sLimit|Fixed\sLimit))\s
			\(
				[^\d\.]?(?P<smallBlind>[\d\.]+)\/
				[^\d\.]?(?P<bigBlind>[\d\.]+)
			\)
			\s-\s
			(?P<year>\d+)\/
			(?P<month>\d+)\/
			(?P<day>\d+)\s
			(?P<hour>\d+)\:
			(?P<minute>\d+)\:
			(?P<second>\d+)
			.+\s*$""", re.X|re.I
		)
	

#************************************************************************************
#
#************************************************************************************
#TODO: home game tourneys

class PokerStarsParserHoldemENTourney2(PokerStarsParserHoldemENCashGame1):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextTourney,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='2',
			)
	
	#PokerStars Game #0123456789: Tournament #0123456789, 0000+000 Hold'em No Limit - Level I (10/20) - 0000/00/00 00:00:00 TZ [0000/00/00 00:00:00 TZ]
	#PokerStars Game #0123456789: Tournament #0123456789, $0.00+$0.00 USD Hold'em No Limit - Match Round I, Level I (10/20) - 0000/00/00 0:00:00 TZ [0000/00/00 0:00:00 TZ]
	PatternGameHeader = re.compile(
		"""^PokerStars\s Game\s
			\#(?P<handID>\d+)\:\s
			Tournament\s \#(?P<tourneyID>\d+),\s
			(?P<tourneyBuyInType>	
				(
					[^\d\.]?(?P<tourneyBuyIn>[\d\.]+)\+
					[^\d\.]?(?P<tourneyRake>[\d\.]+)
					(\+[^\d\.]? (?P<tourneyBounty>[\d\.]+) )?
					(\s(?P<currency>[A-Z]+))?
				)
				|
				Freeroll
			)\s+
			(?P<game>Hold\'em)\s
			(?P<gameLimit>No\sLimit)\s
			\-\s+ 
			(Match\s Round\s [IVXLCDM]+, \s)?
			Level\s[IVXLCDM]+\s
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
	
	@HcConfig.LineParserMethod(priority=1)
	def parseGameHeader(self, lines, eventHandler, events):
		if not PokerStarsParserHoldemENCashGame1.parseGameHeader(self, lines, eventHandler, events):
			return False
				
		d = events[0][1]
		tourneyBuyInType = d.pop('tourneyBuyInType').lower()
		if tourneyBuyInType == 'freeroll':
			d['tourneyBuyIn'] = 0,0171
			d['tourneyRake'] = 0.0
		else:
			d['tourneyBuyIn'] = self.stringToFloat(d['tourneyBuyIn'])
			d['tourneyRake'] = self.stringToFloat(d['tourneyRake'])
		d['tourneyBounty'] = 0.0 if d['tourneyBounty'] is None else self.stringToFloat(d['tourneyBounty'])
		return True
		
		
	#TODO: pass to hand? extract more lines?
	# "player" finished the tournament in 2nd place and received $0.00
	PatternPlayerFinishesTourney = re.compile(
		"^(?P<name>.*?)\s finished\s the\s tournament\s in\s .* \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerFinishesTourney(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerFinishesTourney.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	
		
	#TODO: pass to hand? extract more lines?
	# "player" wins the tournament and receives $0.00 - congratulations!
	PatternPlayerWinsTourney = re.compile(
		"^(?P<name>.*?)\s wins\s the\s tournament\s .* \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerWinsTourney(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerWinsTourney.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
		
	# "player" wins the $0.00 bounty for eliminating "player"
	#TODO: pass to hand? extract more lines?
	PatternPlayerWinsBounty = re.compile(
		"^(?P<name>.*?)\s wins\s the\s [^\d\.]?(?P<amount>[\d\.]+)\s bounty\s .+ \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerWinsBounty(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerWinsBounty.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True
	 	
	# "player" (0000 in chips) out of hand (moved from another table into small blind)
	#TODO: pass to hand? extract more lines?
	PatternPlayerOutOfHand = re.compile(
		"^(?P<name>.*?)\s \([\d]+\s in\s chips\)\s out\s of\s hand\s .+  \s*$", re.X|re.I
		)
	@HcConfig.LineParserMethod(priority=160)
	def parsePlayerOutOfHand(self, lines, eventHandler, events):
		oldLines = []
		for line in lines:
			m = self.PatternPlayerOutOfHand.match(line['chars'])
			if m is not None:
				oldLines.append(line)
		for line in oldLines:
			lines.remove(line)
		return True

class PokerStarsParserHoldemENTourney1(PokerStarsParserHoldemENTourney2):
	
	Id = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextTourney,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='1',
			)
	
	# PokerStars Game #0123456789: Tournament #0123456789, $0.00+$0.00 Hold'em No Limit - Level I (10/20) - 0000/00/00 00:00:00 ET
	PatternGameHeader = re.compile(
		"""^PokerStars\s Game\s
			\#(?P<handID>\d+)\:\s
			Tournament\s \#(?P<tourneyID>\d+),\s
			(?P<tourneyBuyInType>	
				(
					[^\d\.]?(?P<tourneyBuyIn>[\d\.]+)\+
					[^\d\.]?(?P<tourneyRake>[\d\.]+)
					(\+[^\d\.]? (?P<tourneyBounty>[\d\.]+) )?
					(\s(?P<currency>[A-Z]+))?
				)
				|
				Freeroll
			)\s+
			(?P<game>Hold\'em)\s
			(?P<gameLimit>No\sLimit)\s
			\-\s+ 
			(Match\s Round\s [IVXLCDM]+, \s)?
			Level\s[IVXLCDM]+\s
			\(
				[^\d\.]?(?P<smallBlind>[\d\.]+)\/
				[^\d\.]?(?P<bigBlind>[\d\.]+)
				\s?
			\)
			\s-\s
			(?P<year>\d+)\/
			(?P<month>\d+)\/
			(?P<day>\d+)\s
			(?P<hour>\d+)\:
			(?P<minute>\d+)\:
			(?P<second>\d+)
			.+\s*$""", re.X|re.I
		)
			
	
	

if __name__ == '__main__':
	
	from oo1 import hh
	hh = HcConfig.linesFromString(hh)
	p = PokerStarsParserHoldemENCashGame2()
	p = PokerStarsParserHoldemENCashGameHomeGame2()
	p = PokerStarsParserHoldemENTourney2()
	
	eventHandler = HcConfig.HandHoldemDebug()
	hand = p.feed(hh, eventHandler)
	print hand
	
	
	import cProfile as profile	
	def test():
		for i in xrange(20000):
			hand = p.feed(hh, eventHandler)
	##profile.run('test()')

	
