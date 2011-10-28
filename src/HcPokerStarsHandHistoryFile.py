
import codecs
import HcConfig
import HcPokerStarsConfig
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
	def fromString(klass, data):
		lines = HcConfig.linesFromString(data)
		return klass(lines, fileName='')	
		
	def __init__(self, lines, fileName=''):
		self.fileName = fileName
		self.handHistories = []
		self.lines = lines
		self.parse()	
		
	#TODO: file looks like a HandHistory to us but is a 10gigs of garbage? 
	def parse(self):
		self.handHistories = []
		for line in self.lines:
			chars = line['chars'].strip()
			if not chars: continue
			
			ID = HcPokerStarsConfig.handHistoryType((line, ))
			if not ID and not self.handHistories:
				raise HcConfig.ParseError('Couuld not parse file:', line=line, fileName=self.fileName)
			elif not ID:
				self.handHistories[-1][1].append(line)
				continue
			else:
				self.handHistories.append([ID, [line, ]])
			
	def __len__(self): return len(self.handHistories)
	def __getitem__(self, i): return self.handHistories[i]
	def __iter__(self): return iter(self.handHistories)
	def lines(self): return self.lines




