from numpy.fft import ifft
import os
import struct
import sys

input_files = list()
output_file = ""
size = 64

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
	else:
	# Do stuff with flags
		if last_flag == "-i":
			# Check if file can be accessed, warn user if not
			if os.access(arg, os.R_OK):
				input_files.append(arg)
			else:
				print("WARNING: " + arg + " is not a file that can be accessed! Ignoring")
		elif last_flag == "-o":
			# Check to make sure we don't already have an output file
			if output_file == "":
				output_file = arg
			else:
				print("WARNING: extra output file provided (" + arg + ")! Ignoring")

if len(input_files) == 0:
	print("ERROR: no input files provided!")
	exit(1)
if output_file == "":
	print("WARNING: no output file provided! Defaulting to output.fef")

# This list will contain the complex data of every file in order
complex_data = list()

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

# Write file header (FEF, version, and encryption flag)
# Current version is 0x02
# No encryption right now (encryption flag will be 0x01)
output.write(b"FEF\x02\x00")
for i, sections in enumerate(complex_data):
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

print("done")
