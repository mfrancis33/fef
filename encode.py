from numpy.fft import ifft
import struct
import sys

if len(sys.argv) <= 1:
	print("Must have input file as first argument!")
	exit(1)
elif len(sys.argv) == 2:
	print("Warning: output file not specified. Defaulting to output.bin")

size = 400
nums = list()

# Create int arrays
i = 0
try:
	with open(sys.argv[1], "rb") as f:
		while (byte := f.read(1)):
			if i == 0:
				nums.append(list())
			i += 1
			i %= size
			
			nums[-1].append(int.from_bytes(byte, byteorder="big", signed=True))
except:
	print("File does not exist!")
	exit(1)

# Convert to fourier series
fs = list()
for ls in nums:
	fs.append(ifft(ls))

# Convert to file
output = open(sys.argv[-1] if len(sys.argv) > 2 else "output.bin", "wb")
output.write(b"\x4c")
output.write(bytearray(struct.pack(">I", len(fs))))
output.write(b"\x53")
for arr in fs:
	output.write(b"\x6c")
	output.write(bytearray(struct.pack(">I", len(arr))))
	output.write(b"\x73")
	for num in arr:
		real = struct.pack(">d", float(num.real))
		imag = struct.pack(">d", float(num.imag))
		output.write(bytearray(real))
		output.write(bytearray(imag))

output.write(b"\x45")
output.close()

print("done")
