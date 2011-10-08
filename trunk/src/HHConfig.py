
import sys, operator

#************************************************************************************
# consts
#************************************************************************************
LineFeed = '\r' if sys.platform == 'Darwin' else '\n'
TimeNone = 0

SiteNone = ''
SitePokerStars = 'PokerStars'

LanguageNone = ''
LanguageEN = 'EN'

StreetNone = ''
StreetBlinds = 'Blinds'
StreetPreflop = 'Preflop'
StreetFlop = 'Flop'
StreetTurn = 'Turn'
StreetRiver = 'River'
StreetShowDown = 'ShowDown'

GameNone = ''
GameHoldem = 'Holdem'

GameLimitNone = ''
GameLimitNoLimit = 'NoLimit'
GameLimitPotLimit = 'PotLimit'
GameLimitFixedLimit = 'FixedLimit'

CurrencyNone = ''
CurrencyDollar = 'USD'

PotTypeUnclaimed = 'Unclaimed'
PotTypeTied = 'Tied'
PotTypeWon = 'Won'

class Seats(object):
	SeatNameNone = ''
	SeatNameUTG = 'UTG'
	SeatNameUTG1 = 'UTG+1'
	SeatNameUTG2 = 'UTG+2'
	SeatNameMP = 'MP'
	SeatNameMP1 = 'MP+1'
	SeatNameMP2 = 'MP+2'
	SeatNameCO = 'CO'
	SeatNameBTN = 'BTN'
	SeatNameSB = 'SB'
	SeatNameBB = 'BB'
	SeatNames = {		# nPlayers --> seat names
			2: (SeatNameSB, SeatNameBB),
			3: (SeatNameBTN, SeatNameSB, SeatNameBB),
			4: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG),
			5: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameMP),
			6: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameMP, SeatNameCO),
			7: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameMP, SeatNameCO),
			8: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameMP, SeatNameMP1, SeatNameCO, ),
			9: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameUTG2, SeatNameMP, SeatNameMP1, SeatNameCO),
			10: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameUTG2, SeatNameMP, SeatNameMP1, SeatNameMP2, SeatNameCO),
			}
	@classmethod
	def seatName(klass, nSeats, seatNo):
		"""
		@param nSeats: (int) number of seats total
		@param seatNo: (int) index of the seat to retrieve name for. 0 == player first to act preflop
		@return: (str) seat name
		"""
		seatNames = klass.SeatNames[nSeats]
		return seatNames[seatNo]

#************************************************************************************
# events
#************************************************************************************
class Event(object):
	Priority = 0
	@classmethod
	def __eq__(klass, other):
		return klass == other
	@classmethod
	def __ne__(klass, other): not klass.__eq__(other)
	
class EventHandStart(Event):
	Priority = 1
	def __init__(self, 
			lines=None, 
			site=SiteNone, 
			tourneyID='',
			handID='',
			game=GameNone, 
			gameLimit=GameLimitNone, 
			timestamp=TimeNone,
			tableName='',
			maxPlayers=0,
			currency=CurrencyNone,
			smallBlind=0.0,
			bigBlind=0.0,
			ante=0.0,
			):
		self.lines = [] if lines is None else lines
		self.site = site
		self.tourneyID = tourneyID
		self.handID = handID
		self.game = game
		self.gameLimit = gameLimit
		self.timestamp = timestamp
		self.tableName = tableName
		self.maxPlayers = maxPlayers
		self.currency = currency
		self.smallBlind = smallBlind
		self.bigBlind = bigBlind
		self.ante = ante
	def toString(self):
		return 'Hand %s %s' % (self.site, self.game)

class EventPlayer(Event):
	Priority = 10
	def __init__(self, name='', stack=0.0, seatNo=0, seatName='', buttonOrder=0, sitsOut=False):
		"""
		@param name: (str) player name
		@param seatNo: (int) 1 based seat number
		@param seatName: (str) seat name like 'BB' or 'SB' 
		@param buttonOrder: (int) 1 based player order relative to the button (1 is the button)
		@param sitsOut: (bool) True if player sits out initially. (stars) in cash games 
		seatNo and stack are not reported for players sitting out. so always check for 
		bool(seatNo). in tourneys players are dealt into the hand (and alowed to act) 
		regardless of the sitsOut flag.
		"""
		self.name = name
		self.stack = stack
		self.seatNo = seatNo
		self.seatName = seatName
		self.buttonOrder = buttonOrder
		self.sitsOut = sitsOut
	def toString(self):
		return 'player: "%s" seatNo: %s seatName: %s buttonOrder: %s stack: %s sitsOut: %s' % (
				self.name, self.seatNo, self.seatName, self.buttonOrder, self.stack, self.sitsOut
				)
	

