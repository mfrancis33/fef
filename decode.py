import numpy as np
from numpy.fft import fft, ifft
import struct
import sys

if not len(sys.argv) == 2:
	print("Must have input file as first argument!")
	exit(1)

input_binary = bytearray()
raw_files = dict()

# Create binary array
try:
	with open(sys.argv[1], "rb") as f:
		while (byte := f.read(1)):
			input_binary.append(byte[0])
except:
	print("File does not exist!")
	exit(1)

# Parse list using the worst-named variables known to man
mode = "H" # current
temp = bytearray() # temp var
end_len = 0 # temp len var
bin_len = 0 # temp var (how long binary section is)
count = 0 # temp var (counting var)
file_name = ""

for byte in input_binary:
	byte = byte.to_bytes(1, byteorder="big", signed=False)
	#print(mode, end="")
	
	# Header reading
	if mode == "H":
		# Not encrypted flag
		if byte == b"\x00":
			mode = "M"
		# Encrypted flag
		elif byte == b"\x01":
			# TODO: encryption flag and things
			mode = "M"
		continue
	
	# Reading
	elif mode == "M":
		# EOS marker (check section length to verify integrity)
		if byte == b"\x45" and not len(raw_files[file_name]) == end_len: # E
			print("WARNING: file lengths do not match. Created file may be corrupt or dangerous. (" + file_name + ")")
		
		# Start of file (used to reset variables)
		elif byte == b"\x46": # F
			file_name = ""
			end_len = 0
			bin_len = 0
		
		# File name
		elif byte == b"\x4e": # N
			temp = bytearray()
			count = 0
			mode = "N"
		
		# Array length
		elif byte == b"\x4c": # L
			mode = "L"
			temp = bytearray()
			count = 0
			end_len = 0
		
		# Subarray length (real and imaginary separately)
		elif byte == b"\x6c": # l
			mode = "l"
			temp = bytearray()
			count = 0
			bin_len = 0
		
		# Start reading binary (start with real)
		elif byte == b"\x73": # s
			mode = "r"
			temp = bytearray()
			count = 0
			raw_files[file_name].append(list())
		
		# Anything else is just skipped
		continue
	
	# Getting file name
	elif mode == "N":
		# Check for end of string
		if byte == b"\x00": # null is end of string
			# Check if string is invalid
			if count == 0:
				print("WARNING: a file is missing a name. Defaulting as output.txt. File might not be txt.")
				file_name = "output.txt"
				mode = "M"
				continue
			
			# String is valid
			file_name = temp.decode(encoding="UTF-8")
			raw_files[file_name] = list()
			mode = "M"
			continue
		
		# Add byte to list
		temp.append(byte[0])
		count += 1
	
	# Getting length (end_len for actual, bin_len for binary section)
	elif mode == "L" or mode == "l":
		temp.append(byte[0])
		count += 1
		
		# Enough bytes for int
		if count > 3:
			count = 0
			# Parse length
			length = int(struct.unpack(">I", temp)[0])
			if mode == "L":
				end_len = length
			else:
				bin_len = length
			mode = "M"
		continue
	
	# Reading binary content of real numbers
	elif mode == "r" or mode == "i":
		temp.append(byte[0])
		
		# Enough bytes for double
		if len(temp) > 7:
			# Parse float
			fl = float(struct.unpack(">d", temp)[0])
			if mode == "r":
				raw_files[file_name][-1].append([fl])
				mode = "i"
			else:
				raw_files[file_name][-1][count].append(fl)
				mode = "r"
				count += 1
			temp = bytearray()
		
		# Determine if we're at end of binary section
		if count == bin_len:
			mode = "M"
		continue
	
	# Reading binary content of imaginary numbers
	else:
		print("Invalid mode: ", mode)
		break

for name, raw in raw_files.items():
	# Convert list to complex numbers
	complex_list = list()
	
	for i in raw:
		arr = []
		for j in i:
			arr.append(np.cdouble(complex(real=j[0], imag=j[1])))
		complex_list.append(np.array(arr))

	# Convert complex numbers to our actual results
	fft_reals = list()
	for ls in complex_list:
		fft_reals.append(fft(ls).real)

	file = open(name, "wb")

	for i in fft_reals:
		for j in i:
			file.write(int(round(j)).to_bytes(1, byteorder="big", signed=True))

	file.close()

print("done")
