# Implementation of Serpent-1 cipher based on Python 1.5 implementation.
# The Serpent cipher is in the public domain.
# 
# Resources: 
#   - https://www.cl.cam.ac.uk/~fms27/serpent/serpent.py.html
#   - https://www.cl.cam.ac.uk/~rja14/Papers/serpent.pdf
#   - https://en.wikipedia.org/wiki/Serpent_(cipher)
# 
# NOTE: all "binary" strings represented in this program are little-endian by spec.
# I say "binary" because the strings are literally "0"s and "1"s as was written in the original Python implementation.

# We need this to turn numbers into bytes for outputting
import struct

# =====================================================================================================================

# Constants
PHI = 0x9e3779b9 # golden ratio, good for "randomizing"
ROUNDS = 32 # rounds

# Data tables
# These are just copied from the reference

# Each element of this list corresponds to one S-box. Each S-box in turn is
# a list of 16 integers in the range 0..15, without repetitions. Having the
# value v (say, 14) in position p (say, 0) means that if the input to that
# S-box is the pattern p (0, or 0x0) then the output will be the pattern v
# (14, or 0xe).
s_box_decimal_table = [
	[ 3, 8,15, 1,10, 6, 5,11,14,13, 4, 2, 7, 0, 9,12 ], # S0
	[15,12, 2, 7, 9, 0, 5,10, 1,11,14, 8, 6,13, 3, 4 ], # S1
	[ 8, 6, 7, 9, 3,12,10,15,13, 1,14, 4, 0,11, 5, 2 ], # S2
	[ 0,15,11, 8,12, 9, 6, 3,13, 1, 2, 4,10, 7, 5,14 ], # S3
	[ 1,15, 8, 3,12, 0,11, 6, 2, 5, 4,10, 9,14, 7,13 ], # S4
	[15, 5, 2,11, 4,10, 9,12, 0, 3,14, 8,13, 6, 7, 1 ], # S5
	[ 7, 2,12, 5, 8, 4, 6,11,14, 9, 1,15,13, 3,10, 0 ], # S6
	[ 1,13,15, 0,14, 8, 2,11, 7, 4,12,10, 9, 3, 5, 6 ], # S7
]
# NB: in serpent-0, this was a list of 32 sublists (for the 32 different
# S-boxes derived from DES). In the final version of Serpent only 8 S-boxes
# are used, with each one being reused 4 times.


# Make another version of this table as a list of dictionaries: one
# dictionary per S-box, where the value of the entry indexed by i tells you
# the output configuration when the input is i, with both the index and the
# value being bitstrings.  Make also the inverse: another list of
# dictionaries, one per S-box, where each dictionary gets the output of the
# S-box as the key and gives you the input, with both values being 4-bit
# bitstrings.
s_box_bitstring = []
s_box_bitstring_inverse = []


# The Initial and Final permutations are each represented by one list
# containing the integers in 0..127 without repetitions.  Having value v
# (say, 32) at position p (say, 1) means that the output bit at position p
# (1) comes from the input bit at position v (32).
ip_table = [
	0, 32, 64, 96, 1, 33, 65, 97, 2, 34, 66, 98, 3, 35, 67, 99,
	4, 36, 68, 100, 5, 37, 69, 101, 6, 38, 70, 102, 7, 39, 71, 103,
	8, 40, 72, 104, 9, 41, 73, 105, 10, 42, 74, 106, 11, 43, 75, 107,
	12, 44, 76, 108, 13, 45, 77, 109, 14, 46, 78, 110, 15, 47, 79, 111,
	16, 48, 80, 112, 17, 49, 81, 113, 18, 50, 82, 114, 19, 51, 83, 115,
	20, 52, 84, 116, 21, 53, 85, 117, 22, 54, 86, 118, 23, 55, 87, 119,
	24, 56, 88, 120, 25, 57, 89, 121, 26, 58, 90, 122, 27, 59, 91, 123,
	28, 60, 92, 124, 29, 61, 93, 125, 30, 62, 94, 126, 31, 63, 95, 127,
]
fp_table = [
	0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60,
	64, 68, 72, 76, 80, 84, 88, 92, 96, 100, 104, 108, 112, 116, 120, 124,
	1, 5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61,
	65, 69, 73, 77, 81, 85, 89, 93, 97, 101, 105, 109, 113, 117, 121, 125,
	2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54, 58, 62,
	66, 70, 74, 78, 82, 86, 90, 94, 98, 102, 106, 110, 114, 118, 122, 126,
	3, 7, 11, 15, 19, 23, 27, 31, 35, 39, 43, 47, 51, 55, 59, 63,
	67, 71, 75, 79, 83, 87, 91, 95, 99, 103, 107, 111, 115, 119, 123, 127,
 ]

