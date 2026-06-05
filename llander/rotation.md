## Ship rotation


### Buttons

The first function we're going to look at to keep things simple is the one
that reads the player's rotation buttons.

```
.func IO_read_rotate_buttons
6404  a200    LDX #$00                   ; X = 0
6406  2c0624  BIT IO_in1_yaw_right       ; Read the right button from the IO port
6409  1001    BPL not_right              ; If bit 7 is not set, Button is not pressed, jump to @0x640c
640b  ca      DEX                        ; X = X - 1
.label not_right
640c  2c0724  BIT IO_in1_yaw_left        ; Read the left button from the IO port
640f  1001    BPL not_left               ; Button is not pressed, jump to @0x6412
6411  e8      INX                        ; X = X + 1
.label not_left
6412  8a      TXA                        ; A = X
6413  60      RTS                        ; Return 0 if neither or both buttons are pessed, -1 for right, +1 for left
```

This could also be rewritten into something like C:

<pre>
volatile uint8_t * const IO_button_right = (void*) 0x2406;
volatine uint8_t * const IO_button_left = (void*) 0x2407;
int IO_read_rotate_buttons(void)
{
  int yaw = 0;
  if (*IO_button_right & 0x80)
    yaw--;
  if (*IO_button_left & 0x80)
    yaw++;
  return yaw;
}
</pre>

We now know something about the way the game tracks orientation and that it uses a reference frame where positive
rotation is to the left.
Based on the cross references, we can see that this function is called by the @ship_command_yaw and @ship_command_yaw_easy
functions.  Let's look at that first one since it's "easier":


### Yaw (Easy)

```
; Control the ship's yaw by adjusting the angle.
; In the three easy modes the player only controls the rotation angle of the ship
; with the rotate left and rotate right buttons.
; In the easiest mode the ship is limited to mostly upright angles.
;
; Yawing does cost a small amount of fuel and there is a tail call
; to @yaw_drain_fuel.
;
.func ship_command_yaw_easy
63d4  2497    BIT fuel_state             ; Read the fuel variable
63d6  10fb    BPL rts_63d3               ; If bit 8 is not set (no fuel) jump to the shared RTS
63d8  200464  JSR IO_read_rotate_buttons ; Read the rotation buttons
63db  f0f6    BEQ rts_63d3               ; If neither (or both) are set, no rotation so jump to the shared RTS
63dd  18      CLC                        ; Clear carry flag
63de  6567    ADC ship_angle_high        ; A = Rotation (+1/-1) plus the high byte of the ship's angle
63e0  8567    STA ship_angle_high        ; Store the updated rotation back into the high byte
63e2  aa      TAX                        ; Cache the high byte in X
63e3  4a      LSR                        ; A = A / 2
63e4  4a      LSR                        ; A = A / 2
63e5  291f    AND #$1f                   ; A = (Rotation / 4) % 32 -- how far is the angle into the quadrant
63e7  8502    STA ship_angle_modulo      ; Store this remainder
63e9  a523    LDA mission_difficulty     ; What's the current difficulty level?
63eb  d011    BNE yaw_drain_fuel         ; Non-zero difficulty allows arbitrary rotation angles
63ed  e8      INX                        ; But level 0 prevents the ship from rotating past +/- 90 deg
63ee  f006    BEQ cancel_rotation        ; if this is 0, the ship would have rotated too far
63f0  e042    CPX #$42                   ;
63f2  d00a    BNE yaw_drain_fuel         ;
63f4  a910    LDA #$10                   ;
.label cancel_rotation
63f6  8502    STA ship_angle_modulo      ; Store the corrected remainder
63f8  0a      ASL                        ;
63f9  0a      ASL                        ;
63fa  8567    STA ship_angle_high        ; And store the correct high byte for the ship's angle
63fc  90d5    BCC rts_63d3               ; if no rotation happened do not drain any fuel, otherwise fall through into @yaw_drain_fuel

; Wrapper that drains a small amount of fuel when yawing.
; All difficulties use this.
; There is a tail call to @fuel_drain
.func yaw_drain_fuel
63fe  a200    LDX #$00                   ; Pass a 16-bit BCD value 0x0600 to
6400  a006    LDY #$06                   ; the fuel drain wrapper
6402  d05d    BNE fuel_drain_16          ; (Always taken)
```

Note that the last instruction in the function is a `BNE`, even though a constant non-zero value has just
been loaded into `Y`, so it becomes an always-taken relative jump.  This is one byte shorter than
the equivilant `JMP` instruction.

```
.func rts_63d3
63d3  60      RTS                        ; Shared RTS instruction used by several functions
```

