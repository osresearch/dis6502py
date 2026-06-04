## Ship rotation

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
