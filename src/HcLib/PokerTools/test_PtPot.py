
import unittest
from PtPot import Pot

#************************************************************************************
# unittest for PokerTools
#************************************************************************************
class TestPot(unittest.TestCase):
	
	def test_potEmpty(self):
		p = Pot.fromPlayers((('a', 0), ('b', 0), ('c', 0)))
		self.assertEqual(p.total(), 0)
		self.assertEqual(p.height(), 0)
		self.assertEqual(sum(p.bets), 0)
		self.assertEqual(sum(p.extraBets), 0)
		self.assertEqual(len(p.sidePots), 1)
		self.assertEqual(p.players, ['a', 'b', 'c'])
		self.failIf(p.streets)
		self.failIf(p.streetOrder)
		self.failIf(p.playersAll_In)
		self.failIf(p.playersAll_InOrder)
	
	def test_addBet_noStreetInPot(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		self.assertRaises(ValueError, p.addBet, 'a', 1)	
	
	def test_addBet_insufficientStack(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		self.assertRaises(ValueError, p.addBet, 'a', 20)
		
	def test_addBet_betSizeNonPositive(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		self.assertRaises(ValueError, p.addBet, 'a', 0)	
	
	def test_addBet(self):
		p = Pot.fromPlayers((('a', 100), ('b', 200), ('c', 300)))
		p.addStreet(1)
		p.addBet('a', 10)
		self.assertEqual(p.total(), 10)
		self.assertEqual(p.height(), 10)
		self.assertEqual(p.streets[1], 10)
		self.assertEqual(sum(p.bets), 10)
		self.assertEqual(sum(p.extraBets), 0)
		self.assertEqual(len(p.sidePots), 1)
		self.failIf(p.playersAll_In)
		self.failIf(p.playersAll_InOrder)
		
	def test_addBet_all_In(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		p.addBet('a', 10)
		self.assertEqual(p.playersAll_In, {'a': 10})
		self.assertEqual(p.playersAll_InOrder, ['a'])
		
		p.addBet('b', 10)
		self.assertEqual(p.playersAll_In, {'a': 10, 'b': 10})
		self.assertEqual(p.playersAll_InOrder, ['a', 'b'])
		
	def test_addExtraBet_noStreetInPot(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		self.assertRaises(ValueError, p.addExtraBet, 'a', 5)
		
	def test_addExtraBet_onlyFirstStreetAllowed(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		p.addStreet(2)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 5)
		
	def test_addExtraBet_regularBetFirst(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 5)
		p.addBet('a', 5)
		p.addExtraBet('a', 2)
		
	def test_addExtraBet_insufficientStack(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		p.addBet('a', 5)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 20)
		
	def test_addExtraBet_betSizeNonPositive(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		p.addBet('a', 5)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 0)
		
	def test_addExtraBet_extraBetGreaterRegularBet(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 5)
		p.addBet('a', 2)
		self.assertRaises(ValueError, p.addExtraBet, 'a', 5)
	
	def test_addExtraBet(self):
		p = Pot.fromPlayers((('a', 10), ('b', 10), ('c', 10)))
		p.addStreet(1)
		p.addBet('a', 5)
		p.addExtraBet('a', 2)
		self.assertEqual(p.total(), 7)
		self.assertEqual(sum(p.bets), 5)
		self.assertEqual(sum(p.extraBets), 2)
		
	def test_sidePots(self):
		p = Pot.fromPlayers((('a', 10), ('b', 20), ('c', 30)))
		p.addStreet(1)
		p.addBet('a', 10)
		self.assertEqual(len(p.sidePots), 1)
		p.addBet('b', 20)
		self.assertEqual(len(p.sidePots), 2)
		p.addBet('c', 30)
		self.assertEqual(len(p.sidePots), 3)
		
		pot1 = p.slice(p.sidePots[0])
		self.assertEqual(pot1.height(), 10)
		self.assertEqual(pot1.total(), 30)
		
		pot2 = p.slice(p.sidePots[1], p.sidePots[0])
		self.assertEqual(pot2.height(), 10)
		self.assertEqual(pot2.total(), 20)
		
		pot3 = p.slice(p.sidePots[2], p.sidePots[1])
		self.assertEqual(pot3.height(), 10)
		self.assertEqual(pot3.total(), 10)
		
		self.assertEqual(p.playersAll_In, {'a': 10, 'b': 20, 'c': 30})
		self.assertEqual(p.playersAll_InOrder, ['a', 'b', 'c'])
		
		
	def test_addStreet_duplicateStreet(self):
		p = Pot.fromPlayers((('a', 10), ('b', 20), ('c', 30)))
		p.addStreet(1)
		self.assertRaises(ValueError, p.addStreet, 1)
		
	def test_addStreet(self):
		p = Pot.fromPlayers((('a', 10), ('b', 20), ('c', 30)))
		p.addStreet(1)
		p.addBet('a', 10)
		p.addBet('b', 10)
		p.addBet('c', 10)
		p.addStreet(2)
		p.addBet('b', 10)
		p.addBet('c', 10)
		p.addStreet(3)
		p.addBet('c', 10)
				
		self.assertEqual(len(p.streets), 3)
		
		street1 = p.slice(p.streets[1])
		self.assertEqual(street1.total(), 30)
		
		street2 = p.slice(p.streets[2], p.streets[1])
		self.assertEqual(street2.total(), 20)
		
		street3 = p.slice(p.streets[3], p.streets[2])
		self.assertEqual(street3.total(), 10)
				
		self.assertEqual(p.streets, {1:10, 2:20, 3:30})
		self.assertEqual(p.streetOrder, [1, 2, 3])
		
	def test_toCall(self):
		p = Pot.fromPlayers((('a', 10), ('b', 50), ('c', 100)))
		p.addStreet(1)
		p.addBet('a', 10)
		self.assertEqual(p.toCall('b'), 10)
		p.addBet('b', 40)
		self.assertEqual(p.toCall('c'), 40)
		
#************************************************************************************
# run unittests
#************************************************************************************
def suite():
	suite = unittest.TestSuite()
	for name, o in globals().items():
		if name.startswith('Test'):
			suite.addTest(unittest.makeSuite(o))
	return suite

def test():
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite())
		
if __name__ == '__main__': test()	
