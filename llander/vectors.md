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

```
.word 4000 VGRAM ; Digital Vector Generator RAM mapped into the 6502
```

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
7e59  a940    lda #$40                   ; VecCmdQueue = (u16*) 0x4000
7e5b  8528    sta RAMPTR_high            ; .
7e5d  a900    lda #$00                   ; .
7e5f  8527    sta RAMPTR                 ; .
7e61  60      rts                        ; Our work is done


; Start the vector generator!
; Everything that has been copied to @VecCmdQueue should be executed by the DVG and drawn
; to the screen.
;
; `A`: value to write to the `DMAGO` command as well as the watchdog value to write
.func vecgen_go:
7e7a  8d0030  sta IO_DMAGO               ; Write to the `DMAGO` memory mapped pin that enables the vector generator
7e7d  a003    ldy #$03                   ; Fall through to busy wait for 3 * 5 ms = 15 ms

; Busy wait on the external 3 KHz clock connected to bit 6 on @IO_in0
; This will wait 15 of the 3 KHz cycles per `Y`, or about 5 ms each
; It will write to the watchdog after each 5 ms clock cycle to avoid resets while busy waiting,
; but if the 3 KHz clock fails then the watchdog will *not* be petted and the system should
; reset.
;
; `A`: Watchdog value
; `Y`: Number of 5 ms cycles to spin
.func busywait_5ms:
7e7f  8d0034  sta IO_watchdog            ; Pet the watchdog
7e82  a214    ldx #$14                   ; for x = 14 ... 0:
.label spin_3khz_hi:
7e84  2c0020  bit IO_in0                 ; Wait for clock to go low by read from `in0`
7e87  70fb    bvs spin_3khz_hi           ; If bit 6 is set, keep spinning
.label spin_3khz_lo:
7e89  2c0020  bit IO_in0                 ; Wait for clock to go high by re-read from `in0`
7e8c  50fb    bvc spin_3khz_lo           ; If bit 6 is unset, keep spinning
7e8e  ca      dex                        ; if X-- != 0
7e8f  d0f3    bne spin_3khz_hi           ; do another 3 KHz clock cycle (15 per iteration)
7e91  88      dey                        ; if Y-- != 0
7e92  d0eb    bne busywait_5ms           ; pet the watchdog and keep waiting
7e94  60      rts                        ; We've waited `Y` * 14 of the 3 KHz clock cycles, we're done
```


Since much of the game's assets live in 6502 ROM space, not the DVG ROM, there is a memcpy routine
to copy commands to the queue.

```
; Copy `X` bytes from 6502 memory `A:Y` to the DVG's command queue
; Updates @VecPtr with the ending address of the copy
; Updates @VecCmdQueue to point to the end of the command queue
.func VecCmd_memcpy:
7ea6  8565    sta RAMLD_high             ; VecPtr = `A:Y` to start with
7ea8  8464    sty RAMLD                  ; fall through into @VecCmd_memcpy_vecptr

; Copy commands from the 6502's memory to the DVG's command queue
; `X`: Length to copy (in bytes)
; Global @VecPtr Pointer to 6502 memory, will be modified to point to the end of the data copied
; Global @VecCmdQueue Tail of the DVG command queue, will be updated to point to the new end of the queue
.func VecCmd_memcpy_vecptr:
7eaa  8a      txa                        ;
7eab  a8      tay                        ;
7eac  88      dey                        ; for y = len-1 .. 0:
.label vecram_memcpy_loop:
7ead  b164    lda (RAMLD),Y              ; VecCmdQueue[Y] = VecPtr[Y]
7eaf  9127    sta (RAMPTR),Y             ; .
7eb1  88      dey                        ; Y--
7eb2  10f9    bpl vecram_memcpy_loop     ; if Y >= 0, then keep copying
7eb4  8a      txa                        ; restore original len
7eb5  18      clc                        ; prepare for addition
7eb6  6527    adc RAMPTR                 ; (u16) VecCmdQueue += (u8) len
7eb8  8527    sta RAMPTR                 ; .
7eba  9002    bcc vecram_skip_inc        ; .
7ebc  e628    inc RAMPTR_high            ; .
.label vecram_skip_inc:
7ebe  8a      txa                        ; restore original len
7ebf  18      clc                        ; prepare for addition
7ec0  6564    adc RAMLD                  ; (u16) VecPtr += (u8) len
7ec2  8564    sta RAMLD                  ; .
7ec4  9002    bcc vecram_skip_inc2       ; .
7ec6  e665    inc RAMLD_high             ; .
.label vecram_skip_inc2:
7ec8  60      rts                        ; Return to the caller
```

There are lots of helpers to copy short or long vector commands, as well as to set the @VecPtr pointer.

```
; Copy 8 bytes from `A:Y` to the DVG
.func VecCmd_copy_8:
7ea4  a208    ldx #$08                   ; fall through to @VecCmd_memcpy

; Copy 2 bytes from `A:Y` to the DVG
.func VecCmd_copy_2:
7ec9  a202    ldx #$02                   ; X = 2
7ecb  d0d9    bne VecCmd_memcpy          ; always tail call to @VecCmd_memcpy

; Copy 4 bytes from `A:Y` to the DVG
.func VecCmd_copy_4:
7ecd  a204    ldx #$04                   ; X = 4
7ecf  d0d5    bne VecCmd_memcpy          ; always tail call to @VecCmd_memcpy

