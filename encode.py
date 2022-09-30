from numpy.fft import ifft
import os
import struct
import sys

import serpent

input_files = list()
output_file = ""
size = 64 # this may need to be able to change
password = ""

# Parse args
if len(sys.argv) <= 1:
	print("No arguments provided!")
	exit(1)

last_flag = ""
for arg in sys.argv:
	if arg == "encode.py":
		continue
	# Look for flags
	if arg == "-i" or arg == "--input":
		last_flag = "-i"
	elif arg == "-o" or arg == "--output":
		last_flag = "-o"
	elif arg == "-p" or arg == "--password":
		last_flag = "-p"
	# Do stuff with flags
	else:
		# Input file(s)
		if last_flag == "-i":
			# Check if file can be accessed, warn user if not
			if os.access(arg, os.R_OK):
				input_files.append(arg)
			else:
				print("WARNING: " + arg + " is not a file that can be accessed! Ignoring")
		# Output file
		elif last_flag == "-o":
			# Check to make sure we don't already have an output file
			if output_file == "":
				output_file = arg
				last_flag = ""
			else:
				print("WARNING: extra output file provided (" + arg + ")! Ignoring")
		# Password information
		elif last_flag == "-p":
			# Create/add to password (password can be multiple words/have spaces)
			password += ("" if password == "" else " ") + arg
		else:
			print("WARNING: Unknown argument provided (" + arg + ")! Ignoring")

if len(input_files) == 0:
	print("ERROR: no input files provided!")
	exit(1)
if output_file == "":
	print("WARNING: no output file provided! Defaulting to output.fef")

# This list will contain the complex data of every file in order
complex_data = list()

# Encode files
print("Parsing files")
for file in input_files:
	byte_sections = list()
	
	# Create int arrays
	i = 0
	try:
		with open(file, "rb") as f:
			while (byte := f.read(1)):
				if i == 0:
					byte_sections.append(list())
				i += 1
				i %= size
				
				byte_sections[-1].append(int.from_bytes(byte, byteorder="big", signed=True))
	except:
		# We shouldn't be here unless file access was manipulated between reads or os.access failed for some reason
		print("ERROR: Cannot open file " + str(file) + "!")
		exit(1)

	# Convert to fourier series
	complex_sections = list()
	for ls in byte_sections:
		complex_sections.append(ifft(ls))
	
	# Add to list for encoding
	complex_data.append(complex_sections)

# Convert to file
output = open(output_file if not output_file == "" else "output.fef", "wb")

print("Writing file")

# Write file header (FEF, version, and encryption flag)
# Current version is 0x03
output.write(b"FEF\x03" + (b"\x00" if password == "" else b"\x01"))
for i, sections in enumerate(complex_data):
	# Write file flag
	output.write(b"\x46") # F
	
	# Write file name
	output.write(b"\x4e") # N
	output.write(bytearray(input_files[i], encoding="UTF-8"))
	output.write(b"\x00") # null
	
	# Write length of all sections
	output.write(b"\x4c") # L
	output.write(bytearray(struct.pack(">I", len(sections))))
	output.write(b"\x53") # S
	
	# Write sections
	for arr in sections:
		# Write length of section
		output.write(b"\x6c") # l
		output.write(bytearray(struct.pack(">I", len(arr))))
		output.write(b"\x73") # s
		
		# Write section
		for num in arr:
			real = struct.pack(">d", float(num.real))
			imag = struct.pack(">d", float(num.imag))
			output.write(bytearray(real))
			output.write(bytearray(imag))

	output.write(b"\x45") # E
output.close()

# Encryption
if not password == "":
	print("Encrypting file")
	# Reopen file and dump binary content into bytearray
	file_bytes = bytearray()
	with open(output_file if not output_file == "" else "output.fef", "rb") as f:
		while (byte := f.read(1)):
			file_bytes.append(byte[0])
	
	# Encrypt 16 bytes (128 bits) at a time with 32 bytes (256 bits) of repeated key at a time
	key_o = 0 # key offset
	out_bytes = file_bytes[0:5]
	for i in range(5, len(file_bytes), 16):
		print(str(round(i / len(file_bytes) * 100, 2)) + "% ", end="\r")
		# Get section to encode
		to_encrypt = file_bytes[i : min(i+16, len(file_bytes))]
		
		# Figure out key
		key = ""
		for j in range(32):
			key += password[(key_o + j) % len(password)]
		key_o = (key_o + (32 % len(password))) % len(password)
		
		# Encryption woo
		out_bytes += serpent.encrypt(to_encrypt, key_o)
	
	print("100.0%") # erase uneven percent (since it doesn't end on 100)
	
	# Write encrypted output
	output = open(output_file if not output_file == "" else "output.fef", "wb")
	output.write(out_bytes)
	output.close()

print("Done")
