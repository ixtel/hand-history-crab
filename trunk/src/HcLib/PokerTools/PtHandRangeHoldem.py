
import itertools, re
from PtCard import Card
from PtHand import Hand
from PtDeck import Deck
from PtHandTypesHoldem import (
		genHandTypes, 
		genHandTypeTable,
		handTypeToHands, 
		handTypeFromHand,
		handTypeIsPair,
		handTypeIsSuited,
		)
#************************************************************************************
#
#************************************************************************************
#NOTE: neither is this beast below 100% compatible to PokerTracker nor is it tested
# in any depth.
class HandRangeHoldem(object):
	"""wrapper class for texas holdem hand ranges
	
	you may initialize this class directly with a list of L{Hands}s or use the L{fromString}
	method to create a hand range from a standard hand range pattern. recognized patterns are:
	
	random: all hands
	JhTd: a specific card
	AA: a pair
	TT+: all pairs ten or higher
	77-KK: all pairs 77 to KK
	KTs, KTo, KT: all suited, offsuit king ten combinations
	K6s+, K6o+, K6+: all suited, offsuit kings, king 6 to king jack
	KTs-K2s, KTo-K2o, KT-K2: all suited, offsuit king combinations king deuce to king ten
	
	separate patterns by comma to form complex ranges: 'AA-99, ATs+, AJo+, 56s, 7h2c'
	
	@note: the KT (no suit qualifier) types are special to this implementation and
	only recognized on input.
	"""
	
	class ParseError(Exception): pass
	
	ReRanks = '|'.join(Card.RankNames)
	ReSuits = '|'.join(Card.SuitNames)
	ReCard = '(%s)(%s)' % (ReRanks, ReSuits)
	PatHand = re.compile('''
					\A
					(?P<card1>%s)
					(?P<card2>%s)
					\Z
					''' % (ReCard, ReCard), re.X)
	PatHandTypePair = re.compile('''
					\A
					(?P<rank>%s)
					(?P=rank)
					(?P<qualifier>\+)?
					\Z
					''' % ReRanks, re.X)
	PatHandTypePairRange = re.compile('''
					\A(?P<rank1>%s)
					(?P=rank1)
					\-
					(?P<rank2>%s)
					(?P=rank2)
					\Z
					''' % (ReRanks, ReRanks), re.X)
	PatHandTypeSuit = re.compile('''
					\A
					(?P<rank1>%s)
					(?P<rank2>%s)
					(?P<suit>s|o)?
					(?P<qualifier>\+)?
					\Z
					''' % (ReRanks, ReRanks), re.X)
	PatHandTypeSuitRange = re.compile('''
					\A
					(?P<rank1>%s)
					(?P<rank2>%s)
					(?P<suit1>s|o)?
					\-
					(?P<rank3>%s)
					(?P<rank4>%s)
					(?P<suit2>s|o)?
					\Z
					''' % (ReRanks, ReRanks, ReRanks, ReRanks), re.X)
	
	@classmethod
	def fromString(klass, string):
		"""creates a hand range from a string containg hand patterns
		@param string: (str) 
		@return: L{HandRange}
		
		"""
		handRange = klass()
		# clean string
		p = string.replace(' ', '').replace('\t', '')
		p = p.split(',')
		for s in p:
			if not s: continue
					
			if s == 'random':
				deck = Deck()
				for cards in itertools.combinations(deck.cards, 2):
					hand = Hand.fromCards(*cards)
					handRange._hands.add(hand)
				break
						
			elif s == 'suited':
				p.extend([
						'A2s+',
						'K2s+',
						'Q2s+',
						'J2s+',
						'T2s+',
						'92s+',
						'82s+',
						'72s+',
						'62s+',
						'52s+',
						'42s+',
						'32s+',
						])
				continue
				
			elif s == 'offsuit':
				p.extend([
						'A2o+',
						'K2o+',
						'Q2o+',
						'J2o+',
						'T2o+',
						'92o+',
						'82o+',
						'72o+',
						'62o+',
						'52o+',
						'42o+',
						'32o+',
						])
				continue
			
			elif s == 'broadways':
				p.extend([
						'TT+',
						'AT+',
						'KT+',
						'QT+',
						'JT+',
						])
				continue
			elif s == 'pairs':
				p.append('22+')
				continue	
						
			# substring is a hand --> 'Kh7d'
			#
			result = klass.PatHand.match(s)
			if result is not None:
				card1, card2 = Card(result.group('card1')), Card(result.group('card2'))
				hand = Hand.fromCards(card1, card2)
				handRange._hands.add(hand)
				continue
				
			# substring is a handTypePair --> 'TT' or 'TT+'
			#
			result = klass.PatHandTypePair.match(s)
			if result is not None:
				rank = result.group('rank')
				hands =  handTypeToHands(rank+rank)
				for hand in hands:
					handRange._hands.add(hand)
							
				# expand pattern if necessary
				qualifier = result.group('qualifier')
				if qualifier:
					iRank = Card.RankNames.index(rank)
					for otherRank in Card.RankNames[iRank +1:]:
						p.append(otherRank + otherRank)
				continue
								
			# substring is a handTypeSuit --> 'KTs', 'KTs+', 'KTo' or 'KT'
			#
			#NOTE: PokerTracker handles 'KT' but not 'KT+', we do
			result = klass.PatHandTypeSuit.match(s)
			if result is not None:
				rank1 = result.group('rank1')
				rank2 = result.group('rank2')
				rank1, rank2 = klass._sortedCardRanks(rank1, rank2, revert=True)
				suit = result.group('suit')
				qualifier = result.group('qualifier')
										
				# got a pair - assume typo - PokerStove does so as well (?)
				if rank1 == rank2:
					if qualifier:
						p.append('%s%s%s' % (rank1, rank1, qualifier))
					else:
						p.append('%s%s' % (rank1, rank1))
					continue
							
				if suit:
					hands = handTypeToHands(rank1+rank2+suit)
				else:
					hands = handTypeToHands(rank1+rank2+'s') + handTypeToHands(rank1+rank2+'o')
				for hand in hands:
					handRange._hands.add(hand)
							
				# expand pattern if necessary
				if qualifier:
					iRank1 = Card.RankNames.index(rank1)
					iRank2 = Card.RankNames.index(rank2)
					for otherRank in Card.RankNames[iRank2 +1:iRank1]:
						if otherRank == rank1: continue
						if suit:
							for hand in handTypeToHands(rank1 + otherRank + suit):
									handRange._hands.add(hand)
								
						else:
							for hand in handTypeToHands(rank1 + otherRank + 's'):
								handRange._hands.add(hand)
							for hand in handTypeToHands(rank1 + otherRank + 'o'):
								handRange._hands.add(hand)
				continue
				
			# substring is a handTypePairRange --> '22-TT'
			#
			result = klass.PatHandTypePairRange.match(s)
			if result is not None:
				rank1 = result.group('rank1')
				rank2 = result.group('rank2')
				rank1, rank2 = klass._sortedCardRanks(rank1, rank2, revert=False)
				iRank1 = Card.RankNames.index(rank1)
				iRank2 = Card.RankNames.index(rank2)
														
				# expand pattern
				ranks = Card.RankNames[iRank1:iRank2+1]
				for rank in ranks:
					for hand in handTypeToHands(rank + rank):
						handRange._hands.add(hand)
				continue
							
			# substring is a handTypeSuiteRange --> 'K7s-KTs', 'KT-K7', 'KTo-K7', ...
			#
			result = klass.PatHandTypeSuitRange.match(s)
			if result is not None:
				rank1 = result.group('rank1')
				rank2 = result.group('rank2')
				rank1, rank2 = klass._sortedCardRanks(rank1, rank2, revert=True)
				rank3 = result.group('rank3')
				rank4 = result.group('rank4')
				rank3, rank4 = klass._sortedCardRanks(rank3, rank4, revert=True)
				# sort rank2 and 4 once again so we get ascending ranks for expanding
				rank2, rank4 = klass._sortedCardRanks(rank2, rank4, revert=False)
				if rank1 != rank3:
					raise klass.ParseError('invalid range: %s' % s)
				# determine suit
				suit1 = result.group('suit1')
				suit2 = result.group('suit2')
				if suit1:
					suit = suit1
				elif suit2:
					suit = suit2
				else:
					suit = None
							
				# expand pattern
				iRank2 = Card.RankNames.index(rank2)
				iRank4 = Card.RankNames.index(rank4)
				ranks = Card.RankNames[iRank2:iRank4+1]
				for rank in ranks:
					if suit:
						for hand in handTypeToHands(rank1 + rank + suit):
							handRange._hands.add(hand)
						
					else:
						for hand in handTypeToHands(rank1 + rank + 's'):
							handRange._hands.add(hand)
						for hand in handTypeToHands(rank1 + rank + 'o'):
							handRange._hands.add(hand)
				continue
			
			#
			raise klass.ParseError('invalid hand pattern: %s' % s)	
		
		# finally		
		return handRange
			
	@classmethod
	def _sortedCardRanks(self, rank1, rank2, revert=False):
		iRank1 = Card.RankNames.index(rank1)
		iRank2 = Card.RankNames.index(rank2)
		if revert and iRank1 < iRank2:
			return (rank2, rank1)
		elif not revert and iRank2 < iRank1:
			return (rank2, rank1)
		return (rank1, rank2)
		
	def __init__(self, hands=None):
		"""
		@param hands: (list) or L{Hand}s or None to create an empty hand range
		"""
		self._hands = set() if hands is None else set(hands)
				
	def __contains__(self, hand):
		return hand in self._hands
		
	def __len__(self):
		return len(self._hands)
		
	def __iter__(self):
		return iter(self._hands)
		
	def toString(self):
		"""dumps the hand range to a string representing a hand range pattern
		@return: (str)
		"""

		if len(self) == 1326:
			return 'random'
		
		# precompute hand types of our hands
		handTypes = dict([(handType, []) for handType in genHandTypes()])
		for hand in self:
			handType = handTypeFromHand(hand)
			handTypes[handType].append(hand) 
		
		# dump our hands to handType table
		handTypeTable = genHandTypeTable()
		for row in handTypeTable:
			for iCol, handType in enumerate(row):
				# assign dict handTypeData to each cell
				if handTypeIsPair(handType):
					nCardsExpected = 6
					type = 'pair'
					rank = Card.RankNames.index(handType[0])
					rankSignificant = Card.RankNames.index(handType[0])
					nCardsExpected = 6
				elif handTypeIsSuited(handType):
					type = 'suited'
					nCardsExpected = 4
					rank = Card.RankNames.index(handType[0])
					rankSignificant = Card.RankNames.index(handType[1])
				else:
					type = 'offsuit'
					nCardsExpected = 12
					rank = Card.RankNames.index(handType[0])
					rankSignificant = Card.RankNames.index(handType[1])	
				row[iCol] = {
						'type': type,
						'handType': handType,
						'rank': rank,
						'rankSignificant': rankSignificant,
						'nCardsExpected': nCardsExpected,
						'hands': handTypes[handType],
						}
						
		# expand handTypeTable in traverse order
		handTypes = []
		for delta in xrange(13):
			pair = handTypeTable[delta][delta]
			handTypes.append(pair)
			suited = [handTypeTable[delta][i] for i in xrange(delta +1, 13)]
			handTypes.extend(suited)
			offsuit = [handTypeTable[i][delta] for i in xrange(delta +1, 13)]
			handTypes.extend(offsuit)
		
		# accumulate hands to ranges
		ranges = {'pair': [], 'suited': [], 'offsuit': []}
		for handTypeData in handTypes:
			rng = ranges[handTypeData['type']]
			if not handTypeData['hands']:
				continue
			if len(handTypeData['hands']) == handTypeData['nCardsExpected']:
				if not rng:
					rng.append([])
				lastSlc = rng[-1]
				if not lastSlc:
					lastSlc.append(handTypeData)
				elif lastSlc[-1]['nCardsExpected'] != len(lastSlc[-1]['hands']):
					rng.append([handTypeData,] )
				else:
					rankCurrent = handTypeData['rank']
					rankSignificantCurrent = handTypeData['rankSignificant']
					rankLast = lastSlc[-1]['rank']
					rankSignificantLast = lastSlc[-1]['rankSignificant']
					# case pairs
					if handTypeData['type'] == 'pair':
						if rankSignificantCurrent +1 == rankSignificantLast:
							lastSlc.append(handTypeData)
						else:
							rng.append([handTypeData,] )
					#case unpaired hands
					else:
						if rankLast == rankCurrent and \
								rankSignificantCurrent +1 == rankSignificantLast:
							lastSlc.append(handTypeData)
						else:
							rng.append([handTypeData,] )	
			else:
				rng.append([handTypeData,] )
				
		# process ranges
		result = []
		for rngName in ('pair', 'suited', 'offsuit'):
			rng = ranges[rngName]
			for slc in rng:
				if len(slc) > 1:
					# slice is a range of hands
					if slc[0]['type'] == 'pair' and slc[0]['rankSignificant'] == 12:
						# handle special case like: 'TT+'
						result.append( '%s+' % slc[-1]['handType'])
					elif slc[0]['rankSignificant'] +1 == slc[0]['rank']:
						# handle special case like: 'KTs+', 'KTo+'
						result.append( '%s+' % slc[-1]['handType'])				
					else:
						result.append( '%s-%s' % (slc[0]['handType'], slc[-1]['handType']))
				elif len(slc[0]['hands']) == slc[0]['nCardsExpected']:
					# slice is a single handType containing all cards for the handType
					result.append(slc[0]['handType'])
				else:
					# slice is a single HandType with not enough cards to cmplete the handType
					for hand in slc[0]['hands']:
						s = hand.toString()
						s = s.replace('[', '').replace(']', '').replace('\x20', '')
						result.append(s)
						
		return ', '.join(result)
