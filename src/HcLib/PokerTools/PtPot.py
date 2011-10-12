

#************************************************************************************
#
#************************************************************************************
class Pot(object):
	"""poker pot implementation"""
		
	@classmethod
	def fromPlayers(klass, players):
		"""creates a pot from a list of (player, stack) tuples"""
		return klass([i[0] for i in players], [i[1] for i in players])
		
	def __init__(self, players, stacks, bets=None, extraBets=None, streets=None, playersAll_In=None):
		"""
		@cvar players: (list) of players
		@cvar stacks: (list) of stacks
		@cvar extraBets: (list) of extra bets
		@cvar streets: (dict) street --> height of streets
		@cvar streetOrder: (list) of streets
		@cvar playersAll_In: (dict) player --> height of players all in
		@cvar payersAll_InOrder: (list) of players all in (ordered by first being all in)
		@cvar sidePots: (list) of sidepot heights (including main pot)
		@note: treat all cvars in this class as read only. to add bets or extra bets
		or streets. always use L{addBet} or L{addExtraBet} or L{addStreet}
		"""
		self.players = players
		self.stacks = stacks
		self.bets = [0.0]*(len(players)) if bets is None else bets
		self.extraBets = [0.0]*(len(players)) if extraBets is None else extraBets
		streets = [] if streets is None else streets
		self.streets = dict(streets)
		self.streetOrder = [i[0] for i in streets]
		playersAll_In = [] if playersAll_In is None else playersAll_In
		self.playersAll_In =  dict(playersAll_In)
		self.playersAll_InOrder = [i[0] for i in playersAll_In]
		self.sidePots = []
		self.updateSidePots()
			
	def addBet(self, player, amount):
		"""adds a bet to the pot
		@param player: (any) player to add the bet for
		@param amount: (float) amount to add as bet
		@note: the pot must have at least one street
		"""
		iPlayer = self.players.index(player)
		stack = self.stacks[iPlayer]
		bets = self.bets[iPlayer]
		stack -= amount
		bets += amount
		if not self.streets: raise ValueError('pot must have a street')
		if amount <= 0: raise ValueError('amount must be > 0')
		if stack < 0: raise ValueError('player stack exhausted')
		self.stacks[iPlayer] = stack
		self.bets[iPlayer] = bets
		self.streets[self.streetOrder[-1]] = self.height()
		if not stack:
			self.playersAll_In[player] = bets
			self.playersAll_InOrder.append(player)
		self.updateSidePots()
	
	def addExtraBet(self, player, amount):
		"""adds an extra bet to the pot ..that is a bet that does count towards the 
		pot total but not to the other players (penalty for entering a table before the 
		big blind for example)
		@param player: (any) player to add the bet for
		@param amount: (float) amount to add as bet
		@note: the pot must have at least one street
		@note: extra bets can only be added on first street
		@note: extra bets must be placed after regular bets
		@note: extra bets must be <= regular bets
		@note: use this method for "player buys in" cases. example: player buys in
		on the small blind. add the big blind as regular bet and then the small blind
		as extra bet.
		"""
		iPlayer = self.players.index(player)
		stack = self.stacks[iPlayer]
		bets = self.bets[iPlayer]
		extraBets = self.extraBets[iPlayer]
		stack -= amount
		extraBets += amount
		if not self.streets: raise ValueError('pot must have a street')
		if len(self.streets) > 1: raise ValueError('extra bets can only be added on first street')
		if not bets: raise ValueError('extra bets must be added after regular bets')
		if amount <= 0:	raise ValueError('amount must be > 0')
		if extraBets > bets: raise ValueError('extra bets must be <= regular bets')
		if stack < 0: raise ValueError('player stack exhausted')
		self.stacks[iPlayer] = stack
		self.extraBets[iPlayer] = extraBets
		if not stack:
			self.playersAll_In[player] = extraBets
			self.playersAll_InOrder.append(player)
		self.updateSidePots()
	
	def addStreet(self, street):
		"""adds a street to the pot
		@param street: (any)
		"""
		if street in self.streets: raise ValueError('streat already added')
		lower = self.streets[self.streetOrder[-1]] if self.streets else 0.0
		self.streets[street] = lower
		self.streetOrder.append(street)
	
	def copy(self):
		"""copies the pot
		@return: (L{Pot})
		"""
		return self.__class__(
				self.players[:], 
				self.stacks[:], 
				bets=self.bets[:],
				extraBets=self.extraBets[:],
				streets=[(street, self.streets[street]) for street in self.streetOrder],
				playersAll_In=[(player, self.playersAll_In[player]) for player in self.playersAll_InOrder], 
				)
		
	def height(self):
		"""return the height of the side pot (that is the highest bet)
		@return: (float) height
		"""
		return max(self.bets)
		
	#TODO: check if height > lower is correct (height >= lower ?)
	def slice(self, upper, lower=None):
		"""slices the pot and returns a new pot
		@param upper: (float) upper bound to slice the pot at
		@param lower: (float) lower bound to slice the pot at. if None lower bound is 0.0
		@return: (L{Pot})
		"""
		if lower is None:
			lower = 0.0
		if lower > upper:
			upper, lower = lower, upper
		streets = []
		for street in self.streetOrder:
			height = self.streets[street]
			if height <= upper and height > lower:
				streets.append((street, height))
		playersAll_In = []
		for player in self.playersAll_InOrder:
			height = self.playersAll_In[player]
			if height <= upper and height > lower:
				playersAll_In.append((player, height))
		return self.__class__(
				self.players[:], 
				self.stacks[:], 
				bets=[self.sliceNum(n, upper, lower) for n in self.bets],
				extraBets=[self.sliceNum(n, upper, lower) for n in self.extraBets],
				streets=streets,
				playersAll_In=playersAll_In, 
				)
	
	def sliceNum(self, n, upper, lower):
		"""helper method to slice a number
		@param upper: (float) upper bound
		@param lower: (float) lower bound
		@return: (flot)
		"""
		r = n - upper
		n = n-r if r > 0 else n
		n -= lower
		return 0.0 if n < 0 else n
	
	def toCall(self, player):
		"""returns the amount a player has to call in the pot
		@param player: (any)
		@return: (float) amount
		"""
		iPlayer = self.players.index(player)
		amount = self.height() - self.bets[iPlayer]
		return 0.0 if amount < 0 else min(amount, self.stacks[iPlayer])
	
	def total(self):
		"""returns the sum of all bets (and extra bets) in the pot
		@return: (float)
		"""
		return sum(self.bets + self.extraBets)
			
	def updateSidePots(self):
		"""helper method to update list of sidepots"""
		heights = [self.height(), ]
		for height in self.playersAll_In.values():
			if height not in heights:
				heights.append(height)
		self.sidePots = sorted(heights)	
	

if __name__ == '__main__':
	p = Pot.fromPlayers((
			('a', 5),
			('b', 15),
			))

	p.addStreet('pre')
	p.addBet('a', 5)
	p.addBet('b', 10)
	print p.slice(p.streets['pre']).total()
	print p.playersAll_In

	#print p.slice(p.playersAll_In['a']).height()
	print p.sidePots
	lastI = 0
	for i in p.sidePots:
		print 1111, p.slice(i, lastI).bets
		lastI = i

	print p.copy().total()