# The Linear Transformation is represented as a list of 128 lists, one for
# each output bit. Each one of the 128 lists is composed of a variable
# number of integers in 0..127 specifying the positions of the input bits
# that must be XORed together (say, 72, 144 and 125) to yield the output
# bit corresponding to the position of that list (say, 1).
lt_table = [
	[16, 52, 56, 70, 83, 94, 105],
	[72, 114, 125],
	[2, 9, 15, 30, 76, 84, 126],
	[36, 90, 103],
	[20, 56, 60, 74, 87, 98, 109],
	[1, 76, 118],
	[2, 6, 13, 19, 34, 80, 88],
	[40, 94, 107],
	[24, 60, 64, 78, 91, 102, 113],
	[5, 80, 122],
	[6, 10, 17, 23, 38, 84, 92],
	[44, 98, 111],
	[28, 64, 68, 82, 95, 106, 117],
	[9, 84, 126],
	[10, 14, 21, 27, 42, 88, 96],
	[48, 102, 115],
	[32, 68, 72, 86, 99, 110, 121],
	[2, 13, 88],
	[14, 18, 25, 31, 46, 92, 100],
	[52, 106, 119],
	[36, 72, 76, 90, 103, 114, 125],
	[6, 17, 92],
	[18, 22, 29, 35, 50, 96, 104],
	[56, 110, 123],
	[1, 40, 76, 80, 94, 107, 118],
	[10, 21, 96],
	[22, 26, 33, 39, 54, 100, 108],
	[60, 114, 127],
	[5, 44, 80, 84, 98, 111, 122],
	[14, 25, 100],
	[26, 30, 37, 43, 58, 104, 112],
	[3, 118],
	[9, 48, 84, 88, 102, 115, 126],
	[18, 29, 104],
	[30, 34, 41, 47, 62, 108, 116],
	[7, 122],
	[2, 13, 52, 88, 92, 106, 119],
	[22, 33, 108],
	[34, 38, 45, 51, 66, 112, 120],
	[11, 126],
	[6, 17, 56, 92, 96, 110, 123],
	[26, 37, 112],
	[38, 42, 49, 55, 70, 116, 124],
	[2, 15, 76],
	[10, 21, 60, 96, 100, 114, 127],
	[30, 41, 116],
	[0, 42, 46, 53, 59, 74, 120],
	[6, 19, 80],
	[3, 14, 25, 100, 104, 118],
	[34, 45, 120],
	[4, 46, 50, 57, 63, 78, 124],
	[10, 23, 84],
	[7, 18, 29, 104, 108, 122],
	[38, 49, 124],
	[0, 8, 50, 54, 61, 67, 82],
	[14, 27, 88],
	[11, 22, 33, 108, 112, 126],
	[0, 42, 53],
	[4, 12, 54, 58, 65, 71, 86],
	[18, 31, 92],
	[2, 15, 26, 37, 76, 112, 116],
	[4, 46, 57],
	[8, 16, 58, 62, 69, 75, 90],
	[22, 35, 96],
	[6, 19, 30, 41, 80, 116, 120],
	[8, 50, 61],
	[12, 20, 62, 66, 73, 79, 94],
	[26, 39, 100],
	[10, 23, 34, 45, 84, 120, 124],
	[12, 54, 65],
	[16, 24, 66, 70, 77, 83, 98],
	[30, 43, 104],
	[0, 14, 27, 38, 49, 88, 124],
	[16, 58, 69],
	[20, 28, 70, 74, 81, 87, 102],
	[34, 47, 108],
	[0, 4, 18, 31, 42, 53, 92],
	[20, 62, 73],
	[24, 32, 74, 78, 85, 91, 106],
	[38, 51, 112],
	[4, 8, 22, 35, 46, 57, 96],
	[24, 66, 77],
	[28, 36, 78, 82, 89, 95, 110],
	[42, 55, 116],
	[8, 12, 26, 39, 50, 61, 100],
	[28, 70, 81],
	[32, 40, 82, 86, 93, 99, 114],
	[46, 59, 120],
	[12, 16, 30, 43, 54, 65, 104],
	[32, 74, 85],
	[36, 90, 103, 118],
	[50, 63, 124],
	[16, 20, 34, 47, 58, 69, 108],
	[36, 78, 89],
	[40, 94, 107, 122],
	[0, 54, 67],
	[20, 24, 38, 51, 62, 73, 112],
	[40, 82, 93],
	[44, 98, 111, 126],
	[4, 58, 71],
	[24, 28, 42, 55, 66, 77, 116],
	[44, 86, 97],
	[2, 48, 102, 115],
	[8, 62, 75],
	[28, 32, 46, 59, 70, 81, 120],
	[48, 90, 101],
	[6, 52, 106, 119],
	[12, 66, 79],
	[32, 36, 50, 63, 74, 85, 124],
	[52, 94, 105],
	[10, 56, 110, 123],
	[16, 70, 83],
	[0, 36, 40, 54, 67, 78, 89],
	[56, 98, 109],
	[14, 60, 114, 127],
	[20, 74, 87],
	[4, 40, 44, 58, 71, 82, 93],
	[60, 102, 113],
	[3, 18, 72, 114, 118, 125],
	[24, 78, 91],
	[8, 44, 48, 62, 75, 86, 97],
	[64, 106, 117],
	[1, 7, 22, 76, 118, 122],
	[28, 82, 95],
	[12, 48, 52, 66, 79, 90, 101],
	[68, 110, 121],
	[5, 11, 26, 80, 122, 126],
	[32, 86, 99],
]

