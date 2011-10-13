 # -*- coding: UTF-8 -*-

import HcConfig

#NOTES:
#
# PokerStars rake (thanks PokerStars nick): 
# -----------------------------------------
# pot total gives the rake to be taken, according to [http://www.pokerstars.com/poker/room/rake/].
# rake is then taken from each pot (starting from  the main pot) when the threshold is hit.
#
# example - assume 1c for each 20c (threshold) in the pot:
# mainPot = 14
# sidePot1 = 20
# sidePot2 = 66
# total = 100
# rake = 5
#
# * mainPot does not hit the threshold so 0c are taken (remainder 14c)
# * the first 6c of sidePot1 hit the threshold of 20c so 1c is taken (remainder 14c)
# * the first 6c of sidePot 2 hit the threshold so 1c is taken and there are 60c left
#   in the pot that are raked with 3c.
#
# so mainPot is raked 0c, sidePot1 1c and sidePot2 4c.
#
#************************************************************************************
#
#************************************************************************************
CurrencySymbols = u'$€£'

GameMapping = {
		"Hold'em": HcConfig.GameHoldem,
		}

GameLimitMapping = {
		"no limit": HcConfig.GameLimitNoLimit,
		"pot limit": HcConfig.GameLimitPotLimit,
		"fixed limit": HcConfig.GameLimitFixedLimit,
		}

CurrencyMapping = {
		'': HcConfig.CurrencyNone,
		'$': HcConfig.CurrencyUSD,
		u'€': HcConfig.CurrencyEUR,
		u'£':  HcConfig.CurrencyGBP,
		
		}



