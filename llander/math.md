## 6502 Math
The 6502 is an 8-bit CPU with 8-bit wide registers and an 8-bit wide data bus.
There is no multiply instruction, so it is necessary to implement it in software.
Some games, like BattleZone have a math coprocessor for doing 3D transforms, but
Lunar Lander does it in software.

Since the registers are 8-bits wide, passing a 16-bit value to a function requires
two of them.  Most of the time they are passed in A and X, but it is not consistent
across all of the code in Lunar Lander.  However a 16-by-16 multiply needs more registers,
so some temporary zero page locations are used.  The results are also left in
zero page locations and can be used for chaning operations together.

### Minimum

As a warmup, here's a function that returns the minimum of two 16-bit values that are stored in global variables
on the zero page:

```asm
.func min16
72fe  a0ff    ldy #$ff                   ; Not sure what Y is used for in the return result
7300  a57e    lda DISTYL_high            ; Assume A is higher, load high byte AH into A
7302  a67d    ldx DISTYL                 ; and low byte AL into X
7304  c580    cmp DISTYR_high            ; Compare the high bytes of AH and BH
7306  9012    bcc return_ax              ; AH is lower, return it
7308  d00c    bne return_b               ; BH is lower, return it instead
730a  a47f    ldy DISTYR                 ; Need to compare the low bytes, load BL into Y
730c  c47d    cpy DISTYL                 ; Compare BL and AL
730e  b00a    bcs return_ax              ; A is lower, return it
7310  a67f    ldx DISTYR                 ; move BL into X
7312  a47d    ldy DISTYL                 ; why is Y loaded here?
7314  9004    bcc return_ax              ; jump to return B (note that AH=BH, so it does not need to be loaded)
.label return_b
7316  a580    lda DISTYR_high            ; B is larger, move the BH into A
7318  a67f    ldx DISTYR                 ; and BL into X
.label return_ax
731a  60      rts                        ; Return the 16-bit value in A:X
```

To translate this into C with the same logic flow is not very idomatic, but hopefully makes it easier to see how it maps
to the 8-bit math of the assembly:

<pre>
uint8_t a_high, a_low;
uint8_t b_high, b_low;
uint16_t min16(void)
{
	uint8_t a = a_high;
	uint8_t x = a_low;

	if (a_high < b_high)
		goto ret;

	if (a_high > b_high)
	{
		a = b_high;
		x = b_low;
		goto ret;
	}

	if (a_low < b_low)
		x = b_low;

ret:
	return a << 8 | x;
}
</pre>

### Multiply

```asm
; Multiply two 8-bit values in `A` and `Y`, returning a 16-bit value in `A:X`.
; Falls through to @mult16_repeat
.func mult16
70ef  8543    sta MULTC                  ; Store `A` for repeated calls to @mult16_repeat (which this now implicitly calls by falling through)

; Multiply the 8-bit values in Y with the previously used value in A
.func mult16_repeat
70f1  8442    sty MULTR                  ; Store Y into mult_y
70f3  a543    lda MULTC                  ; Load mult_a...
70f5  48      pha                        ; and store it on the stack
70f6  49ff    eor #$ff                   ; Invert the high byte (to make a test easier later)...
70f8  8543    sta MULTC                  ; and store it back in mult_a
70fa  a900    lda #$00                   ; A = 0
70fc  8544    sta PROD                   ; Zero the multiply output low...
70fe  8545    sta PROD_high              ; and high bytes
7100  a208    ldx #$08                   ; Number of rounds (8 since this is an 8x8 to 16-bit multiply)
.label mult_start_round
7102  0643    asl MULTC                  ; Shift the inverted high byte to the left
7104  b006    bcs mult_bit_not_set       ; If the top bit was set, skip the increment
7106  6542    adc MULTR                  ; Add mult_y to A
7108  9002    bcc mult_bit_not_set       ; If this doesn't carry, skip updating the high byte
710a  e645    inc PROD_high              ; The addition overflowed, increment the high byte
.label mult_bit_not_set
710c  ca      dex                        ; Decrement our round counter
710d  d007    bne mult_continue_round    ; If it is not zero, do another round
710f  aa      tax                        ; Move the multiply accumulator low-byte to X
7110  68      pla                        ; Restore the non-inverted mult_a from the stack,
7111  8543    sta MULTC                  ; and store it back in the memory location
7113  a545    lda PROD_high              ; Load the high byte of the multiply accumulator into A
7115  60      rts                        ; return the 16-bit value as the register pair X:A
.label mult_continue_round
7116  0a      asl                        ; Multiply the low-byte of the result by 2
7117  2645    rol PROD_high              ; Multiply the high-byte by two, shifting in the carry
7119  90e7    bcc mult_start_round       ; If this doesn't overflow, start another round
```