# The following table is necessary for the non-bitslice decryption.
lt_table_inverse = [
	[53, 55, 72],
	[1, 5, 20, 90],
	[15, 102],
	[3, 31, 90],
	[57, 59, 76],
	[5, 9, 24, 94],
	[19, 106],
	[7, 35, 94],
	[61, 63, 80],
	[9, 13, 28, 98],
	[23, 110],
	[11, 39, 98],
	[65, 67, 84],
	[13, 17, 32, 102],
	[27, 114],
	[1, 3, 15, 20, 43, 102],
	[69, 71, 88],
	[17, 21, 36, 106],
	[1, 31, 118],
	[5, 7, 19, 24, 47, 106],
	[73, 75, 92],
	[21, 25, 40, 110],
	[5, 35, 122],
	[9, 11, 23, 28, 51, 110],
	[77, 79, 96],
	[25, 29, 44, 114],
	[9, 39, 126],
	[13, 15, 27, 32, 55, 114],
	[81, 83, 100],
	[1, 29, 33, 48, 118],
	[2, 13, 43],
	[1, 17, 19, 31, 36, 59, 118],
	[85, 87, 104],
	[5, 33, 37, 52, 122],
	[6, 17, 47],
	[5, 21, 23, 35, 40, 63, 122],
	[89, 91, 108],
	[9, 37, 41, 56, 126],
	[10, 21, 51],
	[9, 25, 27, 39, 44, 67, 126],
	[93, 95, 112],
	[2, 13, 41, 45, 60],
	[14, 25, 55],
	[2, 13, 29, 31, 43, 48, 71],
	[97, 99, 116],
	[6, 17, 45, 49, 64],
	[18, 29, 59],
	[6, 17, 33, 35, 47, 52, 75],
	[101, 103, 120],
	[10, 21, 49, 53, 68],
	[22, 33, 63],
	[10, 21, 37, 39, 51, 56, 79],
	[105, 107, 124],
	[14, 25, 53, 57, 72],
	[26, 37, 67],
	[14, 25, 41, 43, 55, 60, 83],
	[0, 109, 111],
	[18, 29, 57, 61, 76],
	[30, 41, 71],
	[18, 29, 45, 47, 59, 64, 87],
	[4, 113, 115],
	[22, 33, 61, 65, 80],
	[34, 45, 75],
	[22, 33, 49, 51, 63, 68, 91],
	[8, 117, 119],
	[26, 37, 65, 69, 84],
	[38, 49, 79],
	[26, 37, 53, 55, 67, 72, 95],
	[12, 121, 123],
	[30, 41, 69, 73, 88],
	[42, 53, 83],
	[30, 41, 57, 59, 71, 76, 99],
	[16, 125, 127],
	[34, 45, 73, 77, 92],
	[46, 57, 87],
	[34, 45, 61, 63, 75, 80, 103],
	[1, 3, 20],
	[38, 49, 77, 81, 96],
	[50, 61, 91],
	[38, 49, 65, 67, 79, 84, 107],
	[5, 7, 24],
	[42, 53, 81, 85, 100],
	[54, 65, 95],
	[42, 53, 69, 71, 83, 88, 111],
	[9, 11, 28],
	[46, 57, 85, 89, 104],
	[58, 69, 99],
	[46, 57, 73, 75, 87, 92, 115],
	[13, 15, 32],
	[50, 61, 89, 93, 108],
	[62, 73, 103],
	[50, 61, 77, 79, 91, 96, 119],
	[17, 19, 36],
	[54, 65, 93, 97, 112],
	[66, 77, 107],
	[54, 65, 81, 83, 95, 100, 123],
	[21, 23, 40],
	[58, 69, 97, 101, 116],
	[70, 81, 111],
	[58, 69, 85, 87, 99, 104, 127],
	[25, 27, 44],
	[62, 73, 101, 105, 120],
	[74, 85, 115],
	[3, 62, 73, 89, 91, 103, 108],
	[29, 31, 48],
	[66, 77, 105, 109, 124],
	[78, 89, 119],
	[7, 66, 77, 93, 95, 107, 112],
	[33, 35, 52],
	[0, 70, 81, 109, 113],
	[82, 93, 123],
	[11, 70, 81, 97, 99, 111, 116],
	[37, 39, 56],
	[4, 74, 85, 113, 117],
	[86, 97, 127],
	[15, 74, 85, 101, 103, 115, 120],
	[41, 43, 60],
	[8, 78, 89, 117, 121],
	[3, 90],
	[19, 78, 89, 105, 107, 119, 124],
	[45, 47, 64],
	[12, 82, 93, 121, 125],
	[7, 94],
	[0, 23, 82, 93, 109, 111, 123],
	[49, 51, 68],
	[1, 16, 86, 97, 125],
	[11, 98],
	[4, 27, 86, 97, 113, 115, 127],
]

