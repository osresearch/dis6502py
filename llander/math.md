## 16-bit Math
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
72fe  a0ff    LDY #$ff                   ; Not sure what Y is used for in the return result
7300  a57e    LDA min16_a_high           ; Assume A is higher, load high byte AH into A
7302  a67d    LDX min16_a                ; and low byte AL into X
7304  c580    CMP min16_b_high           ; Compare the high bytes of AH and BH
7306  9012    BCC return_ax              ; AH is lower, return it
7308  d00c    BNE return_b               ; BH is lower, return it instead
730a  a47f    LDY min16_b                ; Need to compare the low bytes, load BL into Y
730c  c47d    CPY min16_a                ; Compare BL and AL
730e  b00a    BCS return_ax              ; A is lower, return it
7310  a67f    LDX min16_b                ; move BL into X
7312  a47d    LDY min16_a                ; why is Y loaded here?
7314  9004    BCC return_ax              ; jump to return B (note that AH=BH, so it does not need to be loaded)
.label return_b
7316  a580    LDA min16_b_high           ; B is larger, move the BH into A
7318  a67f    LDX min16_b                ; and BL into X
.label return_ax
731a  60      RTS                        ; Return the 16-bit value in A:X
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
70ef  8543    STA mult_a                 ; Store `A` into @mult_a for repeated calls to @mult16_repeat (which this now implicitly calls by falling through)

