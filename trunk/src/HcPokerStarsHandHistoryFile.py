
import codecs
import HcConfig
import HcPokerStarsParserHoldem
#************************************************************************************
#
#************************************************************************************
class PokerStarsHandHistoryFile(object):

	@classmethod
	def fromFileName(klass, fileName):
		# stars seems to have switched to utf-8 at some time. more or less a guess
		# that it used to be iso-8859-1 before.
		data = None
		fp = codecs.open(fileName, encoding='utf-8')
		try:
			data = fp.read()
			#NOTE: remove BOM if present
			if data.startswith(unicode(codecs.BOM_UTF8, 'utf-8')):
				data = data[1:]
		except UnicodeDecodeError: pass
		finally:
			fp.close()
		if data is None:
			fp = codecs.open(fileName, encoding='iso-8859-1')
			try:
				data = fp.read()
			finally:
				fp.close()
		lines = HcConfig.linesFromString(data)
		return klass(lines)
		
	@classmethod	
	def fromString(klass, data):
		lines = HcConfig.linesFromString(data)
		return klass(lines)	
		
	def __init__(self, lines):
		self._handHistories = []
		self._lines = lines
		self._parse()	
		
	#TODO: file looks like a HandHistory to us but is a 10gigs of garbage? 
	def _parse(self):
		handHistory = None
		for line in self._lines:
			chars = line['chars'].strip()
			if self.lineIsGameHeader(chars):
				handHistory = [line, ]
				continue
			elif handHistory and chars:
				handHistory.append(line)
			elif handHistory and not chars:
				self._handHistories.append(handHistory)
				handHistory = None
		if handHistory:
			self._handHistories.append(handHistory)

	def lineIsGameHeader(self, line):
		 return line.startswith('PokerStars Game #') or line.startswith('PokerStars Home Game #')
		
	def __len__(self): return len(self._handHistories)
	def __getitem__(self, i): return self._handHistories[i]
	def __iter__(self): return iter(self._handHistories)
	def lines(self): return self._lines
