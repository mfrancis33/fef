# fef
A sort of encoding/encryption test: Fourier-Encoded Files.

## What it is
Uses IFFT and FFT to encode/decode files of your choice, making them extremely bloated and unreadable to anyone except you if you know that you used this.

## What the future holds
In the future, I hope to add support for file names, multiple files, basic security, and even a way to identify if it's a FEF file. Right now, it has none of that. Also, the name FEF was created just now and isn't implemented into the program.

## How to use
With the extremely basic and unfinished state it's in, you just need Python 3.x (I'm using 3.10.6), numpy, and a CLI.

To encode a file, use `$ py encode.py your_file_here.txt output.bin` (of course, replacing `your_file_here.txt` and possibly `output.bin` with whatever file you want to encode). Boom, your file is encoded and probably several magnitudes more file space than it was originally. File size optimization was not my goal here.

To decode a file, use `$ py decode.py output.bin output.txt` (and you can replace those file names too). Your output file will be whatever you put in the second argument and should be exactly the same as the file you inputted (apart from probably some metadata, but who cares about that?).

This program literally doesn't care what file you put into it. From my testing, it works fine with both human-readable and binary files.

## How does it work?
Well that's a great question! It splits the input file into sections of bytes and then uses numpy's IFFT function to create complex numbers out of it, which are then turned into raw bytes and spat into a file with a couple of markers between sections so the program knows what it's doing. On the way back, it reads those markers and binary data back into the original file's bytes.

## Why did you make this?
For fun.
