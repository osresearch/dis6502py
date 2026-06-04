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
63fc  90d5    BCC rts_63d3               ; no rotation happened, so do not drain any fuel
.label yaw_drain_fuel
63fe  a200    LDX #$00                   ; Pass a 16-bit BCD value 0x0600 to
6400  a006    LDY #$06                   ; the fuel drain wrapper
6402  d05d    BNE fuel_drain_wrapper     ; (Always taken)
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
```
