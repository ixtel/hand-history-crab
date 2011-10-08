
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
			\]$
		""", re.X 
		)
	PatternTableHeader = re.compile(
		"""^Table\s \'(?P<tableName>[^\']+)\'\s
			(?P<maxPlayers>\d+)\-max\s
			Seat\s\#(?P<seatNoButton>\d+)\sis\sthe\sbutton
			$
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
				$
		""", re.X
		)
	PatternPlayerSitsOut = re.compile("""^(?P<name>.*?)\:\s (sits\s out | is\s sitting\s out)$
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
			if m is not None:
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
		right = []
		left = []
		for player in players:
			if player.seatNo < self._seatNoButton:
				right.append(player)
			elif player.seatNo > self._seatNoButton:
				left.append(player)
			else:
				left.append(player)
		myPlayers = left + right
		for buttonOrder, seatName in enumerate(HHConfig.Seats.SeatNames[len(myPlayers)]):
			player = myPlayers[buttonOrder]
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
		"""^(?P<name>.*?)\:\sposts\ssmall\sblind\s[^\d\.]?(?P<amount>[\d\.]+)
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
		"""^(?P<name>.*?)\:\sposts\sbig\sblind\s[^\d\.]?(?P<amount>[\d\.]+)
		""", re.X 
		)				
	@HHConfig.LineParserMethod(priority=50)
	def parsePlayerPostsBigBlind(self, data, events):
		print data
		items = []
		for item in data:
			m = self.PatternPlayerPostsBigBlind.match(item['line'])
			if m is not None:
				items.append(item)
				events[item['lineno']] = HHConfig.EventPlayerPostsBigBlind(**m.groupdict())
		for item in items:
			data.remove(item)
	
	
	PatternPlayerFolds = re.compile(
		"^(?P<name>.*?)\:\s folds$", re.X
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
		
		
		
	
	
hh = '''PokerStars Game #56441606094:  Hold'em No Limit ($0.01/$0.02 USD) - 2011/01/23 21:09:53 CET [2011/01/23 15:09:53 ET]
Table 'Mattiaca XVII' 6-max Seat #3 is the button
Seat 1: elanto19 ($1.68 in chips) 
Seat 2: hamtitam ($2.76 in chips) 
Seat 3: NCBB ($1.68 in chips) 
Seat 4: failertb ($4.98 in chips) 
Seat 5: Barny58 ($1.33 in chips)
Seat 6: gracher11 ($2 in chips) 
failertb: posts small blind $0.01
Barny58: posts big blind $0.02

'''
'''
*** HOLE CARDS ***
Dealt to failertb [Td 2s]
gracher11: folds 
elanto19: folds 
hamtitam: folds 
NCBB: raises $0.02 to $0.04
failertb: folds 
Barny58: calls $0.02
*** FLOP *** [Ts Kd 7h]
Barny58: checks 
NCBB: bets $0.06
Barny58: calls $0.06
*** TURN *** [Ts Kd 7h] [Kc]
Barny58: checks 
NCBB: bets $0.20
Barny58: calls $0.20
*** RIVER *** [Ts Kd 7h Kc] [Qc]
Barny58: checks 
NCBB: checks 
*** SHOW DOWN ***
Barny58: shows [Kh Jc] (three of a kind, Kings)
NCBB: mucks hand 
Barny58 collected $0.58 from pot
*** SUMMARY ***
Total pot $0.61 | Rake $0.03 
Board [Ts Kd 7h Kc Qc]
Seat 1: elanto19 folded before Flop (didn't bet)
Seat 2: hamtitam folded before Flop (didn't bet)
Seat 3: NCBB (button) mucked [8h 8d]
Seat 4: failertb (small blind) folded before Flop
Seat 5: Barny58 (big blind) showed [Kh Jc] and won ($0.58) with three of a kind, Kings
Seat 6: gracher11 folded before Flop (didn't bet)
'''
#Table 'Mattiaca XVII' 6-max Seat #3 is the button

p = PokerStarsParserHoldemEN()
for event in p.feed(hh.split('\n')):
	print event.toString()

	
