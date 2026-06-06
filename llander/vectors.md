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

### Vector Commands

```
.byte 3000 IO_DMAGO ; Active low output for starting the Digital Vector Generator

; Pointer to the current end of the commands for the vector generator
; Resets to the start of DVG RAM `0x4000` for each new "frame"
; should always be less than `0x4800` since that is all of the RAM for the DVG.

.word 27 VecCmdQueue ; Address of the end of the current commands for the DVG (starts at `0x4000`)
.word 2d VecCmdQueue_copy ; Another cpoy
.word 2f VecCmdQueue_copy2 ; And a third copy

; Pointer to 6502 memory that should be copied to the @VecCmdQueue
.word 64 VecPtr ; End of the  commands
```

At the start of each new frame, the vector command queue pointer will be set to point at the start of
the DVG's memory.  This is mapped at `0x4000` for the 6502, `0x0000` for the DVG.

```
; Reset the VecCmdQueue to the start of DVG vector memory at the beginning of each "frame"
.func VecCmdQueue_reset:
7e59  a940    LDA #$40                   ; VecCmdQueue = (u16*) 0x4000
7e5b  8528    STA VecCmdQueue_high       ; .
7e5d  a900    LDA #$00                   ; .
7e5f  8527    STA VecCmdQueue            ; .
7e61  60      RTS                        ; Our work is done
```

Since much of the game's assets live in 6502 ROM space, not the DVG ROM, there is a memcpy routine
to copy commands to the queue.

```
; Copy `X` bytes from 6502 memory `A:Y` to the DVG's command queue
; Updates @VecPtr with the ending address of the copy
; Updates @VecCmdQueue to point to the end of the command queue
.func VecCmd_memcpy:
7ea6  8565    STA VecPtr_high            ; VecPtr = `A:Y` to start with
7ea8  8464    STY VecPtr                 ; fall through into @vecram_memcpy_vecptr

; Copy commands from the 6502's memory to the DVG's command queue
; `X`: Length to copy (in bytes)
; Global @VecPtr Pointer to 6502 memory, will be modified to point to the end of the data copied
; Global @VecCmdQueue Tail of the DVG command queue, will be updated to point to the new end of the queue
.func VecCmd_memcpy_vecptr:
7eaa  8a      TXA                        ;
7eab  a8      TAY                        ;
7eac  88      DEY                        ; for y = len-1 .. 0:
.label vecram_memcpy_loop:
7ead  b164    LDA (VecPtr),Y             ; VecCmdQueue[Y] = VecPtr[Y]
7eaf  9127    STA (VecCmdQueue),Y        ; .
7eb1  88      DEY                        ; Y--
7eb2  10f9    BPL vecram_memcpy_loop     ; if Y >= 0, then keep copying
7eb4  8a      TXA                        ; restore original len
7eb5  18      CLC                        ; prepare for addition
7eb6  6527    ADC VecCmdQueue            ; (u16) VecCmdQueue += (u8) len
7eb8  8527    STA VecCmdQueue            ; .
7eba  9002    BCC vecram_skip_inc        ; .
7ebc  e628    INC VecCmdQueue_high       ; .
.label vecram_skip_inc:
7ebe  8a      TXA                        ; restore original len
7ebf  18      CLC                        ; prepare for addition
7ec0  6564    ADC VecPtr                 ; (u16) VecPtr += (u8) len
7ec2  8564    STA VecPtr                 ; .
7ec4  9002    BCC vecram_skip_inc2       ; .
7ec6  e665    INC VecPtr_high            ; .
.label vecram_skip_inc2:
7ec8  60      RTS                        ; Return to the caller
```

There are lots of helpers to copy short or long vector commands, as well as to set the @VecPtr pointer.

```
; Copy 8 bytes from `A:Y` to the DVG
.func vecram_memcpy_8:
7ea4  a208    LDX #$08                   ; fall through to @vecram_memcpy

; Copy 2 bytes from `A:Y` to the DVG
.func vecram_copy_short:
7ec9  a202    LDX #$02                   ; X = 2
7ecb  d0d9    BNE VecCmd_memcpy          ; always tail call to vecram_memcpy

; Copy 4 bytes from `A:Y` to the DVG
.func vecram_copy_long:
7ecd  a204    LDX #$04                   ; X = 4
7ecf  d0d5    BNE VecCmd_memcpy          ; always tail call to vecram_memcpy

; Copy 4 bytes from @VecPtr to the DVG
.func vecram_memcpy_4:
7ed1  a204    LDX #$04                   ; X = 4
7ed3  d0d5    BNE VecCmd_memcpy_vecptr   ; always tail call to vecram_memcpy_vecptr
```



```
; Reset the vector generator to a scale of 7 with the beam at 0,0
.func vecgen_init_screen:
7f10  a955    LDA #$55                   ; `A:Y` = @vecgen_init_screen_cmd
7f12  a0ae    LDY #$ae                   ; .
7f14  4ccd7e  JMP vecram_copy_long       ; tail call to @vecram_copy_long
```

```
.dvg_parse 55ae vecgen_init_screen_cmd 2 ; Command to reset the screen
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
782b  9127    STA (VecCmdQueue),Y        ; Store it in the vector pointer at the current location
782d  bda357  LDA CharPtrTbl_high[0],X   ; Read the high-byte of the font command
7830  c8      INY                        ; Increment `Y`
7831  9127    STA (VecCmdQueue),Y        ; Store the high byte at the next location
7833  203878  JSR VecPtrUpdate           ; Add `Y` to the vector ram pointer
7836  28      PLP                        ; Restore the carry flag
7837  60      RTS                        ; Return to the caller

; Increment the vector ram command address
; `Y` number of bytes minus one added to the vector command list
.func VecPtrUpdate:
7838  98      TYA                        ; Move the number of bytes to `A`
7839  38      SEC                        ; Set the carry, which will add the one extra
783a  6527    ADC VecCmdQueue            ; Add `Y+1` to the pointer
783c  8527    STA VecCmdQueue            ; Store it back in the pointer
783e  9002    BCC VecPtr_no_overflow     ; If no overflow skip the increment
7840  e628    INC VecCmdQueue_high       ; Overflowed, so increment the high byte
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


### Vectors


### Ships

```
.word 53ee twenty_subroutines 20 ; Twenty subroutine calls, maybe ships or stars?
Not now: .dvg 53ee 20 1024 1024 1
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