Another way that programmers saved memory was by reusing instructions across different functions.
The "function" at @63d3 is a single `RTS` instruction that other nearby functions use
instead of having their own `RTS`.  This complicates the control-flow analysis of tools
like ghidra and sometimes requires manual annotation to decompile.



### Yaw (Hard)

```
; Missions are selected with the "Game Select" button and range from 0 - 3:
;
; 0 "Training" Light gravity     Friction     Controlled Rotation
; 1 "Cadet"    Moderate gravity  No Friction  Controlled Rotation
; 2 "Prime"    Strong gravity    No Friction  Controlled Rotation
; 3 "Command"  Moderate gravity  No Friction  Rotational Momentum
;
.byte 23 mission_difficulty ; Mission difficulty 0 - 3
```

```
; @ship_command_yaw handles the hard yaw mode in difficulty 3 "Command"
; where the player controls the yaw thrusters, rather than the angle.
; this allows the ship to rotate all the way around and they have to stop
; rotation by firing the opposite thruster.  it's really hard!
;
; if the game is in a lower difficulty mission, then @ship_command_yaw_easy will
; be called instead.
.func ship_command_yaw:
633c  a556    LDA ship_abort             ; Only process commands if @ship_abort is not set
633e  f001    BEQ not_aborting           ;
6340  60      RTS                        ; Abort in process, nothing to do here
.label not_aborting:
6341  a523    LDA mission_difficulty     ; Use the easy mode for yaw commands other than
6343  c903    CMP #$03                   ; if @mission_difficulty == 3 ("Command")
6345  f003    BEQ yaw_momentum           ; then we will use yaw momentum that is much harder
6347  4cd463  JMP ship_command_yaw_easy  ; else Tail position call to @ship_command_yaw_easy
.label yaw_momentum:
634a  a566    LDA ship_angle             ; @ship_angle += @yaw_rate
634c  18      CLC                        ; these are normal signed
634d  6503    ADC yaw_rate               ; 16-bit values, so the
634f  8566    STA ship_angle             ; code is much simpler than
6351  a567    LDA ship_angle_high        ; the signed magnitude stuff
6353  6504    ADC yaw_rate_high          ; that comes later
6355  8567    STA ship_angle_high        ; for the @ship_update
6357  4a      LSR                        ; Divide the high-byte of the angle
6358  4a      LSR                        ; by four
6359  291f    AND #$1f                   ; And mask it down to 0-31
635b  8502    STA ship_angle_modulo      ; Store it in the 8-bit ship angle
635d  a000    LDY #$00                   ;
635f  a503    LDA yaw_rate               ;
6361  a604    LDX yaw_rate_high          ;
6363  f00a    BEQ yaw_rate_high_zero     ; if @yaw_rate high == 0, then check low
6365  e8      INX                        ; increment `X`
6366  d00b    BNE yaw_check_fuel         ; if @yaw_rate high != 0xFF, then don't set yaw dir
6368  c9c0    CMP #$c0                   ; if @yaw_rate > -0x40
636a  9007    BCC yaw_check_fuel         ; then don't set yaw dir
.label set_yaw_slow:
636c  88      DEY                        ; decrement `Y` to mark that maybe we are close enough to stopped?
636d  3004    BMI yaw_check_fuel         ; always taken since `Y` now = -1
.label yaw_rate_high_zero:
636f  c941    CMP #$41                   ; if @yaw_rate < 0x41
6371  90f9    BCC set_yaw_slow           ; then jump to @set_yaw_slow
.label yaw_check_fuel:
6373  8405    STY yaw_slow               ; Set if @yaw_rate is close enough to zero to be almost stopped
6375  2497    BIT fuel_state             ; Do we have any fuel left?
6377  105a    BPL rts_63d3               ; If bit 7 is not set, we can't fire yaw thruster, so return
6379  200464  JSR IO_read_rotate_buttons ; We have some fuel, so see if the player has pressed yaw button
637c  0a      ASL                        ; The result in A is +/- 1
637d  0a      ASL                        ; Shift-left
637e  0a      ASL                        ; four times
637f  0a      ASL                        ; to result in +/-16
6380  a000    LDY #$00                   ; `Y` is the high-byte for the yaw button command
6382  29f0    AND #$f0                   ; Mask out the bottom bits of the yaw command (which should already be 0)
6384  f025    BEQ no_yaw_command         ; If they are not pressing a button?
6386  9001    BCC yaw_cmd_left           ; If positive yaw command, then we're going left `Y:A` = +16
6388  88      DEY                        ; Going right: `Y:A` = -16
.label yaw_cmd_left:
6389  18      CLC                        ; 16-bit add of `Y:A` and @yaw_rate
638a  6503    ADC yaw_rate               ; add the low bytes
638c  aa      TAX                        ; cache the result low byte in `X`
638d  98      TYA                        ; move the high byte of the yaw command into `A`
638e  6504    ADC yaw_rate_high          ; add the high bytes
6390  100a    BPL yaw_positive           ; if @yaw_rate > 0 goto @yaw_positive
6392  c9fc    CMP #$fc                   ; if @yaw_rate > -0x400
6394  b00e    BCS store_yaw_rate         ; -- goto @yaw_positive
6396  a9fc    LDA #$fc                   ; cap @yaw_rate at -0x400
6398  a200    LDX #$00                   ; which is 0xFC00 as a 16-bit value
639a  f008    BEQ store_yaw_rate         ; always taken
.label yaw_positive:
639c  c904    CMP #$04                   ; if @yaw_rate < +0x400
639e  9004    BCC store_yaw_rate         ; -- goto @yaw_positive
63a0  a903    LDA #$03                   ; cap @yaw_rate at +0x03e0
63a2  a2e0    LDX #$e0                   ; which is 0x03e0 since it is positive
.label store_yaw_rate:
63a4  8504    STA yaw_rate_high          ; store the high byte
63a6  8603    STX yaw_rate               ; store the low byte
63a8  4cfe63  JMP yaw_drain_fuel         ; tail position call to spend some fuel for firing the yaw thrusters
.label no_yaw_command:
63ab  a505    LDA yaw_slow               ; if @yaw_slow == 0 (are we slow enough?)
63ad  f01e    BEQ update_yaw_nonzero     ; then nothing to do
63af  a506    LDA yaw_nonzero            ; is @yaw_nonzero == 0
63b1  f005    BEQ L63b8                  ;
63b3  a900    LDA #$00                   ; Set the new @yaw_rate to be 0
63b5  aa      TAX                        ; high and low bytes in `X:A` == 0
63b6  f011    BEQ update_yaw_rate        ; always taken
.label L63b8:
63b8  a503    LDA yaw_rate               ; Check for @yaw_rate == 0
63ba  0504    ORA yaw_rate_high          ; high and low bytes
63bc  f00f    BEQ update_yaw_nonzero     ; and update the @yaw_nonzero value
63be  a950    LDA #$50                   ; Decay the yaw rate to `0x0050`
63c0  a200    LDX #$00                   ; by setting `X:A`
63c2  2404    BIT yaw_rate_high          ; if @yaw_rate is positive
63c4  1003    BPL update_yaw_rate        ; then use this value
63c6  a9b0    LDA #$b0                   ; else set `X:A` to `0xFFB0`
63c8  ca      DEX                        ; (by decrement)
.label update_yaw_rate:
63c9  8604    STX yaw_rate_high          ; Store `X:A` into the @yaw_rate
63cb  8503    STA yaw_rate               ; high and low bytes
.label update_yaw_nonzero:
63cd  a503    LDA yaw_rate               ; are any bits set in the @yaw_rate
63cf  0504    ORA yaw_rate_high          ; high or low bytes?
63d1  8506    STA yaw_nonzero            ; if so update @yaw_nonzero
```

