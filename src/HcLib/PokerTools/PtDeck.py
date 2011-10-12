
import random
from PtCard import Card
#************************************************************************************
#
#************************************************************************************
class Deck(object):
	"""poker card deck object"""
	__fields__ = ('cards', )
	Cards = [Card(no) for no in xrange(Card.MinCard, Card.MaxCard +1)]

	def __init__(self):
		"""creates a new odered 52 card deck"""
		self.cards = None
		self.reset()

	def reset(self):
		"""resets the deck to an ordered set of 52 cards"""
		self.cards = self.Cards[:]

	def __iter__(self):
		return iter(self._cards)

	def __len__(self): return len(self._cards)

	def shuffle(self, shuffle=random.shuffle):
		'''shuffles the deck in place
		@param shuffle: (func) function to shuffle the decs list of cards in-place
		'''
		shuffle(self.cards)

	def nextCard(self):
		"""pops and returns the next card in the deck
		@return: (L{Card})
		"""
		return self.cards.pop(0)
