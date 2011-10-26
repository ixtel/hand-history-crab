
import sys, calendar, inspect

#************************************************************************************
# consts
#************************************************************************************
LineFeed = '\r' if sys.platform == 'Darwin' else '\n'
TimeNone = 0

TimeZoneNone = ''
TimeZoneET = 'ET'


DataTypeNone = {}
DataTypeHand = 'Hand'

VersionNone = ''

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

GameContextNone = ''
GameContextCashGame = 'CashGame'
GameContextTourney = 'Tourney'

GameLimitNone = ''
GameLimitNoLimit = 'NoLimit'
GameLimitPotLimit = 'PotLimit'
GameLimitFixedLimit = 'FixedLimit'

CurrencyNone = ''
CurrencyUSD = 'USD'
CurrencyEUR = 'EUR'
CurrencyGBP = 'GBP'

#************************************************************************************
# helper methods
#************************************************************************************
def timeFromDate(date, timeZone=TimeZoneET):
	"""converts a date to a timestamp"""
	t = calendar.timegm(date)
	if timeZone == TimeZoneET:
		t += 18000	# ET + 5 hours == UTC
	else:
		raise ValueError('timeZone "%s" not implemented' % timeZone)
	return t

def linesFromString(string):
	return [
		{'lineno': lineno, 'chars': line} for 
		lineno, line in 
		enumerate(string.replace('\r\n', '\n').replace('\r','\n').split('\n'))
		]

def linesToString(lines,lineFeed=LineFeed):
	return lineFeed.join([line['chars'] for line in lines])
	
#************************************************************************************
# base objects
#************************************************************************************
class HcID(object):
	def __init__(self, **kws):
		self._kwList = tuple(kws.items())
		self._kws = kws
	def contains(self, **kws):
		for name, value in kws.items():
			if name not in self._kws:
				return False
			if self._kws[name] != value:
				return False
		return True
	def __eq__(self, other): return self._kwList == other._kwList
	def __ne__(self, other): return not self.__eq__(other)
	def __hash__(self): return hash(self._kwList)
	def __nonzero__(self): return bool(self._kws)
	def __getitem__(self, name):	return self._kws[name]
	

class HcObjectBase(object):
	ID = HcID()
	

class EventHandlerBase(HcObjectBase):
	
	def handleParseStart(self, lines):
		pass
		
	def handleParseEnd(self, events):
		pass

