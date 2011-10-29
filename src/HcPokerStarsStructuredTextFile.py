
import codecs
import HcConfig
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
			#NOTE: remove BOM if present
			if data.startswith(unicode(codecs.BOM_UTF8, 'utf-8')):
				data = data[1:]
			#NOTE: found that some files (TourneySumaries) are tagged with \x10
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
		section = []
		for line in self.lines:
			chars = line['chars'].strip()
			if not chars: continue
			#NOTE: seen unicode BOM_BE trailing game headers. no idea why and what to do.
			# our implementation simply treats them as unidentified section. 
			ID = self.sectionType((line, ))
			if not ID and not section:
				section = [HcConfig.HcID(), [line, ]]
			elif not ID:
				section[1].append(line)
				continue
			else:
				if section:
					yield section
				section = [ID, [line, ]]
		if section:
			yield section	
			
	# en: PokerStars Game #
	# en: PokerStars Home Game #
	# de: PokerStars - Spiel #
	# dk: PokerStars-spil #
	# es: Juego de PokerStars #
	# ...
	# PokerStars Game #1234567890: Tournament #1234567890, Freeroll  Hold'em No Limit
	def sectionType(self, lines):
		header = lines[0]['chars']
		d = {}
		
		if header.startswith('PokerStars '):
			
			d['site'] = HcConfig.SitePokerStars
			if ' Home Game #' in header:
				d['gameScope'] = HcConfig.GameScopeHomeGame
			elif ' Game #' in header:
				d['gameScope'] = HcConfig.GameScopePublic
			else:
				return HcConfig.HcID(**d)
			
			if " Hold'em " in header:
				d['game'] = HcConfig.GameHoldem
			else:
				return HcConfig.HcID(**d)
			
			d['dataType'] = HcConfig.DataTypeHand
			d['language'] = HcConfig.LanguageEN
			
			if ' Tournament ' in header:
				d['gameContext'] = HcConfig.GameContextTourney
				if ' Freeroll ' in header:
					#TODO: freerolls are currently not unsupported
					return HcConfig.HcID(**d)
				elif 'FPP ' in header:
					#TODO: FPP tourneys are currently not supported
					return HcConfig.HcID(**d)
			else:
				if ' 8-Game ' in header:
					#TODO: 8 game is currently not supported
					return HcConfig.HcID(**d)
				elif ' HORSE ' in header:
					#TODO: 8-game is currently not supported
					return HcConfig.HcID(**d)
				elif '  Mixed ' in header:
					#TODO: mixed games is currently not supported
					return HcConfig.HcID(**d)
				d['gameContext'] = HcConfig.GameContextCashGame
					
			if '[' in header:
				d['version'] = '2'
			else:
				d['version'] = '1'
			
		return HcConfig.HcID(**d)
	
		
	
if __name__ == '__main__':
	
	s = "PokerStars Game #22583075112: Tournament #124598875, $1.00+$0.20 Hold'em No Limit - Level II (15/30) - 2008/12/03 9:33:48 ET"
	p = PokerStarsStructuredTextFile.fromString(s)
	for ID, lines in p:
		print ID.toString()
	




