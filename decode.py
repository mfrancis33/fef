import numpy as np
from numpy.fft import fft, ifft
import os
import struct
import sys

import serpent

input_file = ""
output_folder = ""
password = ""

# Parse args
if len(sys.argv) <= 1:
	print("ERROR: No arguments provided!")
	exit(1)

last_flag = ""
for arg in sys.argv:
	if arg == "decode.py":
		continue
	# Look for flags
	if arg == "-i" or arg == "--input":
		last_flag = "-i"
	elif arg == "-f" or arg == "--folder":
		last_flag = "-f"
	elif arg == "-p" or arg == "--password":
		last_flag = "-p"
	# Do stuff with flags
	else:
		# Input file
		if last_flag == "-i":
			# Check if user alreay put file
			if input_file == "":
				# Check if file can be accessed, warn user if not
				if os.access(arg, os.R_OK):
					input_file = arg
					last_flag = ""
				else:
					print("ERROR: " + arg + " is not a file that can be accessed!")
					exit(1)
			else:
				print("WARNING: Extra file provided (" + arg + ")! Ignoring")
		# Folder information
		elif last_flag == "-f":
			# Check if user alreay put file
			if output_folder == "":
				output_folder = arg
				last_flag = ""
			else:
				print("WARNING: Extra folder provided (" + arg + ")! Ignoring")
		# Password information
		elif last_flag == "-p":
			# Create/add to password (password can be multiple words/have spaces)
			password += ("" if password == "" else " ") + arg
		else:
			print("WARNING: Unknown argument provided (" + arg + ")! Ignoring")

input_binary = bytearray()
raw_files = dict()

# Create binary array
print("Parsing file")
try:
	with open(input_file, "rb") as f:
		if output_folder == "":
			output_folder = os.path.join(".", f.name[:f.name.rfind(".")])
		
		while (byte := f.read(1)):
			input_binary.append(byte[0])
except:
	print("ERROR: File does not exist!")
	exit(1)

# Validate file is FEF
if not bytes(input_binary[0:3]) == b"FEF":
	print("ERROR: Invalid FEF file!")
	exit(1)

# Parse version number
version = input_binary[3] # int
if version < 2 or version > 3:
	print("ERROR: Unsupported file version!")
	exit(1)

# Check for password
if input_binary[4] == 1:
	# Check if user entered password
	if password == "":
		print("WARNING: this file appears to be password encrypted. Proceed without entering a password? (this may result in corrupted files or the program failing)")
		if not input("Enter value [y/N]: ").lower() == "y":
			print("Program terminating")
			exit(0)
		# Set to null byte so that there's not nothing in the password
		password = "\x00"
	
	# Decrypt the file
	print("Decrypting file")
	
	# Decrypt 16 bytes (128 bits) at a time with 32 bytes (256 bits) of repeated key at a time
	key_o = 0 # key offset
	decoded = input_binary[0:5]
	for i in range(5, len(input_binary), 16):
		print(str(round(i / len(input_binary) * 100, 2)) + "% ", end="\r")
		# Get section to encode
		to_decrypt = input_binary[i : min(i+16, len(input_binary))]
		
		# Figure out key
		key = ""
		for j in range(32):
			key += password[(key_o + j) % len(password)]
		key_o = (key_o + (32 % len(password))) % len(password)
		
		# Encryption woo
		decoded += serpent.decrypt(to_decrypt, key_o)
	
	print("100.0%") # erase uneven percent (since it doesn't end on 100)
	input_binary = decoded

# Parse list
mode = "H" # current
temp = bytearray() # temp var
end_len = 0 # temp len var
bin_len = 0 # temp var (how long binary section is)
count = 0 # temp var (counting var)
file_name = ""

def next_generic_name():
	i = 1
	while "output" + str(i) + ".txt" in raw_files:
		i += 1
	return "output" + str(i) + ".txt"

print("Extracting data")
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
		if byte == b"E" and not len(raw_files[file_name]) == end_len:
			print("WARNING: file lengths do not match. Created file may be corrupt or dangerous. (" + file_name + ")")
		
		# Start of file (used to reset variables)
		elif byte == b"F":
			file_name = ""
			end_len = 0
			bin_len = 0
		
		# File name
		elif byte == b"N":
			temp = bytearray()
			count = 0
			mode = "N"
		
		# Array length
		elif byte == b"L":
			mode = "L"
			temp = bytearray()
			count = 0
			end_len = 0
		
		# Subarray length (real and imaginary separately)
		elif byte == b"l":
			mode = "l"
			temp = bytearray()
			count = 0
			bin_len = 0
		
		# Start reading binary (start with real)
		elif byte == b"s":
			# Check for file name
			if file_name == "":
				file_name = next_generic_name()
				print("WARNING: a file does not have a name. Defaulting to " + file_name)
				raw_files[file_name] = list()
			
			# Switch modes
			mode = "r"
			temp = bytearray()
			count = 0
			raw_files[file_name].append(list())
		
		# End of file (useful with password because extra bytes may be added)
		elif byte == b"E":
			break
		
		# Anything else is just skipped
		continue
	
	# Getting file name
	elif mode == "N":
		# Check for end of string
		if byte == b"\x00": # null is end of string
			# Check if string is invalid
			if count == 0:
				file_name = next_generic_name()
				print("WARNING: a file does not have a name. Defaulting to " + file_name)
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
		if len(temp) > 3:
			# Parse float
			fl = float(struct.unpack(">f", temp)[0])
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

# Basic output folder validity check
if not (start := output_folder[0]) == "." and not start == "/" and not start == "\\" and not ":/" in output_folder and not ":\\" in output_folder:
	start = os.path.join(".", output_folder)
if not os.path.isdir(output_folder):
	os.makedirs(output_folder)

# Convert to files
print("Writing files")
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

	file = open(os.path.join(output_folder, name), "wb")

	for i in fft_reals:
		for j in i:
			file.write(int(round(j)).to_bytes(1, byteorder="big", signed=True))

	file.close()

print("Done")