#************************************************************************************
# hand types
#************************************************************************************
class HandHoldem(EventHandlerBase):
	
	ID = HcID(
		dataType=DataTypeHand, 
		game=GameHoldem,
		)
	
		
	def handleHandStart(self, 
			site=SiteNone, 
			tourneyID='',
			tourneyBuyIn=0.0,
			tourneyRake=0.0,
			tourneyBounty=0.0,
			homeGameID='',
			handID='',
			game=GameNone, 
			gameLimit=GameLimitNone, 
			time=TimeNone,
			tableName='',
			maxPlayers=0,
			currency=CurrencyNone,
			smallBlind=0.0,
			bigBlind=0.0,
			ante=0.0,
			):
		""""""
		
	def handlePlayer(self, name='', stack=0.0, seatNo=0, seatName='', buttonOrder=0, sitsOut=False):
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
	
	def handlePlayerSitsOut(self, name=''):
		"""
		@param name: (str) player name
		"""
	
	def handlePlayerPostsSmallBlind(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount posted
		"""
		
	def handlePlayerPostsBigBlind(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount posted
		"""
	
	def handlePlayerPostsAnte(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount posted
		"""
		
	def handlePlayerPostsBuyIn(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float)
		"""
		
	def handlePreflop(self):
		""""""
		
	def handleFlop(self, cards=None):
		""""""
		
	def handleTurn(self, card=''):
		""""""
		
	def handleRiver(self, card=''):
		""""""
		
	def handleShowDown(self):
		""""""
		
	def handlePlayerHoleCards(self, name='', cards=None):
		"""
		@param name: (str) player name
		"""
		
	def handlePlayerChecks(self, name=''):
		"""
		@param name: (str) player name
		"""
		
	def handlePlayerFolds(self, name=''):
		"""
		@param name: (str) player name
		"""
		
	def handlePlayerBets(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount bet
		"""
		
	def handlePlayerRaises(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount raised to
		"""
		
	def handlePlayerCalls(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount called
		"""
	
	def handlePlayerChats(self, name='', text=''):
		"""
		@param name: (str) player name
		@param text: 
		"""	
		
	def handlePlayerShows(self, name='', cards=None):
		"""
		@param name: (str) player name
		@param cards:
		"""
	
	def handlePlayerMucks(self, name='', cards=None):
		"""
		@param name: (str) player name
		@param cards: (tuple) cards the player mucks or None
		"""
		
	def handlePlayerWins(self, name='', amount=0.0, potNo=0):
		"""
		@param name: (str) player name
		@param amount: (float) amount called
		@param potNo: (int) 0 for main pot, 1 for side pot1 (..)
		"""
	
	def handleUncalledBet(self, name='', amount=0.0):
		"""
		@param name: (str) player name
		@param amount: (float) amount called
		"""	
		

class HandHoldemDebug(HandHoldem):
		
	class FuncWrapper(object):
		@classmethod
		def fromObject(klass, name, obj):
			if inspect.ismethod(obj) and name.startswith('handle'):
				return klass(name, obj)
			return obj
		def __init__(self, name, func):
				self.name = name
				self.func = func
		def __call__(self, *args, **kws):
			print self.name[6:], kws
			self.func(*args, **kws)
				
	def __getattribute__(self, name):
		obj = object.__getattribute__(self, name)
		return object.__getattribute__(self,'FuncWrapper').fromObject(name, obj)
		
#************************************************************************************
# parser base functionality
#************************************************************************************
Parsers = {}	# HcID --> Parser


class ParseError(Exception):
		def __init__(self, msg, lineno=0):
			self.lineno = lineno
			Exception.__init__(self, msg)


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
		if newClass.ID:
			Parsers[newClass.ID] = newClass
		return newClass
	

class LineParserBase(HcObjectBase):
	"""base class for line parsers
	decorate any methods intendet to take part in the parsing process as LineParserMethod(). 
	the	methods will be called with three arguments:
	
	lines: a list of lines to be parsed
	eventHandler: user passed class to handle events
	events: a list of len(lines) to assign events to.
	
	return: False to flag an error, True to continue parsing
	
	"""
	__metaclass__ = LineParserMeta
	
	ParserMethodNames = []
	ID = HcID()
	
	def __init__(self):
		# gather all parser methods
		#TODO: maybe we can delay parser setup to optimize for speed?	
		ParserMethodNames = []
		for name in dir(self):
			obj = getattr(self, name)
			if getattr(obj, 'klass', None) is LineParserMethod:
				ParserMethodNames.append((obj.priority, name))
		ParserMethodNames.sort()
		self.ParserMethodNames = [i[1] for i in ParserMethodNames]
							
	def canParse(self, lines):
		"""checks if the parser can parse the lines parsed
		@return: (bool)
		"""
		return False
		
	
	def feed(self, lines, eventHandler):
		if not self.canParse(lines):
			return None
				
		myLines = [{'lineno': line['lineno'], 'chars': line['chars'], 'index': index} for index, line in enumerate(lines)]
		events = [None]*len(lines)
		eventHandler.handleParseStart(myLines)
		for name in self.ParserMethodNames:
			if not myLines:
				break		
			if not getattr(self, name)(myLines, eventHandler, events):
				break
		if myLines:
			err = 'could not parse hand (lineno %s)\n' % myLines[0]['lineno']
			err += 'line: %s\n' % myLines[0]['chars']
			err += '\n'
			err += linesToString(lines)
			raise ParseError(err, myLines[0]['lineno'])	
		
		for event in events:
			if event is not None:
				event[0](**event[1])
		eventHandler.handleParseEnd(events)
		return eventHandler
		
		
			

	
	
	