I'm not certain about some of these operations; it seems that the mult_acc field is never used after being zeroed
and I wonder if it is left over from a prior implementation.  This code also causes a problem with the tracing disassembler
since it appears that there is subroutine call to @0x711c, which is in the middle of an instruction.  If the multiply
does overflow, a `BRK` instruction is triggered that should halt the game.

In any event, this algorithm could be translate roughly to the C code:

```C
uint16_t mult16(uint8_t a, uint8_t y)
{
	uint8_t mult_acc = 0, mult_acc_high = 0;
	uint8_t inv_a = ~a;

	for(int8_t x = 8 ; x != 0 ; x--)
	{
		if (inv_a & 0x80)
		{
			mult_acc += y;
			if (mult_acc + y > 0xFF)
				mult_acc_high += 1;
		}

		mult_acc_high <<= 1;
		if (mult_acc & 0x80)
			mult_acc_high |= 1;
		mult_acc <<= 1;
	}

	return mult_acc_high << 8 | mult_acc;
}
```


### 16-bit signed magnitude math

The core game update routine uses the 16-bit signed magnitude XY accelerations to compute
the ship's velocity in the XY coordinate frame, which are then used to update the XY positions.
Adding the values as part of the timestep update is implemented in this set of functions:

```
; Update delta1 with signed byte `Y` and 16-bit magnitude in `A:X`.
; Falls through...
.func add16_signed_mag:
6cfe  844d    sty SDESSGN                ;

; Update delta1 with 16-bit magnitude in `A:X`; does not modify the sign
; Falls through...
.func add16_signed_mag_arg1:
6d00  854b    sta SUMDES_high            ;

; Update only the low-byte of of delta1 from `X`; does not modify the sign or high byte
; Falls through...
.func add16_signed_mag_arg1_low:
6d02  864a    stx SUMDES                 ;

; Compute the 16-bit signed addition of delta1 and delta2
; Returns the result in delta1 and delta1_sign, as well as `X` and `A:Y`
; Why is the return different from the calling convention?
.func add16_signed_mag_core:
6d04  a54c    lda SSORSGN                ; Compare the sign bits for delta1 and delta2
6d06  454d    eor SDESSGN                ; which are stored in the 7th bit of the byte
6d08  1034    bpl same_sign              ; Same sign?
6d0a  38      sec                        ; Not the same sign, so this will be a delta1 - delta2
6d0b  a54a    lda SUMDES                 ; Subtract the low bytes of delta1
6d0d  e548    sbc SUMSOR                 ; and delta2.
6d0f  a8      tay                        ; Store this in `Y`
6d10  a54b    lda SUMDES_high            ; Subtract the high bytes of delta1
6d12  e549    sbc SUMSOR_high            ; and delta2, using the carry from @6d0d
6d14  9016    bcc opposite_underflow     ; If carry was cleared, an underflow occured
6d16  d00d    bne return_delta1_sign     ; Were some bits set in the high byte? Is so return them.
6d18  c000    cpy #$00                   ; Were some bits set in the low byte in `Y`?
6d1a  d009    bne return_delta1_sign     ; If so, return them
6d1c  854a    sta SUMDES                 ; Return result was exactly zero, so store zero in the low byte
6d1e  854b    sta SUMDES_high            ; and zero the high byte
6d20  854d    sta SDESSGN                ; and reset the sign (no negative zero)
6d22  aa      tax                        ; Return low = 0
6d23  a8      tay                        ; Return high = 0
6d24  60      rts                        ; And return the triple
.label return_delta1_sign:
6d25  a64d    ldx SDESSGN                ; Return result has same sign as delta1
.label return_delta1:
6d27  844a    sty SUMDES                 ; Store low byte into `Y`
6d29  854b    sta SUMDES_high            ; Store high byte into `A`
6d2b  60      rts                        ; And return the triple
.label opposite_underflow:
6d2c  49ff    eor #$ff                   ; The result of the subtraction underflowed, so invert the high byte in `A`
6d2e  aa      tax                        ; and move it to `X`
6d2f  98      tya                        ; Move the low byte of the subtraction from `Y` into `A`
6d30  49ff    eor #$ff                   ; Invert the low byte as well
6d32  a8      tay                        ; and move it back into `Y`
6d33  c8      iny                        ; Increment `Y`, to undo the two's complement negative
6d34  d001    bne opposite_2c_carry      ; If this also underflowed,
6d36  e8      inx                        ; then also increment `X` to under the high-byte's two's complement negative
.label opposite_2c_carry:
6d37  8a      txa                        ; Move the high byte of the subtraction into `A`
6d38  a64c    ldx SSORSGN                ; The underflowed result has the same sign as delta2 had
6d3a  864d    stx SDESSGN                ; Store the new sign byte into delta1 for the return
6d3c  90e9    bcc return_delta1          ; I think this is a branch always?
.label same_sign:
6d3e  18      clc                        ; Clear the carry
6d3f  a54a    lda SUMDES                 ; Add the low bytes of delta1
6d41  6548    adc SUMSOR                 ; and delta2
6d43  a8      tay                        ; Store the result in `Y`
6d44  a54b    lda SUMDES_high            ; Add the high bytes of delta1
6d46  6549    adc SUMSOR_high            ; and delta2, using the carry from the low-byte addition
6d48  90db    bcc return_delta1_sign     ; If no overflow occured, return the result in delta1
6d4a  a9ff    lda #$ff                   ; Overflow, so clamp at `0xFFFF`
6d4c  a8      tay                        ; in `A:Y`
6d4d  b0d6    bcs return_delta1_sign     ; And return it with the same sign as delta1
```


