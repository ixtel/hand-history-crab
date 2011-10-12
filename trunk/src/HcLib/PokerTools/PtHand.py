
#************************************************************************************
#
#************************************************************************************
class Hand(long):
	
	@classmethod
	def fromCards(klass, *cards):
		n = 0
		for card in cards:
			n |= 1 << card
		newClass =  long.__new__(klass, n)
		newClass.cards = cards
		return newClass
	
	def __new__(klass, n):
		"""creates a new hand
		@param no: (int or cards)
		"""
		cards = []
		n = 0
		while True:
			b = 1 << n
			if b > n:
				break
			if n & b:
				cards.append(Card(n))
			n += 1
		newClass =  long.__new__(klass, n)
		newClass.cards = cards
		return newClass
	def toString(self):
		return '[%s]' % ' '.join([card.name() for card in self.cards]) 