; Multiply the 8-bit values in Y with the previously used value in A
.func mult16_repeat
70f1  8442    STY mult_y                 ; Store Y into mult_y
70f3  a543    LDA mult_a                 ; Load mult_a...
70f5  48      PHA                        ; and store it on the stack
70f6  49ff    EOR #$ff                   ; Invert the high byte (to make a test easier later)...
70f8  8543    STA mult_a                 ; and store it back in mult_a
70fa  a900    LDA #$00                   ; A = 0
70fc  8544    STA mult_acc               ; Zero the multiply output low...
70fe  8545    STA mult_acc_high          ; and high bytes
7100  a208    LDX #$08                   ; Number of rounds (8 since this is an 8x8 to 16-bit multiply)
.label mult_start_round
7102  0643    ASL mult_a                 ; Shift the inverted high byte to the left
7104  b006    BCS mult_bit_not_set       ; If the top bit was set, skip the increment
7106  6542    ADC mult_y                 ; Add mult_y to A
7108  9002    BCC mult_bit_not_set       ; If this doesn't carry, skip updating the high byte
710a  e645    INC mult_acc_high          ; The addition overflowed, increment the high byte
.label mult_bit_not_set
710c  ca      DEX                        ; Decrement our round counter
710d  d007    BNE mult_continue_round    ; If it is not zero, do another round
710f  aa      TAX                        ; Move the multiply accumulator low-byte to X
7110  68      PLA                        ; Restore the non-inverted mult_a from the stack,
7111  8543    STA mult_a                 ; and store it back in the memory location
7113  a545    LDA mult_acc_high          ; Load the high byte of the multiply accumulator into A
7115  60      RTS                        ; return the 16-bit value as the register pair X:A
.label mult_continue_round
7116  0a      ASL                        ; Multiply the low-byte of the result by 2
7117  2645    ROL mult_acc_high          ; Multiply the high-byte by two, shifting in the carry
7119  90e7    BCC mult_start_round       ; If this doesn't overflow, start another round
```


I'm not certain about some of these operations; it seems that the @mult_acc field is never used after being zeroed
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


### Trig

The @mult16 function is used to compute the ship's X and Y acceleration based on the current thrust,
a thrust-to-force lookup table, and then multiplying by the sine and cosine of the ship's angle to
rotate the force into the screen coordinate frame.

```
; Update the ship's acceleration in the screen reference frame
; Compute sin and cos of the ship's angle and multiplies the
; current thrust setting to get the X and Y acceleration.
; Also computes the sign bit for these accelerations
.func ship_compute_accel_xy:
6b32  a502    LDA ship_angle_modulo      ; Read the reduced ship's angle (updated by @ship_command_yaw_easy )
6b34  4a      LSR                        ; This is 0-31, where 0 is horizontal facing right, 8 is vertical,
6b35  4a      LSR                        ; 16 is horizontal facing left, 31 is straight down
6b36  4a      LSR                        ; Divide this reduced angle by 8 to get the quadrant that it is in
6b37  aa      TAX                        ;
6b38  bdf276  LDA sine_quadrants,X       ; Read the quadrant bits (bit 7 = X direction, bit 6 = Y direction)
6b3b  8546    STA ship_accel_sign        ; Store the X accleration sign bit (used by @add16_signed_mag)
6b3d  0a      ASL                        ; Shift it left once
6b3e  8547    STA ship_accel_sign[1]     ; Store the Y acceleration sign bit
6b40  a601    LDX actual_thrust_maybe    ;
6b42  bdf676  LDA thrust_to_acc,X        ;
6b45  850b    STA thrust_mode_maybe      ;
6b47  a502    LDA ship_angle_modulo      ; Get the ship's angle (0-31)
6b49  290f    AND #$0f                   ; Get how far from horizontal it is (up or down)
6b4b  c909    CMP #$09                   ; If it is 0-8, use the first half of the sine table
6b4d  9004    BCC flip_to_other_half     ; (
6b4f  490f    EOR #$0f                   ; Invert the clamped angle, which flips it around 45 degrees
6b51  6900    ADC #$00                   ; Why carry?
.label flip_to_other_half:
6b53  8537    STA GenByte_0037           ;
6b55  4907    EOR #$07                   ;
6b57  6901    ADC #$01                   ;
6b59  290f    AND #$0f                   ;
6b5b  aa      TAX                        ;
6b5c  bde976  LDA sine_table,X           ;
6b5f  a40b    LDY thrust_mode_maybe      ;
6b61  20ef70  JSR mult16                 ;
6b64  8558    STA ship_accel             ;
6b66  a637    LDX GenByte_0037           ;
6b68  bde976  LDA sine_table,X           ;
6b6b  20ef70  JSR mult16                 ;
6b6e  8559    STA ship_accel[1]          ;
6b70  60      RTS                        ;
```

```
.byte 76f2 sine_quadrants 4 ; Define the quadrants
.byte 76f6 thrust_to_acc 16 ; How much acceleration comes from the different thrust levels
.byte 76e9 sine_table 9 ; Reduced sine table for 0-45 degrees
```

### 16-bit signed magnitude math

The core game update routine uses the 16-bit signed magnitude XY accelerations to compute
the ship's velocity in the XY coordinate frame, which are then used to update the XY positions.
Adding the values as part of the timestep update is implemented in this set of functions:

```
; Update @delta1 with signed byte `Y` and 16-bit magnitude in `A:X`.
; Falls through...
.func add16_signed_mag:
6cfe  844d    STY delta1_sign            ;

; Update @delta1 with 16-bit magnitude in `A:X`; does not modify the sign
; Falls through...
.func add16_signed_mag_arg1:
6d00  854b    STA delta1_high            ;

; Update only the low-byte of of @delta1 from `X`; does not modify the sign or high byte
; Falls through...
.func add16_signed_mag_arg1_low:
6d02  864a    STX delta1                 ;

; Compute the 16-bit signed addition of @delta1 and @delta2
; Returns the result in @delta1 and @delta1_sign, as well as `X` and `A:Y`
; Why is the return different from the calling convention?
.func add16_signed_mag_core:
6d04  a54c    LDA delta2_sign            ; Compare the sign bits for @delta1 and @delta2
6d06  454d    EOR delta1_sign            ; which are stored in the 7th bit of the byte
6d08  1034    BPL same_sign              ; Same sign?
6d0a  38      SEC                        ; Not the same sign, so this will be a @delta1 - @delta2
6d0b  a54a    LDA delta1                 ; Subtract the low bytes of @delta1
6d0d  e548    SBC delta2                 ; and @delta2.
6d0f  a8      TAY                        ; Store this in `Y`
6d10  a54b    LDA delta1_high            ; Subtract the high bytes of @delta1
6d12  e549    SBC delta2_high            ; and @delta2, using the carry from @6d0d
6d14  9016    BCC opposite_underflow     ; If carry was cleared, an underflow occured
6d16  d00d    BNE return_delta1_sign     ; Were some bits set in the high byte? Is so return them.
6d18  c000    CPY #$00                   ; Were some bits set in the low byte in `Y`?
6d1a  d009    BNE return_delta1_sign     ; If so, return them
6d1c  854a    STA delta1                 ; Return result was exactly zero, so store zero in the low byte
6d1e  854b    STA delta1_high            ; and zero the high byte
6d20  854d    STA delta1_sign            ; and reset the sign (no negative zero)
6d22  aa      TAX                        ; Return low = 0
6d23  a8      TAY                        ; Return high = 0
6d24  60      RTS                        ; And return the triple
.label return_delta1_sign:
6d25  a64d    LDX delta1_sign            ; Return result has same sign as @delta1
.label return_delta1:
6d27  844a    STY delta1                 ; Store low byte into `Y`
6d29  854b    STA delta1_high            ; Store high byte into `A`
6d2b  60      RTS                        ; And return the triple
.label opposite_underflow:
6d2c  49ff    EOR #$ff                   ; The result of the subtraction underflowed, so invert the high byte in `A`
6d2e  aa      TAX                        ; and move it to `X`
6d2f  98      TYA                        ; Move the low byte of the subtraction from `Y` into `A`
6d30  49ff    EOR #$ff                   ; Invert the low byte as well
6d32  a8      TAY                        ; and move it back into `Y`
6d33  c8      INY                        ; Increment `Y`, to undo the two's complement negative
6d34  d001    BNE opposite_2c_carry      ; If this also underflowed,
6d36  e8      INX                        ; then also increment `X` to under the high-byte's two's complement negative
.label opposite_2c_carry:
6d37  8a      TXA                        ; Move the high byte of the subtraction into `A`
6d38  a64c    LDX delta2_sign            ; The underflowed result has the same sign as @delta2 had
6d3a  864d    STX delta1_sign            ; Store the new sign byte into @delta1 for the return
6d3c  90e9    BCC return_delta1          ; I think this is a branch always?
.label same_sign:
6d3e  18      CLC                        ; Clear the carry
6d3f  a54a    LDA delta1                 ; Add the low bytes of @delta1
6d41  6548    ADC delta2                 ; and @delta2
6d43  a8      TAY                        ; Store the result in `Y`
6d44  a54b    LDA delta1_high            ; Add the high bytes of @delta1
6d46  6549    ADC delta2_high            ; and @delta2, using the carry from the low-byte addition
6d48  90db    BCC return_delta1_sign     ; If no overflow occured, return the result in @delta1
6d4a  a9ff    LDA #$ff                   ; Overflow, so clamp at `0xFFFF`
6d4c  a8      TAY                        ; in `A:Y`
6d4d  b0d6    BCS return_delta1_sign     ; And return it with the same sign as @delta1

.byte 4d delta1_sign ; Sign byte for the 16-bit @delta1
.word 4a delta1 ; 16-bit magnitude for @add16_signed_mag
.byte 4c delta2_sign ; Sign byte for the 16-bit @delta2
.word 48 delta2 ; 16-bit magnitude for @add16_signed_mag
```


### Ship state

Most of the ship's state is stored in zeropage global variables.  These include the
XY acceleration (stored as 17-bit signed magnitude), the velocity and position
(stored as 9-bit signed magnitude?)

```
.byte 46 ship_accel_sign 2 ; The sign bits for the X and Y accelerations
.byte 55 ship_enable_x ; Disable physics for the X and Y axes (bit 7)
.byte 56 ship_abort ; Has the abort button been triggered?
.byte 57 ship_enable_y ; Accessed via array from @ship_enable_x
.byte 58 ship_accel 2 ; The X and Y acceleration magnitudes for the ship's thrust
.byte 5a ship_vel_sign_x ; Sign bit for the X velocity

; 0x8F == exploding?
; 0x00 == +50 points
; 0x4x == +15 points
; 0x0x == + 5 points (bottom bits ignored?)
; initialized to 0 by @ResetGameState
.byte 5d ship_state_maybe ; Bit map of stuff about the ship

.word 5e ship_vel 2 ; Ship horizontal X and Y
.word 07 ship_pos 2 ; Ship position 16-bit
```

### Ship Update

Now that we have the math functions for computing signed magnitude addition and transforming
the thrust vectors into the XY screen coordinate frame, we can finally update the ship's position.

```
; Update ship acceleration, velocity and position in the XY frame once per clock tick
;
; The 16-bit velocity is normally divided by 256, but if the screen is zoomed in
; then it is only divided by 64.  Since the NMI runs at 250 HZ, this division
; effectively is the same as multiplying the velocity by dt.
;
; This updates the ship position on each axis
;
;    x = x + vx * dt
;    vx = vx + thrust_x * dt
;    y = y + vy * dt
;    vy = vy + (thrust_y - gravity) * dt
;
; @add16_signed_mag_arg1 is used for position update since the position sign is always positive
; @add16_signed_mag_core is used to accumulate the thrust_y - gravity plus velocity
;
.func ship_update:
6c68  a202    LDX #$02                   ; Make two loops, one for X and one for Y.  Note that `i` is decremented by 2 each time through the loop @6ce7
.label ship_update_loop:
6c6a  8637    STX GenByte_0037           ; Store the iterator temporary
6c6c  a900    LDA #$00                   ; Initialize the global helper variables
6c6e  855d    STA ship_state_maybe       ;
6c70  854d    STA delta1_sign            ; Position sign is always positive
6c72  8549    STA delta2_high            ; velocity_high = 0
6c74  b555    LDA ship_enable_x,X        ; is bit 7 set in @ship_enable_x or @ship_enable_y (depending on X)
6c76  3028    BMI skip_physics           ; if so skip the physics for this axis
6c78  b55f    LDA ship_vel_high,X        ; Copy the high byte of the velocity for this axis
6c7a  8548    STA delta2                 ; into the low-byte of @delta2
6c7c  b55e    LDA ship_vel,X             ; Load the low byte of the ship's velocity
6c7e  244e    BIT drawing_scale          ; Check if we have zoomed in on the ship and terrain
6c80  700a    BVS skip_zoom              ; Skip the zoom if we haven't zoomed in (bit 6 is not set)
6c82  0a      ASL                        ; Double the low byte of the velocity
6c83  2648    ROL delta2                 ; Double the high byte of the velocity (shifting in from the low byte)
6c85  2649    ROL delta2_high            ; Double the high high byte of the velocity
6c87  0a      ASL                        ; And do it again...
6c88  2648    ROL delta2                 ; This multiplies the velocity by four
6c8a  2649    ROL delta2_high            ; Note that the bottom byte is otherwise unused
.label skip_zoom:
6c8c  b55a    LDA ship_vel_sign_x,X      ; Get the sign bit for the velocity for this axis
6c8e  854c    STA delta2_sign            ; and store it in the @delta2 workspace
6c90  b508    LDA ship_pos_high,X        ; Get the position high byte for this axis
6c92  48      PHA                        ; Push it
6c93  b507    LDA ship_pos,X             ; Get the position low byte
6c95  aa      TAX                        ; move it into `X`
6c96  68      PLA                        ; Pop the high byte so that the 16-bit position is in `A:X`
6c97  20006d  JSR add16_signed_mag_arg1  ; Compute Position + Velocity for this axis
6c9a  a637    LDX GenByte_0037           ; Restore the iterator
6c9c  9508    STA ship_pos_high,X        ; Write the high byte for this axis
6c9e  9407    STY ship_pos,X             ; and write the low byte for this axis
.label skip_physics:
6ca0  a900    LDA #$00                   ; Gravity always has a zero high-byte
6ca2  8549    STA delta2_high            ;
6ca4  8a      TXA                        ; Move the iterator to the accumulator for testing
6ca5  f002    BEQ no_gravity             ; If i == 0, don't add any gravity (x axis)
6ca7  a563    LDA gravity                ; @gravity global is updated based on the mission difficulty
.label no_gravity:
6ca9  8548    STA delta2                 ; Store either 0 or the gravity into the low-byte of @delta2
6cab  a980    LDA #$80                   ; Since gravity is always negative
6cad  854c    STA delta2_sign            ; set the sign bit for @delta2 to negative
6caf  b45a    LDY ship_vel_sign_x,X      ; Get the sign bit of this axis' velocity into `Y`
6cb1  b55f    LDA ship_vel_high,X        ; And load `A:X` with this axis' 16-bit velocity magnitutde
6cb3  48      PHA                        ; (same logic as before
6cb4  b55e    LDA ship_vel,X             ; to push things onto the stack
6cb6  aa      TAX                        ; and the pop them off again
6cb7  68      PLA                        ; into the right registers)
6cb8  20fe6c  JSR add16_signed_mag       ; Compute Velocity + Gravity for this axis
6cbb  a537    LDA GenByte_0037           ; Restore the iterator
6cbd  4a      LSR                        ; Divide it by two
6cbe  aa      TAX                        ; and move it back to X
6cbf  b558    LDA ship_accel,X           ; Get the 8-bit magnitude of the ship's thrust on this axis
6cc1  8548    STA delta2                 ; and copy it into @delta2
6cc3  b546    LDA ship_accel_sign,X      ; Get the thrust sign bit
6cc5  854c    STA delta2_sign            ; and copy it into @delta2
6cc7  a523    LDA mission_difficulty     ; Depending on the mission difficulty
6cc9  c902    CMP #$02                   ; 2 == "Prime", which has strong gravity
6ccb  d00c    BNE add_thrust_to_vel      ; other missions don't need to tweak the thrust
6ccd  a548    LDA delta2                 ; Multiply the @delta2 value by 1.5
6ccf  4a      LSR                        ; through clever shift and addition
6cd0  18      CLC                        ; tricks with the carry flags
6cd1  6548    ADC delta2                 ; delta2 = delta2 + (delta2 / 2)
6cd3  8548    STA delta2                 ; effectively
6cd5  9002    BCC add_thrust_to_vel      ; no overflow
6cd7  e649    INC delta2_high            ; add the overflow to the high byte
.label add_thrust_to_vel:
6cd9  20046d  JSR add16_signed_mag_core  ; @delta1 already has Velocity + Gravity, so this is Velocity + Gravity + Thrust
6cdc  48      PHA                        ; Result is in `A:Y`, push the high byte
6cdd  8a      TXA                        ; Result sign bit is in `X`
6cde  a637    LDX GenByte_0037           ; Restore the iterator
6ce0  955a    STA ship_vel_sign_x,X      ; Update the velocity sign bit
6ce2  945e    STY ship_vel,X             ; Update the velocity low byte
6ce4  68      PLA                        ; Restore the high byte
6ce5  955f    STA ship_vel_high,X        ; And store the high byte
6ce7  ca      DEX                        ; Decrement `i` twice
6ce8  ca      DEX                        ; since the loop is over 16-bit values
6ce9  3003    BMI ship_update_done       ; If `i` is now negative (2 -> 0 -> -2), we're done
6ceb  4c6a6c  JMP ship_update_loop       ; If not make another pass through the loop
.label ship_update_done:
6cee  60      RTS                        ; Ship position and velocity updated.  Return!
```
