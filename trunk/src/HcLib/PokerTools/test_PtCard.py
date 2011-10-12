
import unittest
from PtCard import Card

Cards = [
		'2h','3h','4h','5h','6h','7h','8h','9h','Th','Jh','Qh','Kh','Ah',
		'2d','3d','4d','5d','6d','7d','8d','9d','Td','Jd','Qd','Kd','Ad',
		'2c','3c','4c','5c','6c','7c','8c','9c','Tc','Jc','Qc','Kc','Ac',
		'2s','3s','4s','5s','6s','7s','8s','9s','Ts','Js','Qs','Ks','As',
		]
#************************************************************************************
# unittest for PokerTools
#************************************************************************************
class TestCard(unittest.TestCase):
	
	def test_cardFromString(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(myCard).name(), myCard)
			
	def test_cardFromInt(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).name(), myCard)
		
	def test_cardValue(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).value(), i)
		
	def test_cardRank(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).rank(), i % 13)
	
	def test_cardRankName(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).rankName(), myCard[0])		
		
	def test_cardSuit(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).suit(), i / 13)	
			
	def test_cardSuitName(self):
		for i, myCard in enumerate(Cards):
			self.assertEqual(Card(i).suitName(), myCard[1])		
		
	def test_cardEqual(self):
		for i, myCard in enumerate(Cards):
			card1 = Card(i)
			for j, mCard in enumerate(Cards):
				card2 = Card(j)
				if i == j:
					self.assertEqual(card1, card2)
				else:
					self.assertNotEqual(card1, card2)
					
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
