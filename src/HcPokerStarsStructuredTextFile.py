
import codecs
import HcConfig

#TODO: extend sectionType() to identify more types
#************************************************************************************
#
#************************************************************************************
class PokerStarsStructuredTextFile(object):

	@classmethod
	def fromFileName(klass, fileName):
		# stars seems to have switched to utf-8 at some time. more or less a guess
		# that it used to be iso-8859-1 before.
		data = None
		fp = codecs.open(fileName, encoding='utf-8')
		try:
			data = fp.read()
		except UnicodeDecodeError: pass
		else:
			#NOTE: remove BOM(s) if present. seen unicode BOM_BE trailing game headers
			# even within HHs (no idea why), so for now we remove all BOMs unconditionally
			data = data.replace(unicode(codecs.BOM_UTF8, 'utf-8'), '')
			#NOTE: found that some files start with \x10 (TourneySumaries)
			if data.startswith('\x10'):
				data = data[1:]
		finally:
			fp.close()
		if data is None:
			fp = codecs.open(fileName, encoding='iso-8859-1')
			try:
				data = fp.read()
			finally:
				fp.close()
		lines = HcConfig.linesFromString(data)
		return klass(lines, fileName=fileName)
		
	@classmethod	
	def fromString(klass, string):
		lines = HcConfig.linesFromString(string)
		return klass(lines, fileName='')	
		
	def __init__(self, lines, fileName=''):
		self.fileName = fileName
		self.lines = lines
			
	#TODO: file looks like a HandHistory to us but is 10gigs of garbage? 
	def __iter__(self):
		ID = HcConfig.HcID
		section = ()
		for line in self.lines:
			if not line[1].strip(): continue
			#NOTE: HcConfig.HcID() objects are rather expensive, so we work on a dict here
			kws = self.headerType(line[1])
			if not kws:
				if section:
					section[1].append(line)
				else:
					section = ID(), [line, ]
			else:
				if section:
					yield section
				section = ID(**kws), [line, ]
		if section:
			yield section	
			
	# en: PokerStars Game #
	# en: PokerStars Home Game #
	# de: PokerStars - Spiel #
	# dk: PokerStars-spil #
	# es: Juego de PokerStars #
	# ...
	# PokerStars Game #1234567890: Tournament #1234567890, Freeroll  Hold'em No Limit
	def headerType(self, header):
		kws = {}
		
		if header.startswith('PokerStars '):
			
			kws['site'] = HcConfig.SitePokerStars
			if ' Home Game #' in header:
				kws['gameScope'] = HcConfig.GameScopeHomeGame
			elif ' Game #' in header:
				kws['gameScope'] = HcConfig.GameScopePublic
			else:
				return kws
			
			if " Hold'em " in header:
				kws['game'] = HcConfig.GameHoldem
			else:
				return kws
			
			kws['dataType'] = HcConfig.DataTypeHand
			kws['language'] = HcConfig.LanguageEN
			
			if ' Tournament ' in header:
				kws['gameContext'] = HcConfig.GameContextTourney
				if ' Freeroll ' in header:
					#TODO: freerolls are currently not unsupported
					return kws
				elif 'FPP ' in header:
					#TODO: FPP tourneys are currently not supported
					return kws
			else:
				if ' 8-Game ' in header:
					#TODO: 8 game is currently not supported
					return kws
				elif ' HORSE ' in header:
					#TODO: 8-game is currently not supported
					return kws
				elif '  Mixed ' in header:
					#TODO: mixed games is currently not supported
					return kws
				kws['gameContext'] = HcConfig.GameContextCashGame
					
			if '[' in header:
				kws['version'] = '2'
			else:
				kws['version'] = '1'
			
		return kws
		
#************************************************************************************
#
#************************************************************************************	
if __name__ == '__main__':
	header = ""
	p = PokerStarsStructuredTextFile.fromString(header)
	for ID, lines in p:
		print ID.toString()
	