# =====================================================================================================================

# Takes a 128-bit text and 256-bit user key, returns 128-bit cipher bitstring
def encrypt(plain_text, user_key):
	# Convert inputs to bitstrings
	plain_text = str_bitstring(plain_text, 128)
	user_key = str_bitstring(user_key, 256)
	
	# Get subkeys from user key
	k_hat = make_subkeys(user_key)
	
	# Encrypt input
	b_hat = ip(plain_text)
	for i in range(ROUNDS):
		b_hat = apply_round(i, b_hat, k_hat)
	
	# Apply final permutation to encrypted
	cipher_text = fp(b_hat)
	
	# Convert encrypted bitstring into actual bytes
	# cipher_bytes = bytearray()
	# for i in range(0, len(cipher_text), 8):
	# 	cipher_bytes.append(int(cipher_text[i:i+8], 2))
	# return cipher_bytes
	return reverse_str_bitstring(cipher_text)

# Takes a 128-bit encrypted text and 256-bit user key, returns 128-bit decoded string
def decrypt(cipher_text, user_key):
	# Convert inputs to bitstrings
	cipher_text = str_bitstring(cipher_text, 128)
	user_key = str_bitstring(user_key, 256)

	k_hat = make_subkeys(user_key)

	b_hat = fp_inverse(cipher_text) # b_hat_r at this stage
	for i in range(ROUNDS-1, -1, -1): # from rounds-1 down to 0 included
		b_hat = round_inverse(i, b_hat, k_hat) # Produce b_hat_i from b_hat_i+1
	# b_hat is now _0
	plain_text = ip_inverse(b_hat)

	# Convert plain text bitstring to bytes
	# return_bytes = bytearray()
	# for i in range(0, len(plain_text), 8):
	# 	return_bytes.append(int(plain_text[i:i+8], 2))
	# return return_bytes
	return reverse_str_bitstring(plain_text)

