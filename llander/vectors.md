## Vector Generator

This is what makes the Atari arcade games from this era so special -- the vectors instead of pixels!
The actual drawing is done by specialized hardware, which is well documented in
[Jed Margolin's "Secret Life of Vector Generators"](https://www.jmargolin.com/vgens/vgens.htm)
and come in two varieties: analog and digital vector generators.  Lunar Lander has the DVG,
which is built out of DACs that steer the CRT's electron beam around.

The DVG implements its own little programming language with scaling, subroutines, and brightness control.
The [Hitch-Hacker's guide to the Atari DVG](https://www.vectorlist.org/Documents/vecgen.pdf) by Philip Pemberton
has a good description of how they work, some of which is excerpted here.  The main features of the DVG are:

* 12-bit program counter
* 4 level stack
* Vector timer
* 12-bit multipliers
* 4-bit (16 level) brightness control
* 1024x1024 resolution (10-bit DACs)

Commands are 16-bits long, with the exception of `VCTR` and `LBAS`. The first nibble is the opcode so it is easy
to visually tell what is going on.

The main commands that are used in Lunar Lander are:

* `VCTR` (`0x0` - `0x9`, 32-bit) Draw long vector from the current position to the new XY position
* `LABS` (`0xA`, 32-bit) Move the beam to the new XY position and set global scale factor
* `HALT` (`0xB`) Halt the generator and blank the screen
* `JSRL` (`0xC`) Jump to a subroutine (stack is only 4-levels deep)
* `RTSL` (`0xD`) Return from subroutine
* `JMPL` (`0xE`) Jump to an address
* `SVEC` (`0xF`) Draw a short vector from the current location to a new relative XY position

The vector generator shares memory with the 6502.  It has RAM from `0x4000` - `0x47FF` and two ROM's
from `0x4800` - `0x4FFF` and `0x5000` - `0x5FFF` (in the 6502's address space).

Once the 6502 has written a "frame" to the vector generator's RAM, it drives @IO_DMAGO which tells
the vector generator to start executing from the RAM until it hits a `HLT` opcode.

```
.byte 3000 IO_DMAGO ; Active low output for starting the Digital Vector Generator
.word 26 VecRamPtr ; Address of the end of the current commands for the DVG (starts at `0x4000`)
```


