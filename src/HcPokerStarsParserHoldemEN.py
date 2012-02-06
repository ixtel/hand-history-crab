# -*- coding: UTF-8 -*-

import re
import HcConfig

#TODO: home game tourneys, tourney sumaries, (...)
#TODO: no idea when stars introduced currency symbols. along with local time?
#TODO: check if home game was introduced after local time?
#TODO:stars does not show ante in game header
#TODO: seen player buying in posting 1) BB 2) SB 3) BB + SB have to check this
#      and add a eventHandler to Hand() ..something like handlePlayerBuysIn(). 
#TODO: no idea currently how to handle rake and actual hands.

#************************************************************************************
#NOTES:
#
# PokerStars incremental rake (thanks PokerStars nick): 
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


# POKERSTARS TIMELINE
# 02.2012: feb 01, 02 (?) there was a bug in HHs. summary where hand winners where shown as loosing: 
#            'Seat N: "playerName" showed [cards] and lost ($$$$) with ...'
#             instead of
#             'Seat N: "playerName" showed [cards] and won ($$$$) with ...'
# 12.28.2011: PokerStars announces switch to weighted contributed rake.
# 01.10.2012: PokerStars changes hand history file format: "PokerStars Game" in header is 
#         now "PokerStars Hand". TODO: not clear how the change is for home games. my guess is
#         "PokerStars Home Hame Hand"

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
# parser implementations
#************************************************************************************
# older header - no local date/time in header
class PokerStarsParserHoldemENCashGame1(HcConfig.LineParserBase):
	
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
		"""^PokerStars\s ((Home\s)? Game\s| (Home\sGame\s)? Hand\s)
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

	def __init__(self, *args, **kws):
		HcConfig.LineParserBase.__init__(self, *args, **kws)
		self._seatNoButton = 0
		
	def feed(self, *args, **kws):
		self._seatNoButton = 0
		return HcConfig.LineParserBase.feed(self, *args, **kws)
		
	def stringToFloat(self, amount):
		return float(amount)
		
	PatternTableHeader = re.compile(
		"""^Table\s \'(?P<tableName>[^\']+)\'\s
			(?P<maxPlayers>\d+)\-max\s
			(\(Play\s Money\)\s)?
			Seat\s\#(?P<seatNoButton>\d+)\sis\sthe\sbutton
			\s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=2)
	def parseGameHeader(self, lines, eventHandler, events, state):
		if len(lines) < 2:
			return False
				
		m = self.PatternGameHeader.match(lines[0][1])
		if m is None:
			return False
		d = m.groupdict()
		m = self.PatternTableHeader.match(lines[1][1])
		if m is None:
			lines.pop(0)
			return False
		d.update(m.groupdict())
		
		d['seatNoButton'] = int(d['seatNoButton'])
		d['site'] = self.ID['site']
		d['gameScope'] = self.ID['gameScope']
		d['gameContext'] = self.ID['gameContext']
		d['game'] = GameMapping[d['game']]
		d['gameLimit'] = GameLimitMapping[d['gameLimit'].lower()]
		#NOTE: stars added currency to header at some point, but this is pretty useless
		# for parsing old hand histories, so we parse currency symbols directly
		line = lines[0][1]
		currency = CurrencyMapping['']
		for symbol in CurrencySymbols:
			if symbol in line:
				currency = CurrencyMapping[symbol]
				break
		d['currency'] = currency
		d['bigBlind'] = self.stringToFloat(d['bigBlind'])
		d['smallBlind'] = self.stringToFloat(d['smallBlind'])
		d['maxPlayers'] = int(d['maxPlayers'])
		d['time'] = HcConfig.timeToUTC(
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
		
		#NOTE: we have to parse ante here because PS does not report it in header
		# we can either guess here (highest amount posted) or look it up somewhere
		# if we are positive that ante is charged.
		maxAnte = self.parsePlayerPostAnte(lines, eventHandler, events, state)
		d['ante'] = maxAnte
				
		events[0] = (eventHandler.handleHandStart, d)
		return True
	
	
	#NOTE: micro optimization here, not shure if its worth it. parsing and passing
	# a sstate info makes actions prior to hole-cards-dealt break loops faster. 
	#WARNING: interferes with call to parsePlayerPostAnte() we make in parseGameHeader()
	KwPreFlop = ' HOLE CARDS '
	PatternPreflop = re.compile("""^^\*\*\*\sHOLE\sCARDS\s\*\*\*$\s*$""")				
	@HcConfig.lineParserMethod(priority=1)
	def parsePreflop(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwPreFlop not in line[1]: continue
			m = self.PatternPreflop.match(line[1])
			if m is not None:
				events[line[2]] = (eventHandler.handlePreflop, {})
				lines.remove(line)
				state[HcConfig.StreetPreflop] = line[2]
				break
		return True
	
	
	KwPatternSummary = ' SUMMARY '
	PatternSummary = re.compile("""^^\*\*\*\sSUMMARY\s\*\*\*\s*$""")				
	@HcConfig.lineParserMethod(priority=3)
	def parseSummary(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwPatternSummary not in line[1]: continue
			m = self.PatternSummary.match(line[1])
			if m is not None:
				# drop summary, we don't need it
				while i < len(lines):
					lines.pop(i)
				break	
		return True
	
	
	KwPlayer = 'Seat '
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
	@HcConfig.lineParserMethod(priority=10)
	def parsePlayer(self, lines, eventHandler, events, state):
		
		# cash game: stars does not report a player sitting out until the blinds are
		# posted. in this case we have a sitting out event but no seat number / no stack info
		# so best ignore these players.
				
		# find players
		oldLines = []
		playerNames = []
		state['playerNames'] = playerNames
		for i, line in enumerate(lines):
			if line[2] >= state[HcConfig.StreetPreflop]: break
			if self.KwPlayer not in line[1]: continue
			m = self.PatternPlayer.match(line[1])
			if m is None:
				#NOTE: we can not break here because other formats may have other player flags
				continue
			oldLines.insert(0, i)
			d = m.groupdict()
			d['seatNo'] = int(d['seatNo'])
			d['stack'] = self.stringToFloat(d['stack'])
			d['sitsOut'] = bool(d['sitsOut'])
			playerNames.append(d['name'])
			events[line[2]] = (eventHandler.handlePlayer, d)
		for i in oldLines:
			del lines[i]
		return True
					
		
	#TODO: report event?
	#playerXYZ will be allowed to play after the button
	KwPlayerAllowedToPlay = ' allowed '
	PatternPlayerAllowedToPlay = re.compile(
		"""^(?P<name>.*?)\s will\s be\s allowed\s to\s play\s .* \s*$
		""", re.X|re.I 
		)				
	@HcConfig.lineParserMethod(priority=40)
	def parsePlayerPlayerAllowedToPlay(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerAllowedToPlay not in line[1]: continue
			m = self.PatternPlayerAllowedToPlay.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: for some strange reason found a HH where a player posts only the small blinds
	# guess buy in rules have changed at some point
	KwPlayerPostsSmallBlind = ' posts small '
	PatternPlayerPostsSmallBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s blind\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.lineParserMethod(priority=45)
	def parsePlayerPostsSmallBlind(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if line[2] >= state[HcConfig.StreetPreflop]: break
			if self.KwPlayerPostsSmallBlind not in line[1]: continue
			m = self.PatternPlayerPostsSmallBlind.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerPostsSmallBlind, d)
		for i in oldLines:
			del lines[i]
		return True
			
	
	KwPlayerPostsBigBlind = ' posts big '
	PatternPlayerPostsBigBlind = re.compile(
		"""^(?P<name>.*?)\:\sposts\s big\s blind\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.lineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if line[2] >= state[HcConfig.StreetPreflop]: break
			if self.KwPlayerPostsBigBlind not in line[1]: continue
			m = self.PatternPlayerPostsBigBlind.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerPostsBigBlind, d)
		for i in oldLines:
			del lines[i]
		return True
	
		
	KwPlayerPostsAnte = ' the ante '
	PatternPlayerPostsAnte = re.compile(
		"""^(?P<name>.*?)\:\sposts\s the\s ante\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	#NOTE: we parse ante manually. see notes in parseGameHeader() 
	##@HcConfig.lineParserMethod(priority=50)
	def parsePlayerPostAnte(self, lines, eventHandler, events, state):
		maxAnte = 0.0
		oldLines = []
		for i, line in enumerate(lines):
			if line[2] >= state[HcConfig.StreetPreflop]: break
			if self.KwPlayerPostsAnte not in line[1]: continue
			m = self.PatternPlayerPostsAnte.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				amount = self.stringToFloat(d['amount'])
				maxAnte = max(maxAnte, amount)
				d['amount'] = amount
				events[line[2]] = (eventHandler.handlePlayerPostsAnte, d)
		for i in oldLines:
			del lines[i]
		##return True
		return maxAnte
		
	
	#TODO: report amount total or small/big blind?
	KwPlayerPostsBuyIn = ' & big '
	PatternPlayerPostsBuyIn = re.compile(
		"""^(?P<name>.*?)\:\sposts\s small\s &\s big\s blinds\s [^\d\.]?(?P<amount>[\d\.]+) (\sand\s is\ all\-in)? \s*$
		""", re.X|re.I 
		)				
	@HcConfig.lineParserMethod(priority=50)
	def parsePlayerPostsBuyIn(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if line[2] >= state[HcConfig.StreetPreflop]: break
			if self.KwPlayerPostsBuyIn not in line[1]: continue
			m = self.PatternPlayerPostsBuyIn.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerPostsBuyIn, d)
		for i in oldLines:
			del lines[i]
		return True
		
			
	KwPlayerHoleCards = 'Dealt to '
	PatternPlayerHoleCards = re.compile(
		"^Dealt\s to\s (?P<name>.*?)\s \[(?P<card1>[23456789TJQKA][cdhs])\s(?P<card2>[23456789TJQKA][cdhs])\]\s*$", 
		re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=150)
	def parsePlayerPlayerHoleCards(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwPlayerHoleCards not in line[1]: continue
			m = self.PatternPlayerHoleCards.match(line[1])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				events[line[2]] = (eventHandler.handlePlayerHoleCards, d)
				lines.remove(line)
				break
		return True
	
	
	KwPlayerFolds = ' folds'
	PatternPlayerFolds = re.compile(
		"""^(?P<name>.*?)\:\s folds
			(
				\s
				\[ 
					(?P<card1>[23456789TJQKA][cdhs]) 
					( \s(?P<card2>[23456789TJQKA][cdhs]) )?
				\]
			)?
			\s*$""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=158)
	def parsePlayerFolds(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerFolds not in line[1]: continue
			m = self.PatternPlayerFolds.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				card1, card2 = d.pop('card1'), d.pop('card2')
				if card1 is not None and card2 is not None:
					d['cards'] = (card1, card2)
				elif card1 is not None:
					d['cards'] = (card1,)
				events[line[2]] = (eventHandler.handlePlayerFolds, d)
		for i in oldLines:
			del lines[i]
		return True
	
	
	KwPlayerChecks = ' checks'
	PatternPlayerChecks = re.compile(
		"^(?P<name>.*?)\:\s checks\s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=159)
	def parsePlayerChecks(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerChecks not in line[1]: continue
			m = self.PatternPlayerChecks.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				events[line[2]] = (eventHandler.handlePlayerChecks, m.groupdict())
		for i in oldLines:
			del lines[i]
		return True
	
	
	KwPlayerBets = ' bets '
	PatternPlayerBets = re.compile(
		"^(?P<name>.*?)\:\s bets\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)? \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerBets(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerBets not in line[1]: continue
			m = self.PatternPlayerBets.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerBets, d)
		for i in oldLines:
			del lines[i]
		return True
		
	
	KwPlayerRaises = ' raises '
	PatternPlayerRaises = re.compile(
		"^(?P<name>.*?)\:\s raises\s .*? to\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerRaises(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerRaises not in line[1]: continue
			m = self.PatternPlayerRaises.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerRaises, d)
		for i in oldLines:
			del lines[i]
		return True
	
	
	KwPlayerCalls = ' calls'
	PatternPlayerCalls = re.compile(
		"^(?P<name>.*?)\:\s calls\s [^\d\.]?(?P<amount>[\d\.]+) (\s and\s is\s all\-in)?\s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerCalls(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerCalls not in line[1]: continue
			m = self.PatternPlayerCalls.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handlePlayerCalls, d)
		for i in oldLines:
			del lines[i]
		return True
	
	#TODO: convert text to unicode?
	KwPlayerChats = 'said, '
	PatternPlayerChats = re.compile(
		"^(?P<name>.*?)\s said,\s \"(?P<text>.*)\" \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerChats(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerChats not in line[1]: continue
			m = self.PatternPlayerChats.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				events[line[2]] = (eventHandler.handlePlayerChats, d)
		for i in oldLines:
			del lines[i]
		return True
	
		
	KwPlayerSitsOut = ' out'
	PatternPlayerSitsOut = re.compile(
		"""^(?P<name>.*?)\:?\s (sits\s out | is\s sitting\s out)\s*$""", 
		re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=159)
	def parsePlayersSitsOut(self, lines, eventHandler, events, state):					
		# find all players sitting out
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerSitsOut not in line[1]: continue
			m = self.PatternPlayerSitsOut.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				if d['name'] not in state['playerNames']:
					# assume cash game (see notes in parsePlayer() )
					continue
				else:
					events[line[2]] = (eventHandler.handlePlayerSitsOut, d)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerDisconnected = ' disconnected'
	PatternPlayerDisconnected = re.compile(
		"^(?P<name>.*?)\s is\s disconnected \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerDisconnected(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerDisconnected not in line[1]: continue
			m = self.PatternPlayerDisconnected.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerReconnects = ' is connected'
	PatternPlayerReconnects = re.compile(
		"^(?P<name>.*?)\s is\s connected \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerReconnects(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerReconnects not in line[1]: continue
			m = self.PatternPlayerReconnects.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerTimedOut = ' timed out'
	PatternPlayerTimedOut = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerTimedOut(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerTimedOut not in line[1]: continue
			m = self.PatternPlayerTimedOut.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerReturns = ' has returned'
	PatternPlayerReturns = re.compile(
		"^(?P<name>.*?)\s has\s returned \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerReturns(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerReturns not in line[1]: continue
			m = self.PatternPlayerReturns.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerTimedOutWhileDisconnected = ' timed out '
	PatternPlayerTimedOutWhileDisconnected = re.compile(
		"^(?P<name>.*?)\s has\s timed\s out\s while\s (being\s)? disconnected \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerTimedOutWhileDisconnected(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerTimedOutWhileDisconnected not in line[1]: continue
			m = self.PatternPlayerTimedOutWhileDisconnected.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	# player removed for missing blinds
	KwPlayerRemoved = ' removed from '
	PatternPlayerRemoved = re.compile(
		"^(?P<name>.*?)\s was\s removed\s from\s the\s table\s .* \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerRemoved(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerRemoved not in line[1]: continue
			m = self.PatternPlayerRemoved.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
	
	KwFlop = ' FLOP '
	PatternFlop = re.compile("""^\*\*\*\sFLOP\s\*\*\*\s
	\[
		(?P<card1>[23456789TJQKA][cdhs])\s
		(?P<card2>[23456789TJQKA][cdhs])\s
		(?P<card3>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	
	)				
	@HcConfig.lineParserMethod(priority=200)
	def parseFlop(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwFlop not in line[1]: continue
			m = self.PatternFlop.match(line[1])
			if m is not None:
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'), d.pop('card3'))
				events[line[2]] = (eventHandler.handleFlop, d)
				lines.remove(line)
				break
		return True
	
	
	KwTurn = ' TURN '
	PatternTurn = re.compile("""^\*\*\*\sTURN\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	)				
	@HcConfig.lineParserMethod(priority=200)
	def parseTurn(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwTurn not in line[1]: continue
			m = self.PatternTurn.match(line[1])
			if m is not None:
				d = m.groupdict()
				events[line[2]] = (eventHandler.handleTurn, d)
				lines.remove(line)
				break
		return True
	
	
	KwRiver = ' RIVER '
	PatternRiver = re.compile("""^\*\*\*\sRIVER\s\*\*\*\s
	\[.+?\]\s
	\[
		(?P<card>[23456789TJQKA][cdhs])
	\]
	\s*$""", re.X|re.I
	)				
	@HcConfig.lineParserMethod(priority=200)
	def parseRiver(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwRiver not in line[1]: continue
			m = self.PatternRiver.match(line[1])
			if m is not None:
				d = m.groupdict()
				events[line[2]] = (eventHandler.handleRiver, d)
				lines.remove(line)
				break
		return True
		
		
	KwShowDown = ' SHOW DOWN '
	PatternShowDown = re.compile("""^^\*\*\*\sSHOW\sDOWN\s\*\*\*\s*$""")				
	@HcConfig.lineParserMethod(priority=300)
	def parseShowDown(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwShowDown not in line[1]: continue
			m = self.PatternShowDown.match(line[1])
			if m is not None:
				events[line[2]] = (eventHandler.handleShowDown, {})
				lines.remove(line)
				break
		return True
	
	
	KwPlayerShows = ' shows '
	PatternPlayerShows = re.compile(
		"""^(?P<name>.*?)\:\s shows\s 
		\[
			(?P<card1>[23456789TJQKA][cdhs])\s 
			(?P<card2>[23456789TJQKA][cdhs])
		\]\s
		\(.+\)\s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerShows(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerShows not in line[1]: continue
			m = self.PatternPlayerShows.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['cards'] = (d.pop('card1'), d.pop('card2'))
				events[line[2]] = (eventHandler.handlePlayerShows, d)
		for i in oldLines:
			del lines[i]
		return True
	
		
	KwPlayerMucks = ' mucks '
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
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerMucks(self, lines, eventHandler, events, state):
		oldLines = []
		players = {}
		for i, line in enumerate(lines):
			if self.KwPlayerMucks not in line[1]: continue
			m = self.PatternPlayerMucks.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				d['cards'] = None
				players[d['name']] = (d, line[2])
		for i in oldLines:
			del lines[i]
			
		# try to find hole cards player mucked
		oldLines = []
		for i, line in enumerate(lines):
			m = self.PatternPlayerMucked.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				players[d['name']][0]['cards'] = (d.pop('card1'), d.pop('card2'))
		for i in oldLines:
			del lines[i]
			
		for name, (d, lineno) in players.items():
			events[line[2]] = (eventHandler.handlePlayerMucks, d)
		return True	
		
		
	KwPlayerCollected = ' collected '
	PatternPlayerCollected = re.compile(
		"""^(?P<name>.*?)\s collected\s [^\d\.]?(?P<amount>[\d\.]+)\s from\s 
		(?P<pot>(
			pot |
			main\s pot |
			side\s pot(\-(?P<potNo>[\d])+)?)
		) \s*$""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=400)
	def parsePlayerWins(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerCollected not in line[1]: continue
			m = self.PatternPlayerCollected.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
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
						if lines[0]['lineno'] < line[2]:
							lines.pop(0)
					return False
				events[line[2]] = (eventHandler.handlePlayerWins, d)
		for i in oldLines:
			del lines[i]
		return True
				
	
	#TODO: stars does not put names in quotes. no idea if player names may end with spaces.
	# if so we are in trouble here. there is no way to tell "player\s" apart from "player\s\s",
	# even if we keep a lokkup of player names. hope stars has done the right thing.
	KwUncalledBet = ' returned to '
	PatternUncalledBet = re.compile(
		"^Uncalled\s bet\s \([^\d\.]?(?P<amount>[\d\.]+)\)\s returned\s to\s (?P<name>.*?) \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=400)
	def parseUncalledBet(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwUncalledBet not in line[1]: continue
			m = self.PatternUncalledBet.match(line[1])
			if m is not None:
				d = m.groupdict()
				d['amount'] = self.stringToFloat(d['amount'])
				events[line[2]] = (eventHandler.handleUncalledBet, d)
				lines.remove(line)
				# logic says there can only be one uncalled bet per hand
				break
		return True
		
	
	KwPlayerShowsCards = ' shows '
	PatternPlayerShowsCards = re.compile(
		"""^(?P<name>.*?)\:\s shows\s 
		\[
			(?P<card1>[23456789TJQKA][cdhs])
			(\s (?P<card2>[23456789TJQKA][cdhs]) )?
		\]\s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=410)
	def parsePlayerShowsCards(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerShowsCards not in line[1]: continue
			m = self.PatternPlayerShowsCards.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
				d = m.groupdict()
				card2 = d.pop('card2')
				if card2:
					d['cards'] = (d.pop('card1'), card2)
				else:
					d['cards'] = (d.pop('card1'), )
				events[line[2]] = (eventHandler.handlePlayerShows, d)
		for i in oldLines:
			del lines[i]
		return True
	
	
	#TODO: report event?
	KwPlayerDoesNotShowHand = " doesn't show "
	PatternPlayerDoesNotShowHand = re.compile(
		"""^(?P<name>.*?)\:\s doesn\'t\s show\s  hand \s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=450)
	def parsePlayerDoesNotShowHand(self, lines, eventHandler, events, state):
		for i, line in enumerate(lines):
			if self.KwPlayerDoesNotShowHand not in line[1]: continue
			m = self.PatternPlayerDoesNotShowHand.match(line[1])
			if m is not None:
				lines.remove(line)
				# logic says there can only be one "player does not show hand" per hand
				break
		return True
		
	
	#TODO: report event?
	KwPlayerLeavesTable = ' leaves '
	PatternPlayerLeavesTable = re.compile(
		"""^(?P<name>.*?)\s leaves\s the\s table \s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=450)
	def parsePlayerLeavesTable(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerLeavesTable not in line[1]: continue
			m = self.PatternPlayerLeavesTable.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True	
	
	
	#TODO: report event?
	KwPlayerJoinsTable = ' joins '
	PatternPlayerJoinsTable = re.compile(
		"""^(?P<name>.*?)\s joins\s the\s table\s at\s seat\s \#\d+ \s*$
		""", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=450)
	def parsePlayerJoinsTable(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerJoinsTable not in line[1]: continue
			m = self.PatternPlayerJoinsTable.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
		
	# clean up events
		
	PatternEmptyLine = re.compile('^\s*$')
	@HcConfig.lineParserMethod(priority=9999)
	def parseEmptyLines(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.PatternEmptyLine.match(line[1]) is not None:
				oldLines.insert(0, i)	
		for i in oldLines:
			del lines[i]
		return True	


class PokerStarsParserHoldemENTourney1(PokerStarsParserHoldemENCashGame1):
	
	ID = HcConfig.HcID(
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
		"""^PokerStars\s ((Home\s)? Game\s| (Home\sGame\s)? Hand\s)
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

	@HcConfig.lineParserMethod(priority=1)
	def parseGameHeader(self, lines, eventHandler, events, state):
		if not PokerStarsParserHoldemENCashGame1.parseGameHeader(self, lines, eventHandler, events, state):
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
		
		
	#TODO: report event?
	# "player" finished the tournament in 2nd place and received $0.00
	KwPlayerFinishesTourney = ' finished '
	PatternPlayerFinishesTourney = re.compile(
		"^(?P<name>.*?)\s finished\s the\s tournament\s in\s .* \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerFinishesTourney(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerFinishesTourney not in line[1]: continue
			m = self.PatternPlayerFinishesTourney.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	
		
	#TODO: report event?
	# "player" wins the tournament and receives $0.00 - congratulations!
	KwPlayerWinsTourney = ' wins '
	PatternPlayerWinsTourney = re.compile(
		"^(?P<name>.*?)\s wins\s the\s tournament\s .* \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerWinsTourney(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerWinsTourney not in line[1]: continue
			m = self.PatternPlayerWinsTourney.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
		
	
	#TODO: report event?
	# "player" wins the $0.00 bounty for eliminating "player"
	KwPlayerWinsBounty = ' bounty '
	PatternPlayerWinsBounty = re.compile(
		"^(?P<name>.*?)\s wins\s the\s [^\d\.]?(?P<amount>[\d\.]+)\s bounty\s .+ \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerWinsBounty(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerWinsBounty not in line[1]: continue
			m = self.PatternPlayerWinsBounty.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True
	 	
	#TODO: report event?
	# "player" (0000 in chips) out of hand (moved from another table into small blind)
	KwPlayerOutOfHand = ' out of '
	PatternPlayerOutOfHand = re.compile(
		"^(?P<name>.*?)\s \([\d]+\s in\s chips\)\s out\s of\s hand\s .+  \s*$", re.X|re.I
		)
	@HcConfig.lineParserMethod(priority=160)
	def parsePlayerOutOfHand(self, lines, eventHandler, events, state):
		oldLines = []
		for i, line in enumerate(lines):
			if self.KwPlayerOutOfHand not in line[1]: continue
			m = self.PatternPlayerOutOfHand.match(line[1])
			if m is not None:
				oldLines.insert(0, i)
		for i in oldLines:
			del lines[i]
		return True


#************************************************************************************
# parser implementations
#************************************************************************************
# newer header - local date/time in header
class PokerStarsParserHoldemENCashGame2(PokerStarsParserHoldemENCashGame1):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='2',
			)
	
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

class PokerStarsParserHoldemENTourney2(PokerStarsParserHoldemENTourney1):
	
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
		"""^PokerStars\s ((Home\s)? Game\s| (Home\sGame\s)? Hand\s)
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


class PokerStarsParserHoldemENTourneyHomeGame2(PokerStarsParserHoldemENTourney2):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextTourney,
			gameScope=HcConfig.GameScopeHomeGame,
			site=HcConfig.SitePokerStars,
			version='2',
			)
			
	PatternGameHeader = re.compile(
		"""^PokerStars\s Home\s Game\s
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



#************************************************************************************
#
#************************************************************************************
# PokerStars header change (01.10.2011) - "PokerStars Game #" is now "PokerStars Hand #"
class PokerStarsParserHoldemENCashGame3(PokerStarsParserHoldemENCashGame2):
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopeHomeGame,
			site=HcConfig.SitePokerStars,
			version='3',
			)
	
	PatternGameHeader = re.compile(
		"""^PokerStars\s Hand\s
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
	
class PokerStarsParserHoldemENCashGameHomeGame3(PokerStarsParserHoldemENCashGameHomeGame2):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextCashGame,
			gameScope=HcConfig.GameScopeHomeGame,
			site=HcConfig.SitePokerStars,
			version='3',
			)
	
	#TODO: got no HHs / confirmation that header now actually reads "PokerStars Home Game Hand #"
	PatternGameHeader = re.compile(
		"""^PokerStars\s Home\s Game\s Hand\s
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
	
class PokerStarsParserHoldemENTourney3(PokerStarsParserHoldemENTourney2):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextTourney,
			gameScope=HcConfig.GameScopePublic,
			site=HcConfig.SitePokerStars,
			version='3',
			)
			
	PatternGameHeader = re.compile(
		"""^PokerStars\s Hand\s
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
		
class PokerStarsParserHoldemENTourneyHomeGame3(PokerStarsParserHoldemENTourney3):
	
	ID = HcConfig.HcID(
			dataType=HcConfig.DataTypeHand, 
			language=HcConfig.LanguageEN,
			game=HcConfig.GameHoldem,
			gameContext=HcConfig.GameContextTourney,
			gameScope=HcConfig.GameScopeHomeGame,
			site=HcConfig.SitePokerStars,
			version='3',
			)
			
	PatternGameHeader = re.compile(
		"""^PokerStars\s Home\s Game\s Hand\s
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