# =====================================================================================================================

def make_subkeys(user_key):
	# Turn key into 32-bit words
	# Start with prekeys -8..-1
	# Note: w-8 is least significant word
	w = {}
	for i in range(-8, 0):
		w[i] = user_key[(i+8)*32:(i+9)*32]
	# Expand to prekeys 0..131
	for i in range(132):
		w[i] = rotate_left(xor(w[i-8], w[i-5], w[i-3], w[i-1], bitstring(PHI, 32), bitstring(i, 32)), 11)
	
	# Calculate round keys
	k = {}
	for i in range(ROUNDS + 1):
		s = (ROUNDS + 3 - i) % ROUNDS # whichS in reference
		
		k[0+4*i] = ""
		k[1+4*i] = ""
		k[2+4*i] = ""
		k[3+4*i] = ""
		
		for j in range(32): # for every bit in the k and w words
			# Note: w0 and k0 are the least significant words, w99 and k99 the most.
			inp = w[0+4*i][j] + w[1+4*i][j] + w[2+4*i][j] + w[3+4*i][j]
			output = s_box(s, inp)
			for l in range(4):
				k[l+4*i] = k[l+4*i] + output[l]
	
	# Transform into 128-bit values
	K = []
	for i in range(33):
		# Note: k4i is the least significant word, k4i+3 the most.
		K.append(k[4*i] + k[4*i+1] + k[4*i+2] + k[4*i+3])
	
	# Apply initial permutation
	k_hat = []
	for i in range(33):
		k_hat.append(ip(K[i]))
	
	return k_hat

# =====================================================================================================================

def rotate_left(arr, pos):
	p = pos % len(arr)
	return arr[-p:] + arr[:-p]

def xor(*args):
	# Binary XOR on string of "0"s and "1"s
	result = args[0]
	for arg in args[1:]:
		new_result = ""
		for i in range(len(arg)):
			new_result += "0" if result[i] == arg[i] else "1"
		result = new_result
	
	return result

def bitstring(n, l):
	# Convert num to bitstring
	
	if l < 1:
		# Must have at least 1 character in a bitstring
		raise ValueError("a bitstring must have at least 1 char")
	if n < 0:
		# Only works with positive ints
		raise ValueError("bitstring representation undefined for neg numbers")
	
	# Convert num to bitstring
	result = ""
	while n > 0:
		result += "0" if n & 1 == 0 else "1"
		n >>= 1
	
	# Pad with 0s to fill rest of space if necessary
	if len(result) < l:
		result = result + ("0" * (l - len(result)))
	
	return result

def str_bitstring(s, l):
	# Convert str to bitstring if it is a string (otherwise it is probably bytes, make sure it's a bytearray)
	b = bytearray(s.encode("utf-8")) if isinstance(s, str) else bytearray(s)
	
	# Convert bytearray to actual 0's and 1's
	result = ""
	for byte in b:
		result += bitstring(byte, 8)
	
	# Pad with 0s to fill rest of space if necessary
	if len(result) < l:
		result = result + "0" * (l - len(result))
	
	return result

