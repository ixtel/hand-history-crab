
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
def timestampFromDate(timeZone, year, month, day, hour, minute, second):
	"""converts a date to a timestamp"""
	t = calendar.timegm((int(year), int(month), int(day), int(hour), int(minute), int(second)))
	if timeZone == TimeZoneET:
		t += 18000	# ET + 5 hours == UTC
	else:
		raise ValueError('timeZone "%s" not implemented' % timeZone)
	return t

#************************************************************************************
# base objects
#************************************************************************************
class HcObjectBase(object):
	Metadata = {}
	
	@classmethod
	def metadataContains(klass, **kws):
		for name, value in kws.items():
			if name in klass.Metadata:
				if klass.Metadata[name] != value:
					return False
		return True


class ParserHandlerBase(HcObjectBase):
	
	def handleParseStart(self, data, handled):
		pass
		
	def handleParseEnd(self, data, handled):
		pass

#************************************************************************************
# hand types
#************************************************************************************
class HandHoldem(ParserHandlerBase):
	
	Metadata = {
		'dataType': DataTypeHand, 
		'game': GameHoldem,
		}
	
		
	def handleHandStart(self, 
			lines=None, 
			site=SiteNone, 
			tourneyID='',
			tourneyBuyIn=0.0,
			tourneyRake=0.0,
			tourneyBounty=0.0,
			homeGameID='',
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
Parsers = []	# list containing all parsers


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
		if newClass.Metadata:
			Parsers.append(newClass)
		return newClass
	

class LineParserBase(HcObjectBase):
	"""base class for linewise parsers
	decorate any methods intendet to take part in the parsing process as ParserMethod(). 
	the	methods will be called with two arguments:
	
	- to include methods in the parsing process decorate them as L{ParserMethod}
	- each method will be passes two parameters: (data) a list of lines to be parsed and
	  a list of events of len(lines) the method(s) will need to fill in with a tuple
	  (methodCall, kws). None events will be ignored. the method should return
	  True to continue parsing or False to flag an error. in case of an error make
	  shure the line causing the error ist the first member of (data)
		
	usage: feed() data to the parser and iterate over the returned events.
	"""
	__metaclass__ = LineParserMeta
	
	ParserMethodNames = []
	Metadata = {}
	
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
		
	
	def feed(self, lines, handler):
		if not self.canParse(lines):
			return None
				
		data = [{'lineno': lineno, 'line': line} for lineno, line in enumerate(lines)]
		handled = [None]*len(data)
		handler.handleParseStart(data, handled)
		for name in self.ParserMethodNames:
			if not data:
				break		
			if not getattr(self, name)(data, handler, handled):
				break
		if data:
			err = 'could not parse hand (lineno %s)\n' % data[0]['lineno']
			err += 'line: %s\n' % data[0]['line']
			err += '\n'
			err += '\n'.join(lines)
			raise ParseError(err, data[0]['lineno'])	
		
		for item in handled:
			if item is not None:
				item[0](**item[1])
		handler.handleParseEnd(data, handled)
		return handler
		
		
			
	
	

