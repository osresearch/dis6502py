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
.word 27 VecRamPtr ; Address of the end of the current commands for the DVG (starts at `0x4000`)
```


```
; Draw a BCD number without a leading zero
; `A` address of number on zero page
; `Y` number of digits
.func DrawNumber_no_leading_zero:
7b59  38      SEC                        ; Set carry flag and fall through into @DrawNumber

; Draw a BCD number from the zero page
; `A` address of number on zero page
; `Y` number of digits
; `C` include leading zeros (carry flag clear)
.func DrawNumber:
7b5a  08      PHP                        ; Push the status register onto the stack (save the carry flag)
7b5b  88      DEY                        ; decrement the number of digits (to compute last address)
7b5c  8438    STY GenByte_0038           ; store number of digits in genbyte
7b5e  18      CLC                        ; Clear the carry
7b5f  6538    ADC GenByte_0038           ; Add `A` to `Y-1`, which is the address of the MSB of the BCD digit
7b61  28      PLP                        ; Restore the carry flag from the stack
7b62  aa      TAX                        ; Move the starting address for the MSB digit into `X`
.label DrawNumStringLoop:
7b63  08      PHP                        ; Push the carry flag again
7b64  8637    STX GenByte_0037           ; Store the address into genbyte
7b66  b500    LDA state_00,X             ; Treat the zero page as an array and read the BCD digit
7b68  4a      LSR                        ; Shift
7b69  4a      LSR                        ; it
7b6a  4a      LSR                        ; right
7b6b  4a      LSR                        ; four times to get the upper digit from the top nibble into `A`
7b6c  28      PLP                        ; Restore the carry flag
7b6d  201878  JSR SetDigitVecPtr         ; Draw the upper digit
7b70  a538    LDA GenByte_0038           ; Do we do more digits?
7b72  d001    BNE DoLowerDigit           ; if so do the lower digit for this value
7b74  18      CLC                        ; Clear the carry (we will always do zeros now)
.label DoLowerDigit:
7b75  a637    LDX GenByte_0037           ; Get the current digit address
7b77  b500    LDA state_00,X             ; Zero-page array read for the digit
7b79  201878  JSR SetDigitVecPtr         ; Draw the lower digit
7b7c  a637    LDX GenByte_0037           ; Decrement the digit address
7b7e  ca      DEX                        ; to move to the next digit
7b7f  c638    DEC GenByte_0038           ; Decrement our digit counter
7b81  10e0    BPL DrawNumStringLoop      ; If still positive, draw more digits
7b83  60      RTS                        ; And we're done!
```

```
; Draw a single digit
; This will skip leading zeros when outputing numbers.
; `A` bottom four bits are the BCD digit to draw
; `C` include leading zeros if clear
.func SetDigitVecPtr:
7818  9004    BCC ChkSetDigitPntr        ; If carry is clear, always display the digit
781a  290f    AND #$0f                   ; If not, check to see if the bottom nibble is zero
781c  f005    BEQ DisplayDigit           ; If digit is zero, then draw character 0 which is a blank
.label ChkSetDigitPntr:
781e  290f    AND #$0f                   ; Mask out the top nibble
7820  18      CLC                        ; Clear carry
7821  6901    ADC #$01                   ; Add one to the digit, which shifts it to the correct font location
.label DisplayDigit:
7823  08      PHP                        ; Push the CPU state (preserve the carry flag?)
7824  0a      ASL                        ; Multiple the digit by 2, since the DVG uses 16-bit words
7825  a000    LDY #$00                   ; `Y` is the offset for the vector ram pointer
7827  aa      TAX                        ; `X = A`
7828  bda257  LDA CharPtrlTbl[0],X       ; Read the low-byte of the font command
782b  9127    STA (VecRamPtr),Y          ; Store it in the vector pointer at the current location
782d  bda357  LDA CharPtrlTbl_high[0],X  ; Read the high-byte of the font command
7830  c8      INY                        ; Increment `Y`
7831  9127    STA (VecRamPtr),Y          ; Store the high byte at the next location
7833  203878  JSR VecPtrUpdate           ; Add `Y` to the vector ram pointer
7836  28      PLP                        ; Restore the carry flag
7837  60      RTS                        ; Return to the caller

; Increment the vector ram command address
; `Y` number of bytes minus one added to the vector command list
.func VecPtrUpdate:
7838  98      TYA                        ; Move the number of bytes to `A`
7839  38      SEC                        ; Set the carry, which will add the one extra
783a  6527    ADC VecRamPtr              ; Add `Y+1` to the pointer
783c  8527    STA VecRamPtr              ; Store it back in the pointer
783e  9002    BCC VecPtr_no_overflow     ; If no overflow skip the increment
7840  e628    INC VecRamPtr_high         ; Overflowed, so increment the high byte
.label VecPtr_no_overflow:
7842  60      RTS                        ; Return to the caller
```

The font table is stored in the vector generator's ROM; note that all of their addresses are offset by `0x4000`
since it is mapped into the 6502 at `0x4000` but at `0x0000` in the DVG, and that all of the addresses are *words*,
not bytes, so the `CADF` command is a subroutine call to word `0xADF`, DVG address `0x15be`, or 6502 address `0x55be`

```
; The characters are stored in the order ' ', 0 - 9, A - Z
.word 57a2 CharPtrlTbl 47 ; Subroutine calls for each font character
```

Using our emulator for the DVG, we can render out this font table as an SVG:

<!-- .dvg 57a4 92 1024 32 -->
![SVG rendering of the font](images/font.svg)

Each character is it's own DVG subroutine.  For example, here is the routine that draws `A` -- you can see
that it consists of a few short vectors (command `F`) and then a `RTSL` (command `D`) to return:

```
.word 55be font_a 8 ; Character "A"
.dvg_parse 55be 16
```


