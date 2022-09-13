import numpy as np
from numpy.fft import fft, ifft
import struct
import sys

if len(sys.argv) <= 1:
	print("Must have input file as first argument!")
	exit(1)
elif len(sys.argv) == 2:
	print("Warning: output file not specified. Defaulting to output.txt")

bn = bytearray()
raw = list()

# Create binary array
try:
	with open(sys.argv[1], "rb") as f:
		while (byte := f.read(1)):
			bn.append(byte[0])
except:
	print("File does not exist!")
	exit(1)

# Parse list
endLen = 0 # temp len var
temp = bytearray() # temp var
mode = "M" # current
i = 0   # temp var (counting var)
j = 0   # temp var (counting var)
binLen = 0   # temp var (how long binary section is)

for byte in bn:
	byte = byte.to_bytes(1, byteorder="big", signed=False)
	#print(mode, end="")
	# Reading
	if mode == "M":
		# EOS marker, but in test file is just EOF
		if byte == b"\x45":
			break
		# Array length
		elif byte == b"\x4c":
			mode = "L"
			endLen = 0
		# Subarray length (real and imaginary separately)
		elif byte == b"\x6c":
			mode = "l"
			i = 0
			binLen = 0
		# Start reading binary (start with real)
		elif byte == b"\x73":
			mode = "r"
			i = 0
			raw.append([])
		else:
			pass
		continue
	# Getting length (L for actual, endLen for binary section)
	elif mode == "L" or mode == "l":
		temp.append(byte[0])
		i += 1
		# Enough bytes for int
		if i > 3:
			i = 0
			mode = "M"
			# Parse length
			length = int(struct.unpack(">I", temp)[0])
			if mode == "L":
				endLen = length
			else:
				binLen = length
			temp = bytearray()
		continue
	# Start of numerical content (this is just i flag; do nothing)
	elif mode == "S":
		continue
	# Reading binary content of real numbers
	elif mode == "r" or mode == "i":
		temp.append(byte[0])
		# Enough bytes for double
		if len(temp) > 7:
			# Parse float
			fl = float(struct.unpack(">d", temp)[0])
			if mode == "r":
				raw[-1].append([fl])
				mode = "i"
			else:
				raw[-1][i].append(fl)
				mode = "r"
				i += 1
			temp = bytearray()
		# Determine if we're at end of binary section
		if i == binLen:
			mode = "M"
			temp = bytearray()
		continue
	# Reading binary content of imaginary numbers
	else:
		print("Invalid mode: ", mode)
		break

# Convert list to complex numbers
nums = list()

for i in raw:
	arr = []
	for j in i:
		arr.append(np.cdouble(complex(real=j[0], imag=j[1])))
	nums.append(np.array(arr))

# Convert complex numbers to our actual results
nums2 = list()
for ls in nums:
	nums2.append(fft(ls).real)

file = open(sys.argv[2] or "output.txt", "wb")

for i in nums2:
	for j in i:
		file.write(int(round(j)).to_bytes(1, byteorder="big", signed=True))

file.close()

print("done")