; Copy 4 bytes from @VecPtr to the DVG
.func VecCmd_copy_4_vecptr:
7ed1  a204    ldx #$04                   ; X = 4
7ed3  d0d5    bne VecCmd_memcpy_vecptr   ; always tail call to vecram_memcpy_vecptr
```




### Fonts and number drawing

```
; Draw a BCD number without a leading zero
; `A` address of number on zero page
; `Y` number of digits
.func DrawNumber_no_leading_zero:
7b59  38      sec                        ; Set carry flag and fall through into @DrawNumber

; Draw a BCD number from the zero page
; `A` address of number on zero page
; `Y` number of digits
; `C` include leading zeros (carry flag clear)
.func DrawNumber:
7b5a  08      php                        ; Push the status register onto the stack (save the carry flag)
7b5b  88      dey                        ; decrement the number of digits (to compute last address)
7b5c  8438    sty TEMP2                  ; store number of digits in genbyte
7b5e  18      clc                        ; Clear the carry
7b5f  6538    adc TEMP2                  ; Add `A` to `Y-1`, which is the address of the MSB of the BCD digit
7b61  28      plp                        ; Restore the carry flag from the stack
7b62  aa      tax                        ; Move the starting address for the MSB digit into `X`
.label DrawNumStringLoop:
7b63  08      php                        ; Push the carry flag again
7b64  8637    stx TEMP1                  ; Store the address into genbyte
7b66  b500    lda SOFT_0,X               ; Treat the zero page as an array and read the BCD digit
7b68  4a      lsr                        ; Shift
7b69  4a      lsr                        ; it
7b6a  4a      lsr                        ; right
7b6b  4a      lsr                        ; four times to get the upper digit from the top nibble into `A`
7b6c  28      plp                        ; Restore the carry flag
7b6d  201878  jsr DrawDigit              ; Draw the upper digit
7b70  a538    lda TEMP2                  ; Do we do more digits?
7b72  d001    bne DoLowerDigit           ; if so do the lower digit for this value
7b74  18      clc                        ; Clear the carry (we will always do zeros now)
.label DoLowerDigit:
7b75  a637    ldx TEMP1                  ; Get the current digit address
7b77  b500    lda SOFT_0,X               ; Zero-page array read for the digit
7b79  201878  jsr DrawDigit              ; Draw the lower digit
7b7c  a637    ldx TEMP1                  ; Decrement the digit address
7b7e  ca      dex                        ; to move to the next digit
7b7f  c638    dec TEMP2                  ; Decrement our digit counter
7b81  10e0    bpl DrawNumStringLoop      ; If still positive, draw more digits
7b83  60      rts                        ; And we're done!
```

```
; Draw a single digit
; This will skip leading zeros when outputing numbers.
; `A` bottom four bits are the BCD digit to draw
; `C` include leading zeros if clear
.func DrawDigit:
7818  9004    bcc ChkSetDigitPntr        ; If carry is clear, always display the digit
781a  290f    and #$0f                   ; If not, check to see if the bottom nibble is zero
781c  f005    beq DisplayDigit           ; If digit is zero, then draw character 0 which is a blank
.label ChkSetDigitPntr:
781e  290f    and #$0f                   ; Mask out the top nibble
7820  18      clc                        ; Clear carry
7821  6901    adc #$01                   ; Add one to the digit, which shifts it to the correct font location
.label DisplayDigit:
7823  08      php                        ; Push the CPU state (preserve the carry flag?)
7824  0a      asl                        ; Multiple the digit by 2, since the DVG uses 16-bit words
7825  a000    ldy #$00                   ; `Y` is the offset for the vector ram pointer
7827  aa      tax                        ; `X = A`
7828  bda257  lda CharPtrTbl[0],X        ; Read the low-byte of the font command
782b  9127    sta (RAMPTR),Y             ; Store it in the vector pointer at the current location
782d  bda357  lda CharPtrTbl_high[0],X   ; Read the high-byte of the font command
7830  c8      iny                        ; Increment `Y`
7831  9127    sta (RAMPTR),Y             ; Store the high byte at the next location
7833  203878  jsr VecCmdQueueUpdate      ; Add `Y` to the vector ram pointer
7836  28      plp                        ; Restore the carry flag
7837  60      rts                        ; Return to the caller

; Increment the vector ram command address
; `Y` number of bytes minus one added to the vector command list
.func VecCmdQueueUpdate:
7838  98      tya                        ; Move the number of bytes to `A`
7839  38      sec                        ; Set the carry, which will add the one extra
783a  6527    adc RAMPTR                 ; (u16) VecCmdQueue += `Y` + 1
783c  8527    sta RAMPTR                 ; .
783e  9002    bcc VecCmdQueue_no_overflow ; .
7840  e628    inc RAMPTR_high            ; .
.label VecCmdQueue_no_overflow:
7842  60      rts                        ; Return to the caller
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
.dvg_parse 53ee twenty_subroutines 20 ; Twenty subroutine calls, maybe ships or stars?
Not now: .dvg 53ee 20 1024 1024 1

.dvg_parse 4ba2 ships_jsrl 6 ; Vector JSRL for the different ships
.dvg 4ba2 6 640 384 3 512 64
```

### Landscape

There are "Major" and "Minor" landscapes


```
.word 51ba lunar_minor_scape_jsrl 20 ; JSRL for the minor lunar landscape
.dvg 51ba 20 1024 1024 1 0 256
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