class EventPlayerSitsOut(Event):
	Priority = 100
	def __init__(self, name=''):
		"""
		@param name: (str) player name
		"""
		self.name = name
	def toString(self):
		return 'player "%s" sits out' % self.name


class EventPlayerPostsSmallBlind(Event):
	Priority = 100
	def __init__(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount posted
		"""
		self.name = name
		self.amount = amount
	def toString(self):
		return 'player "%s" posts small blind: %s' % (self.name, self.amount)


class EventPlayerPostsBigBlind(Event):
	Priority = 100
	def __init__(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount posted
		"""
		self.name = name
		self.amount = amount
	def toString(self):
		return 'player "%s" posts big blind: %s' % (self.name, self.amount)


class EventPlayerFolds(Event):
	"""
	@param name: (str) player name
	"""
	Priority = 100
	def __init__(self, name=''):
		self.name = name
	def toString(self):
		return 'player "%s" folds' % self.name

#************************************************************************************
# parser base functionality
#************************************************************************************
Parsers = []	# list containing all parsers


class ParserError(Exception): pass


class LineParserMethod(object):
	"""decorator to mark a method as line parser method and assign a priority to it"""
	def __init__(self, priority=sys.maxint):
		self.priority = priority
	def __call__(self, func):
		def parseMethod(*args, **kws):
			return func(*args, **kws)
		parseMethod.klass = self.__class__
		parseMethod.priority = self.priority
		return parseMethod


class LineParserMeta(type):
	"""records all parser classes to global (list) Parsers + gathers all ParserMethods and dumps 
	their names into the (list) ParserethodNames of the class sorted by priority (ascending)
	"""
	def __new__(klass,  name, bases, kws):
		newClass = type.__new__(klass,  name, bases, kws)
		ParserMethodNames = []
		for name in newClass.__dict__:
			obj = getattr(newClass, name)
			if getattr(obj, 'klass', None) is LineParserMethod:
				ParserMethodNames.append((obj.priority, name))
		ParserMethodNames.sort()
		newClass.ParserMethodNames = [i[1] for i in ParserMethodNames]	
		Parsers.append(newClass)
		return newClass
	

class LineParserBase(object):
	"""base class for linewise parsers
	decorate any methods intendet to take part in the parsing process as ParserMethod(). 
	the	methods will be called with two arguments:
	
	data: (list) of dicts {lineno, line} of the hand history
	events: a list containg len(data) None's that needs to be filled by the methods with events
	
	the parser iterates over all parse methods, feeding data and events list to the
	next method in turn. each method should remove the lines it processed from the data
	and place an event(s) into the according slot(s) of the events list. None events will
	be ignored. if there is data left when iteration over methods is finished the 	parser 
	will throw a ParseError().
	
	usage: feed() data to the parser and iterate over the returned events.
	"""
	__metaclass__ = LineParserMeta
	
	ParserMethodNames = []
	Site = SiteNone
	Game = GameNone
	Language = LanguageNone
	
	@classmethod
	def site(klass): return klass.Site
	@classmethod
	def game(klass): return klass.Game
	@classmethod
	def language(klass): return klass.Language
		
	def __init__(self):
		pass
				
	def feed(self, lines):
		data = [{'lineno': lineno, 'line': line} for lineno, line in enumerate(lines)]
		events = [None] * len(data)
		for name in self.ParserMethodNames:
			getattr(self, name)(data, events)
		if data:
			err = 'could not parse hand (lineno %s)\n' % data[0]['lineno']
			err += 'line: %s\n' % data[0]['line']
			err += '\n'
			err += '\n'.join(lines)
			raise ParserError(err)	
		events = [event for event in events if event is not None]
		events.sort(key=operator.attrgetter('Priority'))
		return events




