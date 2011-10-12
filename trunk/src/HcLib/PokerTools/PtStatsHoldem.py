

#************************************************************************************
#
#************************************************************************************
class StatsHoldem(object):

	def __init__(self):
		self._nSevenCardCombinations = None
		self._nNoPairCombinations = None
		self._pNoPairCombinations = None
		self._nOnePairCombinations = None
		self._pOnePairCombinations = None
		self._nTwoPairCombinations = None
		self._pTwoPairCombinations = None
		self._nThreeOfKindCombinations = None
		self._pThreeOfKindCombinations = None
		self._nStraightCombinations = None
		self._pStraightCombinations = None
		self._nFlushCombinations = None
		self._pFlushCombinations = None
		self._nFullHouseCombinations = None
		self._pFullHouseCombinations = None
		self._nFourOfKindCombinations = None
		self._pFourOfKindCombinations = None
		self._nStraightFlushCombinations = None
		self._pStraightFlushCombinations = None
		self._nRoyalFlushCombinations = None
		self._pRoyalFlushCombinations = None

		self._nFlopCombinations = None
		self._nFlopIsStraighFlush = None
		self._pFlopIsStraightFlush= None
		self._nFlopIsThreeOfKind = None
		self._pFlopIsThreeOfKind = None
		self._nFlopIsStraight = None
		self._pFlopIsStraight = None
		self._nFlopIsFlush = None
		self._pFlopIsFlush = None
		self._nFlopIsPair = None
		self._pFlopIsPair = None
		self._nFlopIsTwoSuited = None
		self._pFlopIsTwoSuited = None
		self._nFlopIsTwoConnected = None
		self._pFlopIsTwoConnected = None

		self._nTurnCombinations = None
		self._nRiverCombinations = None

		self._nStartingHands = None
		self._pStartingHand = None
		self._nPocketPairs = None
		self._pPocketPairs = None
		self._nPocketsSuited = None
		self._pPocketsSuited = None
		self._nPocketsOffsuit = None
		self._pPocketsOffsuit = None
		self._pPocketPair = None
		self._pPocketPairHigher = None


		self._nCombinationsPocketsPair = None
		self._nCombinationsPocketsSuited = None
		self._nCombinationsPocketsOffsuit = None

		self._pPocketPairFlopOvercards = None
		self._pAcesHigher = None
		self._pFlopPair = None
		self._pFlopSet = None

	def nSevenCardCombinations(self):
		"""returns the number of seven card combinations"""
		if self._nSevenCardCombinations is None:
			self._nSevenCardCombinations = binom(52, 7)
		return self._nSevenCardCombinations

	def nNoPairCombinations(self):
		"""returns the number of no pairs"""
		if self._nNoPairCombinations is None:
			nSetsOfRanks = binom(13, 7) - 8 - (2 * binom(6, 1) + 7 * binom(5, 1)) - (2 * binom(7, 2) + 8  * binom(6, 2))
			nSuits = binom(4, 1)**7 - 844
			self._nNoPairCombinations = nSetsOfRanks * nSuits
		return self._nNoPairCombinations

	def pNoPairCombinations(self):
		"""returns the probability of no pair"""
		if self._pNoPairCombinations is None:
			self._pNoPairCombinations = self.nNoPairCombinations() / self.nSevenCardCombinations()
		return self._pNoPairCombinations

	def pctNoPairCombinations(self, round_=None):
		"""returns the percent chance of no pair"""
		if round_ is None:
			return self.pNoPairCombinations() * 100
		else:
			return round(self.pNoPairCombinations() * 100, round_)

	def nOnePairCombinations(self):
		"""returns the number of a pairs"""
		if self._nOnePairCombinations is None:
			nSetsOfRanks = binom(13, 6) - 9 - (2 * binom(7, 1) + 8 * binom(6, 1))
			nSuits = binom(4, 1)**5 - 34
			nRanks = binom(6, 1) * binom(4, 2)
			self._nOnePairCombinations = nSetsOfRanks * nSuits * nRanks
		return self._nOnePairCombinations

	def pOnePairCombinations(self):
		"""returns the probability of a pair"""
		if self._pOnePairCombinations is None:
			self._pOnePairCombinations = self.nOnePairCombinations() / self.nSevenCardCombinations()
		return self._pOnePairCombinations

	def pctOnePairCombinations(self, round_=None):
		"""returns the percent chance of a pair"""
		if round_ is None:
			return self.pOnePairCombinations() * 100
		else:
			return round(self.pOnePairCombinations() * 100, round_)

	def nTwoPairCombinations(self):
		"""returns the number of two pairs"""
		if self._nTwoPairCombinations is None:
			nThreePairOneKicker = binom(13, 4) * binom(4, 3) * binom(4, 2)**3 * binom(4, 1)
			nTwoPairsThreeKickers = (binom(13, 5) -10) * binom(5, 2) * 2268
			self._nTwoPairCombinations = nThreePairOneKicker + nTwoPairsThreeKickers
		return self._nTwoPairCombinations

	def pTwoPairCombinations(self):
		"""returns the probability of a two pair"""
		if self._pTwoPairCombinations is None:
			self._pTwoPairCombinations = self.nTwoPairCombinations() / self.nSevenCardCombinations()
		return self._pTwoPairCombinations

	def pctTwoPairCombinations(self, round_=None):
		"""returns the percent chance of a two pair"""
		if round_ is None:
			return self.pTwoPairCombinations() * 100
		else:
			return round(self.pTwoPairCombinations() * 100, round_)

	def nThreeOfKindCombinations(self):
		"""returns the number of three of a kinds"""
		if self._nThreeOfKindCombinations is None:
			nSetsOfRanks = binom(13, 5) - 10
			nTripples = binom(5, 1) * binom(4, 3)
			nSuits = binom(4, 1)**4 - binom(3, 1)
			self._nThreeOfKindCombinations = nSetsOfRanks * nTripples * nSuits
		return self._nThreeOfKindCombinations

	def pThreeOfKindCombinations(self):
		"""returns the probability of a three of a kind"""
		if self._pThreeOfKindCombinations is None:
			self._pThreeOfKindCombinations = self.nThreeOfKindCombinations() / self.nSevenCardCombinations()
		return self._pThreeOfKindCombinations

	def pctThreeOfKindCombinations(self, round_=None):
		"""returns the percent chance of a three of a kind"""
		if round_ is None:
			return self.pThreeOfKindCombinations() * 100
		else:
			return round(self.pThreeOfKindCombinations() * 100, round_)

	def nStraightCombinations(self):
		"""returns the number of a straights"""
		if self._nStraightCombinations is None:
			nSetsOfRanks = binom(8, 2) + binom(9, 1) *binom(7,2)
			nSetsOfSuits = binom(4, 1)**7
			nFlushes = binom(4, 1) * (1+binom(7, 6) * binom(3, 1) + binom(7, 5) * binom(3, 1)**2)
			nSevenDistinctRanks = nSetsOfRanks * (nSetsOfSuits - nFlushes)

			nSetsOfRanks = binom(8, 1) + binom(9, 1) * binom(7, 1)
			nPairs = binom(6, 1) * binom(4, 2)
			nSetsOfSuits = binom(4, 1)**5
			nFlushs = binom(4, 1) + binom(5, 4) * binom(2, 1) * binom(3, 1)
			nPairs = binom(6, 1) * binom(4, 2)
			nSixDistinctRanks = nSetsOfRanks *  nPairs * (nSetsOfSuits - nFlushs)

			nTripples = binom(5, 1) * binom(4, 3)
			nStraightsNotFlush = binom(4, 1)**4 - binom(3, 1)
			nSetsOfRanks = 10
			nFiveDistinctRanksPlusTripple = nSetsOfRanks * nTripples * nStraightsNotFlush

			nPairs = binom(5, 2)
			nSuitsOfPairs = binom(4, 2)**2
			nSuitsNotFlush = 6 * (64 - binom(2, 1)) + 24 * (64 - 1) + 6 * 64
			nFiveDistinctRanksTwoPairs = nPairs * nPairs * nSuitsNotFlush

			self._nStraightCombinations = (
					nSevenDistinctRanks +
					nSixDistinctRanks +
					nFiveDistinctRanksPlusTripple +
					nFiveDistinctRanksTwoPairs
					)
		return self._nStraightCombinations

	def pStraightCombinations(self):
		"""returns the probability of a straight"""
		if self._pStraightCombinations is None:
			self._pStraightCombinations = self.nStraightCombinations() / self.nSevenCardCombinations()
		return self._pStraightCombinations

	def pctStraightCombinations(self, round_=None):
		"""returns the percent chance of a straight"""
		if round_ is None:
			return self.pStraightCombinations() * 100
		else:
			return round(self.pStraightCombinations() * 100, round_)

	def nFlushCombinations(self):
		"""returns the number of flushs"""
		if self._nFlushCombinations is None:
			self._nFlushCombinations = binom(4, 1) * (binom(13, 5) * binom(39, 2) + binom(13, 6) * binom(39, 1) + binom(13, 7)) - 41584
		return self._nFlushCombinations

	def pFlushCombinations(self):
		"""returns the probability of a flush"""
		if self._pFlushCombinations is None:
			self._pFlushCombinations = self.nFlushCombinations() / self.nSevenCardCombinations()
		return self._pFlushCombinations

	def pctFlushCombinations(self, round_=None):
		"""returns the percent chance of a flush"""
		if round_ is None:
			return self.pFlushCombinations() * 100
		else:
			return round(self.pFlushCombinations() * 100, round_)

	def nFullHouseCombinations(self):
		"""returns the number of full houses"""
		if self._nFullHouseCombinations is None:
			self._nFullHouseCombinations = (
						(binom(13, 1) * binom(4, 3) * binom(12, 1) * binom(4, 2) * binom(11, 2) * binom(4, 1)**2) +
						(binom(13, 2) * binom(4, 2)**2 * binom(11, 1) * binom(4, 1)) +
						(binom(13, 2) * binom(4, 3)**2 * binom(11, 1) * binom(4, 1))
						)
		return self._nFullHouseCombinations

	def pFullHouseCombinations(self):
		"""returns the probability of a full house"""
		if self._pFullHouseCombinations is None:
			self._pFullHouseCombinations = self.nFullHouseCombinations() / self.nSevenCardCombinations()
		return self._pFullHouseCombinations

	def pctFullHouseCombinations(self, round_=None):
		"""returns the percent chance of a full house"""
		if round_ is None:
			return self.pFullHouseCombinations() * 100
		else:
			return round(self.pFullHouseCombinations() * 100, round_)

	def nFourOfKindCombinations(self):
		"""returns the number of four of a kinds"""
		if self._nFourOfKindCombinations is None:
			self._nFourOfKindCombinations = binom(13, 1) * binom(48, 3)
		return self._nFourOfKindCombinations

	def pFourOfKindCombinations(self):
		"""returns the probability of a four of a kind"""
		if self._pFourOfKindCombinations is None:
			self._pFourOfKindCombinations = self.nFourOfKindCombinations() / self.nSevenCardCombinations()
		return self._pFourOfKindCombinations

	def pctFourOfKindCombinations(self, round_=None):
		"""returns the percent chance of a four of a kind"""
		if round_ is None:
			return self.pFourOfKindCombinations() * 100
		else:
			return round(self.pFourOfKindCombinations() * 100, round_)

	def nStraightFlushCombinations(self):
		"""returns the number of straight flushs"""
		if self._nStraightFlushCombinations is None:
			self._nStraightFlushCombinations = binom(4,1) * (binom(47, 2) + binom(9, 1) * binom(46, 2) )
		return self._nStraightFlushCombinations

	def pStraightFlushCombinations(self):
		"""returns the probability chance of a straight flush"""
		if self._pStraightFlushCombinations is None:
			self._pStraightFlushCombinations = self.nStraightFlushCombinations() / self.nSevenCardCombinations()
		return self._pStraightFlushCombinations

	def pctStraightFlushCombinations(self, round_=None):
		"""returns the percent chance of a straight flush"""
		if round_ is None:
			return self.pStraightFlushCombinations() * 100
		else:
			return round(self.pStraightFlushCombinations() * 100, round_)

	def nRoyalFlushCombinations(self):
		"""returns the number of royal flushs"""
		if self._nRoyalFlushCombinations is None:
			self._nRoyalFlushCombinations = 4
		return self._nRoyalFlushCombinations

	def pRoyalFlushCombinations(self):
		"""returns the probability of a royal flush"""
		if self._pRoyalFlushCombinations is None:
			self._pRoyalFlushCombinations = self.nRoyalFlushCombinations() / self.nSevenCardCombinations()
		return self._pRoyalFlushCombinations

	def pctRoyalFlushCombinations(self, round_=None):
		"""returns the percent chance of a royal flush"""
		if round_ is None:
			return self.pRoyalFlushCombinations() * 100
		else:
			return round(self.pRoyalFlushCombinations() * 100, round_)

	def nFlopCombinations(self):
		"""returns the total number of flop combinations"""
		if self._nFlopCombinations is None:
			self._nFlopCombinations = binom(52, 3)
		return self._nFlopCombinations

	#--> see: Brian Alspach --> http://www.math.sfu.ca/~alspach/comp16/
	def nFlopIsStraightFlush(self):
		"""returns the number of flops being a straight flush"""
		if self._nFlopIsStraighFlush is None:
			self._nFlopIsStraighFlush = 48
		return self._nFlopIsStraighFlush

	def pFlopIsStraighFlush(self):
		"""returns the probability of the flop being a straight flush"""
		if self._pFlopIsStraightFlush is None:
			self._pFlopIsStraightFlush = self.nFlopIsStraightFlush() / self.nFlopCombinations()
		return self._pFlopIsStraightFlush

	def pctFlopIsStraightFlush(self, round_=None):
		"""returns the percent chance of the flop being a straight flush"""
		if round_ is None:
			return self.pFlopIsStraighFlush() * 100
		else:
			return round(self.pFlopIsStraighFlush() * 100, round_)

	def nFlopIsThreeOfKind(self):
		"""returns the number of the flops being a straight"""
		if self._nFlopIsThreeOfKind is None:
			self._nFlopIsThreeOfKind = 4 * 13 	# or binom(4, 3)*13
		return self._nFlopIsThreeOfKind

	def pFlopIsThreeOfKind(self):
		"""returns the probability of the flop being a straight"""
		if self._pFlopIsThreeOfKind is None:
			self._pFlopIsThreeOfKind = self.nFlopIsThreeOfKind() / self.nFlopCombinations()
		return self._pFlopIsThreeOfKind

	def pctFlopIsThreeOfKind(self, round_=None):
		"""returns the percent chance of the flop being a three of a kind"""
		if round_ is None:
			return self.pFlopIsThreeOfKind() * 100
		else:
			return round(self.pFlopIsThreeOfKind() * 100, round_)

	def nFlopIsStraight(self):
		"""returns the number of flops being a straight"""
		if self._nFlopIsStraight is None:
			self._nFlopIsStraight = 4**3*12 - self.nFlopIsStraightFlush()
		return self._nFlopIsStraight

	def pFlopIsStraight(self):
		"""returns the probability of the flop being a straight"""
		if self._pFlopIsStraight is None:
			self._pFlopIsStraight = self.nFlopIsStraight() / self.nFlopCombinations()
		return self._pFlopIsStraight

	def pctFlopIsStraight(self, round_=None):
		"""returns the percent chance of the flop being a straight"""
		if round_ is None:
			return self.pFlopIsStraight() * 100
		else:
			return round(self.pFlopIsStraight() * 100, round_)

	def nFlopIsFlush(self):
		"""returns the number of flops being a flush"""
		if self._nFlopIsFlush is None:
			self._nFlopIsFlush = binom(13, 3) * 4 - self.nFlopIsStraightFlush()
		return self._nFlopIsFlush

	def pFlopIsFlush(self):
		"""returns the probability of the flop being a flush"""
		if self._pFlopIsFlush is None:
			self._pFlopIsFlush = self.nFlopIsFlush() / self.nFlopCombinations()
		return self._pFlopIsFlush

	def pctFlopIsFlush(self, round_=None):
		"""returns the percent chance of the flop being a flush"""
		if round_ is None:
			return self.pFlopIsFlush() * 100
		else:
			return round(self.pFlopIsFlush() * 100, round_)

	def nFlopIsPair(self):
		"""returns the number of flops being paired"""
		if self._nFlopIsPair is None:
			self._nFlopIsPair = binom(4, 2) *13*48
		return self._nFlopIsPair

	def pFlopIsPair(self):
		"""returns the probability of the flop being paired"""
		if self._pFlopIsPair is None:
			self._pFlopIsPair = self.nFlopIsPair() / self.nFlopCombinations()
		return self._pFlopIsPair

	def pctFlopIsPair(self, round_=None):
		"""returns the percent chance of the flop being paired"""
		if round_ is None:
			return self.pFlopIsPair() * 100
		else:
			return round(self.pFlopIsPair() * 100, round_)

	# 13  ways you can pick the first card * 12 you can pick the second * 39 you can pick the third * 2 combinations for the board
	def nFlopIsTwoSuited(self):
		"""returns the number of flops containng two of a suit"""
		if self._nFlopIsTwoSuited is None:
			self._nFlopIsTwoSuited = 13*12*39*2
		return self._nFlopIsTwoSuited

	def pFlopIsTwoSuited(self):
		"""returns the probability of the flop containing two of sa suit"""
		if self._pFlopIsTwoSuited is None:
			self._pFlopIsTwoSuited = self.nFlopIsTwoSuited() / self.nFlopCombinations()
		return self._pFlopIsTwoSuited

	def pctFlopIsTwoSuited(self, round_=None):
		"""returns the percent chance of the flop containing two of sa suit"""
		if round_ is None:
			return self.pFlopIsTwoSuited() * 100
		else:
			return round(self.pFlopIsTwoSuited() * 100, round_)

	#TODO: no idea how to calculate this. we take if from pFlopIsTwoConnected() for now
	def nFlopIsTwoConnected(self):
		"""returns the number of flops containing two connected cards"""
		if self._nFlopIsTwoConnected is None:
			self._nFlopIsTwoConnected = int( self.pFlopIsTwoConnected() * self.nFlopCombinations() )
		return self._nFlopIsTwoConnected

	def pFlopIsTwoConnected(self):
		"""returns the probability of the flop containing two connected cards"""
		if self._pFlopIsTwoConnected is None:
			self._pFlopIsTwoConnected = prob(6, 51)*(1-prob(6, 50) )*4
		return self._pFlopIsTwoConnected

	def pctFlopIsTwoConnected(self, round_=None):
		"""returns the percent chance of the flop containing two connected cards"""
		if round_ is None:
			return self.pFlopIsTwoConnected() * 100
		else:
			return round(self.pFlopIsTwoConnected() * 100, round_)

	#<-- Brian Alspach

	def nTurnCombinations(self):
		"""retuturns the total number of turn card combinations"""
		if self._nTurnCombinations is None:
			self._nTurnCombinations = binom(52, 4)
		return self._nTurnCombinations

	def nRiverCombinations(self):
		"""returns the total number of river card combinations"""
		if self._nRiverCombinations is None:
			self._nRiverCombinations = binom(52, 5)
		return self._nRiverCombinations

	def nStartingHands(self):
		"""returns the total number of starting hands"""
		if self._nStartingHands is None:
			self._nStartingHands = binom(52, 2)
		return self._nStartingHands

	def pStartingHand(self):
		'''returns the probability of getting dealt a specific starting hand'''
		if self._pStartingHand is None:
			self._pStartingHand = prob(1, 52)* prob(1, 51)
		return self._pStartingHand

	def pctStartingHand(self, round_=None):
		"""returns the percent chance of getting dealt a specific starting hand"""
		if round_ is None:
			return self.pStartingHand() * 100
		else:
			return round(self.pStartingHand() * 100, round_)

	def nPocketPairs(self):
		"""returns the number of pocket pairs"""
		if self._nPocketPairs is None:
			self._nPocketPairs = binom(13, 2)
		return self._nPocketPairs

	def pPocketPairs(self):
		"""returns the probability of getting dealt a pocket pair"""
		if self._pPocketPairs is None:
			self._pPocketPairs = self.nPocketPairs() / self.nStartingHands()
		return self._pPocketPairs

	def pctPocketPairs(self, round_=None):
		"""returns the percent chance of getting dealt a pocket pair"""
		if round_ is None:
			return self.pPocketPairs() * 100
		else:
			return round(self.pPocketPairs() * 100, round_)

	def nPocketsSuited(self):
		'''returns the number of suited starting hands'''
		if self._nPocketsSuited is None:
			self._nPocketsSuited = binom(13, 2) * binom(4, 1)
		return self._nPocketsSuited

	def pPocketsSuited(self):
		"""returns the probability of getting dealt a suited starting hand"""
		if self._pPocketsSuited is None:
			self._pPocketsSuited = self.nPocketsSuited() / self.nStartingHands()
		return self._pPocketsSuited

	def pctPocketsSuited(self, round_=None):
		"""returns the percent chancre of getting dealt a suited starting hand"""
		if round_ is None:
			return self.pPocketsSuited() * 100
		else:
			return round(self.pPocketsSuited() * 100, round_)

	def nPocketsOffsuit(self):
		"""returns the number of offsuited unpaired starting hands"""
		if self._nPocketsOffsuit is None:
			self._nPocketsOffsuit = binom(13, 2) * binom(4, 1) * binom(3, 1)
		return self._nPocketsOffsuit

	def pPocketsOffsuit(self):
		"""returns the probability of getting dealt an offsuited unpaired starting hand"""
		if self._pPocketsOffsuit is None:
			self._pPocketsOffsuit = self.nPocketsOffsuit() / self.nStartingHands()
		return self._pPocketsOffsuit

	def pctPocketsOffsuit(self, round_=None):
		"""returns the percent chancre of getting dealt an offsuited unpaired starting hand"""
		if round_ is None:
			return self.pPocketsOffsuit() * 100
		else:
			return round(self.pPocketsOffsuit() * 100, round_)

	def nCombinationsPocketsPair(self):
		"""returns the number of ways to form a paired starting hand"""
		if self._nCombinationsPocketsPair is None:
			self._nCombinationsPocketsPair = binom(4, 2)
		return self._nCombinationsPocketsPair

	def nCombinationsPocketsSuited(self):
		"""returns the number of ways to form a suited starting hand"""
		if self._nCombinationsPocketsSuited is None:
			self._nCombinationsPocketsSuited = binom(4, 1)
		return self._nCombinationsPocketsSuited

	def nCombinationsPocketsOffsuit(self):
		"""returns the number of ways to form an unpaired offsuit starting hand"""
		if self._nCombinationsPocketsOffsuit is None:
			self._nCombinationsPocketsOffsuit = binom(4, 1) * binom(3, 1)
		return self._nCombinationsPocketsOffsuit

	def pPocketPair(self):
		"""returns probability of getting dealt a specific pocket pair"""
		if self._pPocketPair is None:
			self._pPocketPair = self.nCombinationsPocketsPair() / self.nStartingHands()
		return self._pPocketPair

	#-->wikipedia: http://en.wikipedia.org/wiki/Poker_probability_%28Texas_hold_%27em%29

	def pctPocketPair(self, round_=None):
		"""returns percent chance of getting dealt a specific pocket pair"""
		if round_ is None:
			return self.pPocketPair() * 100
		else:
			return round(self.pPocketPair() * 100, round_)

	# calculates the probability that at least one  opponent is holding a higher pair
	def pPocketPairHigher(self, cardRank, nOponents=1):
		"""calculates probability of at least one opponent holding a better pair if you hold a pair
		@param cardRank: (int) rank of the pocket pair
		@param nOpponents: (int) number of opponents to calculate probsability for
		@return: (float) probability
		"""
		if cardRank < 0 or cardRank > 12: raise ValueError('cardRank must be in 0-12')
		return (84 - (6*(cardRank + 2))) / float(1225) * nOponents

	def pctPocketPairHigher(self, cardRank, nOponents=1):
		return self.pPocketPairHigher(self, cardRank, nOponents=nOpponents) * 100

	def pPocketPairsHigher(self):
		"""returns probability / percent chance of at least one player holding a higher pocket pair (1 - 9 opponents)
		@return: (tuple) (strPocketPair, ( (pOpponents1, pctOpponents1), (pOpponents2, ...), ..) ) for each pocket pair
		"""
		if self._pPocketPairHigher is None:
			result = []
			for rank in range(len(Card.RankNames) -2, -1, -1):
				pair = Card.RankNames[rank] * 2
				ps = []
				pp = [pair, ]
				for i in xrange(1, 10):
					p = self.pPocketPairHigher(rank, nOponents=i)
					pct = round(probToPct(p), 2)
					ps.append( (p, pct) )
				pp.append(tuple(ps))
				result.append(tuple(pp) )
			self._pPocketPairHigher = tuple(result)
		return self._pPocketPairHigher

	def pOvercardsToPair(self, cardRank, nCards):
		"""calculates probability of at least one overcard to come if you hold a pair
		@param cardRank: (int) rank of the pocket pair
		@param nCards: (int) number of cards to come
		@return: (float) probability
		"""
		if cardRank < 0 or cardRank > 12: raise ValueError('cardRank must be in 0-12')
		nOvercards = (12 - cardRank) * 4
		nBoardsWithoutOvercards = binom(52-nOvercards, nCards)
		if nBoardsWithoutOvercards:
			nBoards = binom(52, nCards)
			return (1 - (nBoardsWithoutOvercards / nBoards))
		return 1.0

	def pctOvercardsToPair(self, cardRank, nCards):
		return self.pOvercardsToPair(cardRank, nCards) * 100

	def pPocketPairFlopOvercards(self):
		"""returns probability of at least one overcard on the flop if you hold a pocketpair
		@return: (tuple) ( (strPair, probability, percentChance), ...)
		"""
		if self._pPocketPairFlopOvercards is None:
			result = []
			for rank in range(len(Card.RankNames) -2, -1, -1):
				pair = Card.RankNames[rank] * 2
				p = self.pOvercardsToPair(rank, 3)
				result.append( (pair, p, round(probToPct(p), 2)) )
			self._pPocketPairFlopOvercards = tuple(result)

		return self._pPocketPairFlopOvercards

	def pAceHigher(self, cardRank):
		"""returns the probability that an opponent has an ace with a better kicker
		@param cardRank: rank of the kicker to the ace
		"""
		rank = cardRank +2
		return (159 - (12 * rank) ) / 1225.0

	def pAcesHigher(self):
		"""returns the probability of (1-9) opponents holding an ace wih a beter kicker
		@return: (tuple) ('Ax', (pVillains1, percentChanceVillains1), (pVilainsN, percentChanceVillainsN) )
		for each Ax
		"""
		if self._pAcesHigher is None:
			result = []
			for cardRank in xrange(11, -1, -1):
				ace = ['A' + Card.RankNames[cardRank], ]
				p = self.pAceHigher(cardRank)
				players = []
				for nPlayers in xrange(1, 10):
					pp =  (1- (1 - p) ** nPlayers)
					players.append( (pp, round(probToPct(pp), 2)) )
				ace.append(tuple(players))
				result.append(tuple(ace))
			self._pAcesHigher = tuple(result)
		return self._pAcesHigher

	# <-- wikipedia

	def pFlopPair(self):
		"""returns the probability of flopping a pair"""
		if self._pFlopPair is None:
			self._pFlopPair = prob(6, 50) + prob(6, 49) + prob(6, 48)
		return self._pFlopPair

	def pctFlopPair(self):
		"""returns the percent chance of flopping a pair"""
		return round(probToPct(self.pFlopPair() ), 2)

	def pFlopSet(self):
		"""returns the probability of flopping a set"""
		if self._pFlopSet is None:
			self._pFlopSet = prob(2, 50) + prob(2, 49) + prob(2, 48)
		return self._pFlopSet

	def pctFlopSet(self):
		"""returns the percent chance of flopping a set"""
		return round(probToPct(self.pFlopSet() ), 2)

