
import math
#************************************************************************************
#
#************************************************************************************
def binom(n, k):
	if 0 <= k <= n:
		p = 1
		for t in xrange(min(k, n - k)):
			p = (p * (n - t)) // (t + 1)
		return float(p)
	else:
		return float(0)

# taken from: http://introcs.cs.princeton.edu/21function/ErrorFunction.java.html
def cdf(z):
	return 0.5 * (1.0 + erf(z / math.sqrt(2.0)) )

def deviation(variance):
	return math.sqrt(variance)

def distance(x, y):
	return x - y

try:
	from math import erf		# new in Python 2.7
except ImportError:
	# taken from: http://introcs.cs.princeton.edu/21function/ErrorFunction.java.html
	def erf(z):
		"""error function."""
		t = 1.0 / (1.0 + 0.5 * abs(z))
		ans = 1 - t * math.exp( -z * z - 1.26551223 +
				t * ( 1.00002368 +
				t * ( 0.37409196 +
				t * ( 0.09678418 +
				t * (-0.18628806 +
				t * ( 0.27886807 +
				t * (-1.13520398 +
				t * ( 1.48851587 +
				t * (-0.82215223 +
				t * 0.17087277)))))))))
		return ans if z >= 0 else -ans

def expectation(distribution):
	result = 0.0
	for outcome, p in distribution:
		result += p * outcome
	return result

def factorial(n):
	total = n
	while n > 1:
		total *= (n - 1)
		n -= 1
	return total

def mean(values):
	return sum(values) / float(len(values))

def normalDistribution(x, d, m, v):
	return (
		(1 / (d * math.sqrt(2 * math.pi)) ) *
		math.exp( - ( (x - m)**2 ) / (2*v) )
		)

def oddsToPct(odds):
	return 100.0 / odds
	
def oddsFromPct(pcnt):
	return (100.0 / pcnt) -1

def prob(a, b):
	return float(a) / b
	
def probComplement(p):
	return 1 - p
	
def probFromPct(pct):
	return p / 100.0
	
def probIntersection(p1, p2):
	return p1 * p2

def probToPct(p):
	return p * 100

def probUnion(p1, p2, intersection=None):
	if intersection is None:
		return p1 + p2
	return  p1 + p2 - intersection

def pct(value, base=100):
	return 100*float(value)/base
	
def pctBase(value, percent):
	return 100*float(value) / percent

def pctValue(percent, base=100):
	return float(base) / 100 * percent

def product(numbers):
	return functools.reduce(operator.mul, numbers, 1)

def variance(ev, values):
	p = [distance(i, ev)**2 for i in values]
	return sum(p) / len(p)

def variationK(ev, stdDeviation):
	return (stdDeviation / ev) if ev else stdDeviation

