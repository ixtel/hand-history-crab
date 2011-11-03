"""example usage cases for the package"""

import __init__ as Hc
#************************************************************************************
#
#************************************************************************************
def runExample():
	
	# parse a hand history with a dedicated parser
	data = '''
	'''
		
	eventHandler = Hc.DebugHandler()
	lines = Hc.linesFromString(data)
	p = Hc.PokerStarsParserHoldemENCashGame2()
	#p = Hc.PokerStarsParserHoldemENCashGameHomeGame2()
	#p = Hc.PokerStarsParserHoldemENTourney1()
	# ..more parsers here
	eventHandler = Hc.DebugHandler()
	hand = p.feed(lines, eventHandler)
	

##runExample()
#************************************************************************************
#
#************************************************************************************
def runExample():
	
	# parse a data of an unknown type ## paste data (hand history for example) below
	data = '''	
	'''
		
	eventHandler = Hc.DebugHandler()
	lines = Hc.linesFromString(data)
	for ID, parser in Hc.Parsers.items():
		p = parser()
		try:
			hand = p.feed(lines, eventHandler)
		except Hc.ParseError:
			pass
		else:
			print '>>', ID.toString()
		

##runExample()
#************************************************************************************
def runExample():
	
	import os, operator
	
	# run over a directory and see what players we have more than 50 hands of PS holdem CG
	#WARNING: this may take some time to complete!
	directory = ''
	
	# set up a dict of parsers for later lookup
	parsers = {}
	for parser in Hc.Parsers.values():
		if parser.ID.contains(
				dataType=Hc.DataTypeHand, 
				game= Hc.GameHoldem,
				gameContext=Hc.GameContextCashGame,
				language=Hc.LanguageEN,
				):
			parsers[parser.ID] = parser()
			
	# set up a custom event handler
	class MyEventHandler(Hc.HandHoldem):
		Players = {}
		def handlePlayer(self, name='', stack=0.0, seatNo=0, seatName='', buttonOrder=0, sitsOut=False):
			if not sitsOut:
				if name not in self.Players:
					self.Players[name] = 0
				self.Players[name] += 1
				
	# run over directory
	myEventHandler = MyEventHandler()
	for root, dirs, files in os.walk(directory):
		for name in files:
			fileName = os.path.join(root, name)
			f = Hc.PokerStarsStructuredTextFile.fromFileName(fileName)
			for ID, lines in f:
				# structured text file returns an ID we can lookup to see if we have a matching parser
				parser = parsers.get(ID, None)
				if parser is None: 
					continue
				parser.feed(lines, myEventHandler)
				
	# print out results
	players = myEventHandler.Players.items()
	players.sort(key=operator.itemgetter(1), reverse=True)
	for name, nHands in players:
		if nHands > 50:
			print '%s: %s' % (name, nHands)
			
	
##runExample()
#************************************************************************************
	



