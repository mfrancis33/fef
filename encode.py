from numpy.fft import ifft
import os
import struct
import sys

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
	# Look for flags
	if arg == "-i" or arg == "--input":
		last_flag = "-i"
	elif arg == "-o" or arg == "--output":
		last_flag = "-o"
	elif arg == "-p" or arg == "--password":
		last_flag = "-p"
	else:
	# Do stuff with flags
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
			else:
				print("WARNING: extra output file provided (" + arg + ")! Ignoring")
		# Password information
		elif last_flag == "-p":
			# Create/add password (password can be multiple words/have spaces)
			password += arg

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
# No encryption right now (encryption flag will be 0x01)
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

# Encryption (uses basic XOR encryption with password of unknown length)
if not password == "":
	# NOTE: Needs different encryption than XOR, password is shown in null sections of file (which there are a significant amount of).
	print("Encrypting file")
	print("WARNING: encryption feature is currently insecure and should not be used! (also, decode.py isn't programmed to reverse it yet)")
	# Reopen file and dump binary content into bytearray
	file_bytes = bytearray()
	with open(output_file if not output_file == "" else "output.fef", "rb") as f:
		while (byte := f.read(1)):
			file_bytes.append(byte[0])
	
	password_bytes = bytearray(password, encoding="UTF-8")
	
	# Encrypt the bytes using password XOR
	j = 0
	# First 5 bytes do not get encrypted because file header
	for i in range(5, len(file_bytes)):
		file_bytes[i] ^= password_bytes[j]
		j += 1
		j %= len(password_bytes)
	
	# Write encrypted output
	output = open(output_file if not output_file == "" else "output.fef", "wb")
	output.write(file_bytes)
	output.close()

print("Done")
