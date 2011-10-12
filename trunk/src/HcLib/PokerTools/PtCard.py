

#************************************************************************************
#
#************************************************************************************
class Card(int):
	"""card object"""
	Ranks = range(0, 13)
	Suits = range(0, 4)
	MinCard = 0
	MaxCard = len(Ranks) * len(Suits) -1
	RankNames = '23456789TJQKA'
	SuitNames = 'hdcs'
	RankNamesDict = {
			0: ('deuce', 'deuces'),
			1: ('trey', 'treys'),
			2: ('four', 'fours'),
			3: ('five', 'fives'),
			4: ('six', 'sixes'),
			5: ('seven', 'sevens'),
			6: ('eight', 'eights'),
			7: ('nine', 'nines'),
			8: ('ten', 'tens'),
			9: ('jack', 'jacks'),
			10: ('queen', 'quens'),
			11: ('king', 'kings'),
			12: ('ace', 'aces'),
			}
	SuitNamesDict = {
			0: ('heart', 'hearts'),
			1: ('diamond', 'diamonds'),
			2: ('club', 'clubs'),
			3: ('spade', 'spades'),
			}
		
	def __new__(klass, no):
		"""creates a new card
		@param no: (int or string) can be either a string like 'Ah' or another card or an integer card value
		"""
		if isinstance(no, (int, long)):
			if no < klass.MinCard or no > klass.MaxCard:
				raise ValueError('invalid card')
		else:
			if len(no) != 2:
				raise ValueError('invalid card')
			try:
				rank = klass.RankNames.index(no[0])
				suit = klass.SuitNames.index(no[1])
			except IndexError:
				raise ValueError('invalid card')
			no = suit * len(klass.RankNames) + rank
		return int.__new__(klass, no)

	def __repr__(self):
		return '<%s.%s object %r at 0x%x>' % (__name__, self.__class__.__name__, self.name(), id(self))
	def __str__(self): return self.__repr__()
	def __unicode__(self): return self.__repr__()

	def __eq__(self, other): return self.value() == other.value()
	def __ne__(self, other): return not self.__eq__(other)
	
	def name(self):
		"""returns the string representation of the card, i.e. 'Ah'
		@return: (str) card
		"""
		return self.rankName() + self.suitName()

	def rank(self):
		"""returns the rank of the card
		@return: (int) rank
		"""
		return self % len(self.RankNames)

	def rankName(self):
		"""returns the string representation of the rank of the the card, i.e. 'A'
		@return: (str) shape
		"""
		return self.RankNames[self.rank()]

	def suit(self):
		"""returns the suite of the card
		@return: (int) suit
		"""
		return int(self / len(self.RankNames))

	def suitName(self):
		"""returns the string representation of the suit of the the card, i.e. 'h'
		@return: (str) shape
		"""
		return self.SuitNames[self.suit()]

	def value(self):
		"""returns the integer representation of the card
		@return: (int) value
		"""
		return int(self)