def reverse_bitstring(s):
	# Convert bitstring to num
	ls = list(s)
	result = 0
	while len(ls) > 0:
		result <<= 1
		result |= 0 if ls.pop() == "0" else 1
	return result

def reverse_str_bitstring(s):
	# Convert bytearray to literal bytes
	result = bytearray()
	for i in range(0, len(s), 8):
		result.append(reverse_bitstring(s[i:i+8]))
	
	return result

# =====================================================================================================================

def apply_permutation(table, inp):
	# Check to make sure input and table lengths match
	if len(inp) != len(table):
		raise ValueError("input size (%d) doesn't match perm table size (%d)" % (len(inp), len(table)))
	
	# Apply permutations
	result = ""
	for i in range(len(table)):
		result += inp[table[i]]
	
	return result

def ip(input):
	# Initial permutation
	return apply_permutation(ip_table, input)

def fp(input):
	# Final permutation
	return apply_permutation(fp_table, input)

def ip_inverse(output):
	# Reverse initial permutation
	return fp(output)

def fp_inverse(output):
	# Reverse final permutation
	return ip(output)

def lt(inp):
	# Table-based linear transformation
	
	# Check for invalid length
	if len(inp) != 128:
		raise ValueError("input to lt is not 128 bit long")
	
	# Apply transformation
	result = ""
	for i in range(len(lt_table)):
		outputBit = "0"
		for j in lt_table[i]:
			outputBit = xor(outputBit, inp[j])
		result = result + outputBit
	return result

def lt_inverse(output):
	# Inverse table-based linear transform
	
	# Check for invalid length
	if len(output) != 128:
		raise ValueError("input to inverse lt is not 128 bit long")
	
	# Apply inverse transformation
	result = ""
	for i in range(len(lt_table_inverse)):
		inputBit = "0"
		for j in lt_table_inverse[i]:
			inputBit = xor(inputBit, output[j])
		result = result + inputBit
	return result

# =====================================================================================================================

def apply_round(i, b_hati, k_hat):
	xored = xor(b_hati, k_hat[i])
	
	s_hat_i = s_hat(i, xored)
	
	b_hat_i_plus_1 = None
	if 0 <= i <= ROUNDS-2:
		b_hat_i_plus_1 = lt(s_hat_i)
	elif i == ROUNDS-1:
		b_hat_i_plus_1 = xor(s_hat_i, k_hat[ROUNDS])
	else:
		raise ValueError("round %d is out of 0..%d range" % (i, ROUNDS-1))
	
	return b_hat_i_plus_1

def round_inverse(i, b_hat_i_plus_1, k_hat):
	# Error checking
	if 0 <= i <= ROUNDS-2:
		s_hat_i = lt_inverse(b_hat_i_plus_1)
	elif i == ROUNDS-1:
		s_hat_i = xor(b_hat_i_plus_1, k_hat[ROUNDS])
	else:
		raise ValueError("round %d is out of 0..%d range" % (i, ROUNDS-1))
	
	# inverse s_hat
	xored = s_hat_inverse(i, s_hat_i)
	
	# Xor with k_hat
	b_hati = xor(xored, k_hat[i])
	
	return b_hati

def s_box(box, inp):
	# Apply S-box to string
	return s_box_bitstring[box%8][inp]

def s_box_inverse(box, output):
	return s_box_bitstring_inverse[box%8][output]

def s_hat(box, inp):
	# Apply S-boxes to bitstrings
	result = ""
	for i in range(32):
		result = result + s_box(box, inp[4*i:4*(i+1)])
	return result

def s_hat_inverse(box, output):
	result = ""
	for i in range(32):
		result = result + s_box_inverse(box, output[4*i:4*(i+1)])
	return result

# =====================================================================================================================

# Populate s_box_bitstring and s_box_bitstring_inverse
for line in s_box_decimal_table:
	dict = {}
	inverse_dict = {}
	for i in range(len(line)):
		index = bitstring(i, 4)
		value = bitstring(line[i], 4)
		dict[index] = value
		inverse_dict[value] = index
	s_box_bitstring.append(dict)
	s_box_bitstring_inverse.append(inverse_dict)