### BCD

The 6502 has a "Binary Coded Decimal" mode that only allows the values `0` - `9` for each four bits in a byte.
This means that one byte can represent `00` to `99`, and is frequently used by games to track scores or resources
that are displayed to the player in base-10.  On a modern system programmers would just use `printf()` or something
to convert from binary to base-10, but that requires mutliply and divide operations that the 6502 did not have.

Most of the fuel and score calculations in Lunar Lander are done in BCD, but there are other parts that are all
done in binary, so occasionally it is necessary to convert between them.  For these few times there is an interesting
algorithm called [Double Dabble](https://en.wikipedia.org/wiki/Double_dabble) that relatively efficiently
produces a result with no multiplies or divides.  If space is available, a lookup table is also an option.


```
; Convert a 16-bit binary value into BCD, outputing to bcd_output or `Y:X:A`.
; `Y:X` input 16-bit value
.func dec_to_bcd_16bit:
79c2  8437    sty TEMP1                  ; Store MSB of argument in gb37
79c4  a00f    ldy #$0f                   ; Pass 16 as the number of bits to convert

; Convert an arbitrary bit width binary value into BCD using the Double Dabble algorithm.
; `Y`: Number of bits to convert
; `X`: LSB of 16-bit input value
; `GenByte_0038`: MSB of the 16-bit input value
;
; Returns the data in bcd_output or in `Y:X:A`
.func dec_to_bcd:
79c6  8638    stx TEMP2                  ; Store LSB of argument in gb38
79c8  a900    lda #$00                   ; Zero the bcd output
79ca  8592    sta NUMB1[0]               ; lsb
79cc  8593    sta NUMB1[1]               ; mid
79ce  8594    sta NUMB1[2]               ; msb
79d0  f8      sed                        ; turn on BCD mode
.label dd_loop:
79d1  0637    asl TEMP1                  ; D
79d3  2638    rol TEMP2                  ; -O
79d5  a592    lda NUMB1[0]               ; --U
79d7  6592    adc NUMB1[0]               ; ---B
79d9  8592    sta NUMB1[0]               ; ----L
79db  a593    lda NUMB1[1]               ; -----E
79dd  6593    adc NUMB1[1]               ; ------D
79df  8593    sta NUMB1[1]               ; -------A
79e1  a594    lda NUMB1[2]               ; --------B
79e3  6594    adc NUMB1[2]               ; ---------B
79e5  8594    sta NUMB1[2]               ; ----------L
79e7  88      dey                        ; -----------E
79e8  10e7    bpl dd_loop                ; if bits-- > 0 do it again
79ea  a494    ldy NUMB1[2]               ; load the bcd output
79ec  a693    ldx NUMB1[1]               ; into the registers
79ee  a592    lda NUMB1[0]               ; for some callers who want that
79f0  d8      cld                        ; back into binary mode
79f1  60      rts                        ; return to caller
```

