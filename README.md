# fef
A sort of encoding/encryption test: Fourier-Encoded Files.

## What it is
Uses IFFT (the inverse of the next) and [FFT](https://en.wikipedia.org/wiki/Fast_Fourier_transform) to encode/decode files of your choice. This is not actually very useful as the output file has a larger size than your input file(s).

## What the future holds
On the relatively small TODO list at this point is converting the encode/decode files into usable functions, adding a license, and potentially rewriting the encryption algorithm to be a lot faster (since it is pretty slow).

## How to use
To use this program, you just need the latest version of Python 3.* (I'm using 3.10.6), [numpy](https://numpy.org/), and a CLI.

Here's an example of how to encode files: `$ py encode.py -i file_1.txt file_2.png -o output.fef`. All you need to do is run `encode.py` with python, place your files after the `-i` flag, and place your output file name after the `-o` flag. The `-i` flag and some files are required, although the `-o` and its corresponding output file are not.

To decode a file, use `$ py decode.py -i output.fef`, replacing `output.fef` with whatever you named your file. Your output files will have the same name as what you originally encoded and will be located in a folder the same name as the input file. The name of the output folder can be customized with the `-o` option.

This program literally doesn't care what files you put into it. From my testing, it works fine with both human-readable and binary files.

If you want to encrypt the output files so you can't turn them back as easily, add a `-p` flag followed by a password. The same password will be used to decrypt the file, so REMEMBER THE PASSWORD!!! The `-p` flag is also used to decrypt files.

## How does it work?
If you're too lazy to look at the source code or find it to be a hideous, unreadable mess (sorry if that's the case), then this is the place to be! The program reads all the bytes in the file and turns them into signed ints. It then uses IFFT to encode them into complex numbers, which are then spat out as raw binary data into the file along with some general metadata.

On the way back, it does the opposite: turns the raw binary data into complex numbers, uses FFT to turn them roughly back into the same numbers they were before (the difference is pretty much floating point precision errors), and turns those numbers back into the bytes of the files you encoded. It also utilizes the metadata to retrieve the file names.

In terms of encryption, it encodes the file before encrypting it. The encryption algorithm used is the Serpent cipher, which came second to the Rijandel cipher to being AES. There is no particular reason as to why this particular cipher was chosen other than that it is symmetric.

## Why did you make this?
For fun.
