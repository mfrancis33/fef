# fef
A sort of encoding/encryption test: Fourier-Encoded Files.

## What it is
Uses IFFT (the inverse of the next) and [FFT](https://en.wikipedia.org/wiki/Fast_Fourier_transform) to encode/decode files of your choice. This isn't really useful for anything, I just thought it was cool. Also, the encoded file is a lot more massive than the original file(s)

## What the future holds
Now that support for file names and multiple files has been added (and in the same day I uploaded this to GitHub!), I hope to add support for some basic security (namely "passwords" that encrypt the bytes of the data). After that, I might focus on file size optimizations, as the output files can be massive.

## How to use
To use this program, you just need Python 3.x (I'm using 3.10.6), [numpy](https://numpy.org/), and a CLI.

Here's an example of how to encode files: `$ py encode.py -i file_1.txt file_2.png -o output.fef`. All you need to do is run `encode.py` with python, place your files after the `-i` flag, and place your output file name after the `-o` flag. The `-i` flag and some files are required, although the `-o` and its corresponding output file are not.

To decode a file, use `$ py decode.py output.fef`, replacing `output.fef` with whatever you named your file. Your output files will be named the same thing as the files you encoded and ***right now the program does not check if it's overwriting files, so be careful not to lose data!!*** Not that you should lose any, unless in the time you encoded and decoded the files, you edited the original file.

This program literally doesn't care what files you put into it. From my testing, it works fine with both human-readable and binary files.

## How does it work?
If you're too lazy to look at the source code or find it to be a hideous, unreadable mess (sorry if that's the case), then this is the place to be! The program reads all the bytes in the file and turns them into signed ints. It then uses IFFT to encode them into complex numbers, which are then spat out as raw binary data into the file.

On the way back, it does the opposite: turns the raw binary data into complex numbers, uses FFT to turn them roughly back into the same numbers they were before (the difference is pretty much floating point precision errors), and turns those numbers back into the bytes of the files you encoded.

Names of the files are included, although they aren't encoded.

## Why did you make this?
For fun.
