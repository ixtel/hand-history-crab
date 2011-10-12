

#************************************************************************************
#
#************************************************************************************
class Seats(object):
	SeatNameBTN = 'BTN'
	SeatNameSB = 'SB'
	SeatNameBB = 'BB'
	SeatNameUTG = 'UTG'
	SeatNameUTG1 = 'UTG1'
	SeatNameUTG2 = 'UTG2'
	SeatNameMP = 'MP'
	SeatNameMP1 = 'MP1'
	SeatNameMP2 = 'MP2'
	SeatNameCO = 'CO'
	SeatNames = {		# nPlayers --> seat names
			2: (SeatNameSB, SeatNameBB),
			3: (SeatNameBTN, SeatNameSB, SeatNameBB),
			4: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG),
			5: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameMP),
			6: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameMP, SeatNameCO),
			7: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameMP, SeatNameCO),
			8: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameMP, SeatNameMP1, SeatNameCO),
			9: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameUTG2, SeatNameMP, SeatNameMP1, SeatNameCO),
			10: (SeatNameBTN, SeatNameSB, SeatNameBB, SeatNameUTG, SeatNameUTG1, SeatNameUTG2, SeatNameMP, SeatNameMP1, SeatNameMP2, SeatNameCO),
			}
	@classmethod
	def seatName(klass, nSeats, seatNo):
		"""
		@param nSeats: (int) number of seats total
		@param seatNo: (int) index of the seat to retrieve name for. 0 == player first to act preflop
		@return: (str) seat name
		"""
		seatNames = klass.SeatNames[nSeats]
		return seatNames[seatNo]
