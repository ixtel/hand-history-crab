
import itertools
from PtCard import Card
from PtHand import Hand
#************************************************************************************
#
#************************************************************************************
def genHandTypes():
	"""
	@return: (list) of hand types ['AA', 'AKs', 'AKo', ... '32o', '22']
	"""
	result = []
	ranks = Card.RankNames[::-1]
	for iRank, rank in enumerate(ranks):
		result.append(rank + rank)
		for rank2 in ranks[iRank+1:]:
			result.append(rank + rank2 + 's')
			result.append(rank + rank2 + 'o')
	return result

def genHandTypeTable():
	"""creates a table of hand types
	AA   AKs   AQs  ...
	AKo  KK     ...
	...
	@return: (list)
	"""
	handTypes = genHandTypes()
	lookup = dict((rank, i) for i, rank in enumerate(Card.RankNames[::-1]))
	table = [ [None for x in xrange(13)] for y in xrange(13)]
	for handType in handTypes:
		row = lookup[handType[0]]
		col = lookup[handType[1]]
		if handType[-1] == 'o':
			table[col][row] = handType
		else:
			table[row][col] = handType
	return table

def handTypeFromHand(hand):
	"""
	@param hand: L{Hand} containing two L{Card}s
	@return:(str) hand type of the hand ('AKo' or whatevs)
	"""
	if len(hand.cards) != 2:
		raise ValueError('expected a two card hand')
	
	card0, card1  = hand.cards
	rank0, rank1 = card0.rank(), card1.rank()
	if rank0 == rank1:
		return card0.rankName() + card1.rankName()
	suit = 's' if card1.suit() == card0.suit() else 'o'
	if rank1 > rank0:
		return card1.rankName() + card0.rankName() + suit
	return card0.rankName() + card1.rankName()+ suit

def handTypeIsPair(handType):
	return len(handType) == 2

def handTypeIsSuited(handType):
	return handType[-1] == 's'

def handTypeIsOffsuit(handType):
	return handType[-1] == 'o'

def handTypeToHands(handType):
	if handTypeIsPair(handType):
		cards = [Card(handType[0] + suit) for suit in Card.SuitNames]
		return [Hand.fromCards(*cards) for cards in itertools.combinations(cards, 2)]
	elif handTypeIsSuited(handType):
		return [Hand.fromCards(Card(handType[0]+s), Card(handType[1]+s)) for s in Card.SuitNames]
	else:
		cards1 = [handType[0] + suit for suit in Card.SuitNames]
		cards2 = [handType[1] + suit for suit in Card.SuitNames]
		return [
			Hand.fromCards(Card(a), Card(b)) for (a, b) in itertools.product(cards1, cards2) if a[1] != b[1]
			]
		
def handTypeRanks(handType):
	return (Card.RankNames.index(handType[0]), Card.RankNames.index(handType[1]))
