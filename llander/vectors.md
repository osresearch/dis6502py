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

### Fonts and number drawing

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
7828  bda257  LDA CharPtrTbl[0],X        ; Read the low-byte of the font command
782b  9127    STA (VecRamPtr),Y          ; Store it in the vector pointer at the current location
782d  bda357  LDA CharPtrTbl_high[0],X   ; Read the high-byte of the font command
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
.word 57a2 CharPtrTbl 47 ; Subroutine calls for each font character
```

Using our emulator for the DVG, we can render out this font table as an SVG:

<!-- .dvg 57a4 47 1024 32 -->
![SVG rendering of the font](images/font.svg)

Each character is it's own DVG subroutine.  For example, here is the routine that draws `A` -- you can see
that it consists of a few short vectors (command `F`) and then a `RTSL` (command `D`) to return:

```
.dvg_parse 55be font_a 8 ; Character "`A`"
```

### Strings

Text strings are drawn as a sequence of DVG subroutine calls, each character is a DVG `JSRL` subroutine call
copied from the @CharPtrTbl to the vector generator RAM.  The strings are stored not in ASCII, but with
the offsets into the font table of the character subroutine call, and the last character in the string
has the high bit set as a terminator.

```
.word 2b draw_string_ptr ; Pointer to character in a string being copied to vector ram
```

```
; DrawString
; `X:Y` Pointer to the string to write, terminated with 0x80 on the last character
; Copies the font subroutines to @VecRamPtr
; Sets @draw_string_ptr to point to the end of the string
.func DrawString:
79f2  862c    STX draw_string_ptr_high   ; Store the pointer high
79f4  842b    STY draw_string_ptr        ; and low bytes
79f6  a900    LDA #$00                   ; for i = 0 ... strlen * 2
.label copy_next_vec_instruction:
79f8  4a      LSR                        ; halve i since we're copying 16-bit `JSRL` vector subroutine
79f9  a8      TAY                        ; calls for each letter and it is going up by two each byte
79fa  b12b    LDA (draw_string_ptr),Y    ; Read low byte from the string
79fc  8539    STA GenByte_0039           ; Cache it in gen byte
79fe  297f    AND #$7f                   ; Strings are terminated by setting the high bit
7a00  aa      TAX                        ; so strip the high bit from the letter
7a01  98      TYA                        ; move y back into a
7a02  0a      ASL                        ; and double it back to by index by words
7a03  a8      TAY                        ; and back into y (what a dance)
7a04  bda257  LDA CharPtrTbl[0],X        ; Index into the font table to get the low byte
7a07  9127    STA (VecRamPtr),Y          ; and store it in the vector ram ptr
7a09  c8      INY                        ; next byte...
7a0a  bda357  LDA CharPtrTbl_high[0],X   ; store the high byte of the font into the vector ram ptr
7a0d  9127    STA (VecRamPtr),Y          ; indexed by y
7a0f  c8      INY                        ; and increment y again since we moved two bytes
7a10  98      TYA                        ; and back into a
7a11  2439    BIT GenByte_0039           ; Test the cached version of the letter
7a13  10e3    BPL copy_next_vec_instruction ; If positive, keep copying
7a15  18      CLC                        ; Clear carry
7a16  6527    ADC VecRamPtr              ; Add number of bytes written to vector ram
7a18  8527    STA VecRamPtr              ; to the @VecRamPtr
7a1a  9002    BCC increment_char_ptr     ; Did the low byte overflow?
7a1c  e628    INC VecRamPtr_high         ; if so increment the high byte as well
.label increment_char_ptr:
7a1e  98      TYA                        ; Copy number of bytes copied to vector ram back to A
7a1f  4a      LSR                        ; Divide it by two to get the number of characters in the string
7a20  652b    ADC draw_string_ptr        ; Increase the character pointer
7a22  852b    STA draw_string_ptr        ; so it points to the end of the string
7a24  9002    BCC draw_string_return     ; did the low byte overflow?
7a26  e62c    INC draw_string_ptr_high   ; if so increment the high byte as well
.label draw_string_return:
7a28  60      RTS                        ; return to the caller
```

There are 33 strings in the game and they are all indexed by number. For English the table has the pointers,
note that string number 17 is an index into string 16 to reuse the word `DESTROYED`.

```
.ptr 692b string_table 33 ; Pointers to the English strings
.byte 69ab str_PUSH_START 10 ; 0 "PUSH START"
.byte 6979 str_LOW_ON_FUEL 11 ; 1 "LOW ON FUEL"
.byte 6984 str_OUT_OF_FUEL 11 ; 2 "OUT OF FUEL"
.byte 698f str_LOST 4 ; 3 "LOST"
.byte 699f str_INSERT_COINS 12 ; 4 "INSERT COINS"
.byte 69dd str_PER_COIN 8 ; 5 "PER COIN"
.byte 69e6 str_AUXILIARY_FUEL_TANKS_DESTROYED 30 ; 6 "AUXILIARY FUEL TANKS DESTROYED"
.byte 6a04 str_CONGRATULATIONS 15 ; 7 "CONGRATULATIONS"
.byte 6a13 str_YOU_LANDED_HARD 15 ; 8 "YOU LANDED HARD"
.byte 6a22 str_THAT_WAS_A_GREAT_LANDING 24 ; 9 "THAT WAS A GREAT LANDING"
.byte 6a3a str_THE_EAGLE_HAS_LANDED 20 ; 10 "THE EAGLE HAS LANDED"
.byte 6a4e str_THE_COLUMBIA_HAS_LANDED 23 ; 11 "THE COLUMBIA HAS LANDED"
.byte 6a65 str_YOU_HAVE_LANDED 15 ; 12 "YOU HAVE LANDED"
.byte 6a74 str_LIFE_SUPPORT_IS_GONE 20 ; 13 "LIFE SUPPORT IS GONE"
.byte 6a88 str_YOUR_TRIP_IS_ONE_WAY 20 ; 14 "YOUR TRIP IS ONE WAY"
.byte 6a9c str_YOU_ARE_HOPELESSLY_MAROONED 27 ; 15 "YOU ARE HOPELESSLY MAROONED"
.byte 6ab7 str_COMMUNICATION_SYSTEM_DESTROYED 30 ; 16 "COMMUNICATION SYSTEM DESTROYED"
.byte 6ad5 str_YOU_CREATED_A_TWO_MILE_CRATER 29 ; 18 "YOU CREATED A TWO MILE CRATER"
.byte 6af2 str_YOU_JUST_DESTROYED_A_100_MEGABUCK_LANDER 40 ; 19 "YOU JUST DESTROYED A 100 MEGABUCK LANDER"
.byte 6b1a str_THERE_WERE_NO_SURVIVORS 23 ; 20 "THERE WERE NO SURVIVORS"
.byte 69c2 str__POINTS 7 ; 21 " POINTS"
.byte 69b5 str_SELECT_OPTION 13 ; 22 "SELECT OPTION"
.byte 6993 str__FUEL_UNITS_ 12 ; 23 " FUEL UNITS "
.byte 69e5 str_X 1 ; 24 "X"
.byte 69c9 str_450 3 ; 25 "450"
.byte 69cc str_600 3 ; 26 "600"
.byte 69cf str_750 3 ; 27 "750"
.byte 69d2 str_900 3 ; 28 "900"
.byte 64ff str_1100 4 ; 29 "1100"
.byte 6503 str_1300 4 ; 30 "1300"
.byte 69d5 str_1550 4 ; 31 "1550"
.byte 69d9 str_1800 4 ; 32 "1800"
```


### Ships

```
.word 53ee twenty_subroutines 20 ; Twenty subroutine calls, maybe ships or stars?
.dvg 53ee 20 1024 1024 1
```

### Displays

Some of the displays are also generated this way.

```
```

which calls these subroutines:

```
.dvg_parse 55b2 setup_font 6 ; ???
.dvg_parse 5576 setup_display_2 8 ; ???
.dvg_parse 5586 setup_display_3 9 ; ???
.dvg_parse 5598 setup_display_4 9 ; ???
```

##