```
.word 03 yaw_rate			; 16-bit yaw rate for momentum mode
.byte 05 yaw_slow			; Is the yaw rate slow enough to decay
.byte 06 yaw_nonzero			; Is the yaw rate non-zero
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

```
.byte 62a7 mission_gravity 4 ; Gravity settings for the different missions
.byte 62e2 mission_lamps 4 ; Bitmask of lamps to illuminate based on the mission difficulty
```

```
; Reset the ship but keep the angle the same
.func ship_reset_saved_angle:
62bc  a502    LDA ship_angle_modulo      ; Load the current ship angle and fall through

; Reset the ship to a new angle and re-read the mission parameters
; `A`: Ship's starting angle from 0 - 31
.func ship_reset:
62be  0a      ASL                        ; Multiply the small angle
62bf  0a      ASL                        ; by four
62c0  8567    STA ship_angle_high        ; and store that in the high byte of the ship angle
62c2  a900    LDA #$00                   ; Memset the yaw_rate, yaw_slow and yaw_nonzero
62c4  a203    LDX #$03                   ; parameters to 0
.label ship_reset_bzero:
62c6  9503    STA yaw_rate,X             ; bzzzzt
62c8  ca      DEX                        ; x--
62c9  10fb    BPL ship_reset_bzero       ; keep bzeroing
62cb  8566    STA ship_angle             ; zero the low byte of the ship angle
62cd  a623    LDX mission_difficulty     ; Read the current mission setting
62cf  bda762  LDA mission_gravity[0],X   ; Read the mission specific gravity
62d2  8563    STA gravity                ; and store it in a global
62d4  bde262  LDA mission_lamps[0],X     ; Read the lamps to illuminate for this mission
62d7  aa      TAX                        ; Move them to X
62d8  a9f0    LDA #$f0                   ; Keep the rest of the bits on
62da  4c5f79  JMP io_lamps_set           ; make a tail call to turn on the lamps
```



### Ship Position and Velocity update

The @mult16 function is used to compute the ship's X and Y acceleration based on the current thrust,
a thrust-to-force lookup table, and then multiplying by the sine and cosine of the ship's angle to
rotate the force into the screen coordinate frame.

```
.byte 76f2 sine_quadrants 4 ; Define the quadrants
.byte 76f6 thrust_to_acc 16 ; How much acceleration comes from the different thrust levels
.byte 76e9 sine_table 9 ; Reduced sine table for 0-45 degrees
```

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
6b38  bdf276  LDA sine_quadrants[0],X    ; Read the quadrant bits (bit 7 = X direction, bit 6 = Y direction)
6b3b  8546    STA ship_accel_sign[0]     ; Store the X accleration sign bit (used by @add16_signed_mag)
6b3d  0a      ASL                        ; Shift it left once
6b3e  8547    STA ship_accel_sign[1]     ; Store the Y acceleration sign bit
6b40  a601    LDX actual_thrust_maybe    ;
6b42  bdf676  LDA thrust_to_acc[0],X     ;
6b45  850b    STA thrust_value           ;
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
6b5c  bde976  LDA sine_table[0],X        ;
6b5f  a40b    LDY thrust_value           ;
6b61  20ef70  JSR mult16                 ;
6b64  8558    STA ship_accel[0]          ;
6b66  a637    LDX GenByte_0037           ;
6b68  bde976  LDA sine_table[0],X        ;
6b6b  20ef70  JSR mult16                 ;
6b6e  8559    STA ship_accel[1]          ;
6b70  60      RTS                        ;
```


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
6c78  b55f    LDA ship_vel_high[0],X     ; Copy the high byte of the velocity for this axis
6c7a  8548    STA delta2                 ; into the low-byte of @delta2
6c7c  b55e    LDA ship_vel[0],X          ; Load the low byte of the ship's velocity
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
6c90  b508    LDA ship_pos_high[0],X     ; Get the position high byte for this axis
6c92  48      PHA                        ; Push it
6c93  b507    LDA ship_pos[0],X          ; Get the position low byte
6c95  aa      TAX                        ; move it into `X`
6c96  68      PLA                        ; Pop the high byte so that the 16-bit position is in `A:X`
6c97  20006d  JSR add16_signed_mag_arg1  ; Compute Position + Velocity for this axis
6c9a  a637    LDX GenByte_0037           ; Restore the iterator
6c9c  9508    STA ship_pos_high[0],X     ; Write the high byte for this axis
6c9e  9407    STY ship_pos[0],X          ; and write the low byte for this axis
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
6cb1  b55f    LDA ship_vel_high[0],X     ; And load `A:X` with this axis' 16-bit velocity magnitutde
6cb3  48      PHA                        ; (same logic as before
6cb4  b55e    LDA ship_vel[0],X          ; to push things onto the stack
6cb6  aa      TAX                        ; and the pop them off again
6cb7  68      PLA                        ; into the right registers)
6cb8  20fe6c  JSR add16_signed_mag       ; Compute Velocity + Gravity for this axis
6cbb  a537    LDA GenByte_0037           ; Restore the iterator
6cbd  4a      LSR                        ; Divide it by two
6cbe  aa      TAX                        ; and move it back to X
6cbf  b558    LDA ship_accel[0],X        ; Get the 8-bit magnitude of the ship's thrust on this axis
6cc1  8548    STA delta2                 ; and copy it into @delta2
6cc3  b546    LDA ship_accel_sign[0],X   ; Get the thrust sign bit
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
6ce2  945e    STY ship_vel[0],X          ; Update the velocity low byte
6ce4  68      PLA                        ; Restore the high byte
6ce5  955f    STA ship_vel_high[0],X     ; And store the high byte
6ce7  ca      DEX                        ; Decrement `i` twice
6ce8  ca      DEX                        ; since the loop is over 16-bit values
6ce9  3003    BMI ship_update_done       ; If `i` is now negative (2 -> 0 -> -2), we're done
6ceb  4c6a6c  JMP ship_update_loop       ; If not make another pass through the loop
.label ship_update_done:
6cee  60      RTS                        ; Ship position and velocity updated.  Return!
```
