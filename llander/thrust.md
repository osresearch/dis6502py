## Thrust and Fuel

The player has a large lever that controls the thrust from the ship's engine.
More thrust burns more fuel and the game rewards good landings with more fuel.

### Fuel

The fuel is stored in BCD format, which means that each byte can represent up 00 - 99, so a
three byte value can represented 000000 to 999999.  The 6502 has a special mode in the ALU that
causes addition and subtraction to produce results in this format.  Games often used it
for scores since they wanted to display a base-10 value for the player.

```
; The remaining fuel is stored as a 3-byte BCD amount,
; which gives a maximum of 6 digits in base 10.
; It is stored in reverse order, so fuel_tank[0] is the LSB and fuel_tank[2] is MSB.
.byte ac fuel_tank 3 ; BCD amount of fuel in the tank
.byte a1 fuel_used 3 ; BCD amount of fuel used during the mission

; Bitmask tracking the current fuel (and game) state
; 0x80 = Have fuel
; 0x40 = Out of fuel
; 0x00 = Not playing
.byte 97 fuel_state				; Bitmask of fuel state
```

Various functions in the code will spend fuel, and they either call @fuel_drain_16 to drain a
two-byte amount, or the full @fuel_drain that takes a three-byte amount.  This is in BCD and
the `A:X:Y` calling convention is different from some other functions that work on multi-byte arguments.

```
; Drain a 16-bit BCD `X:Y` amount of fuel from the ship.
; This tail calls into @fuel_drain
.func fuel_drain_16:
6461  a900    LDA #$00                   ;

; Drain a 24-bit BCD `A:X:Y` amount of fuel from the ship
;
.func fuel_drain:
6463  f8      SED                        ; Enable Decimal mode since the fuel is in BCD
6464  8539    STA GenByte_0039           ; Cache the MSB of the argument into GenBytes 39
6466  8638    STX GenByte_0038           ; ... the middle byte into 38
6468  8437    STY GenByte_0037           ; ... the lowest byte into 37
646a  a5ac    LDA fuel_tank              ; Load LSB of fuel
646c  38      SEC                        ; Clear the carry (to start a SBC chain)
646d  e537    SBC GenByte_0037           ; fuel_tank[0] - GenByte37
646f  a8      TAY                        ; -> Y
6470  a5ad    LDA fuel_tank[1]           ; Load the middle byte of fuel
6472  e538    SBC GenByte_0038           ; fuel_tank[1] - GenByte38
6474  aa      TAX                        ; -> X
6475  a5ae    LDA fuel_tank[2]           ; Load the MSB of fuel
6477  e539    SBC GenByte_0039           ; fuel_tank[2] - GenByte39 -> A
6479  b014    BCS fuel_no_underflow      ; If carry is not set, the remaining fule did not go below zero
.label low_fuel:
647b  2497    BIT fuel_state             ; Read the @fuel_state global
647d  1029    BPL fuel_drain_done        ; If bit 7 is not set, then we've already run out of fuel
647f  a940    LDA #$40                   ; Store 0x40 indicting out of fuel
6481  8597    STA fuel_state             ; into @fuel_state
6483  a900    LDA #$00                   ; Write 00:00:00 into @fuel_tank
6485  85ac    STA fuel_tank              ; no fuel
6487  85ad    STA fuel_tank[1]           ; so sad
6489  85ae    STA fuel_tank[2]           ; burma shave
648b  858d    STA time_in_seconds        ; stop the clock?
648d  f00a    BEQ fuel_track_used        ; always taken
.label fuel_no_underflow:
648f  84ac    STY fuel_tank              ; Store LSB of the 3-byte remaining fuel
6491  86ad    STX fuel_tank[1]           ; Store the middle byte
6493  85ae    STA fuel_tank[2]           ; Store the MSB of @fuel_tank back in the global
6495  05ad    ORA fuel_tank[1]           ; Are both the middle and MSB zero?
6497  f0e2    BEQ low_fuel               ; If so we are in a low fuel state
.label fuel_track_used:
6499  18      CLC                        ; clear the carry to start an ADC chain
649a  a002    LDY #$02                   ; for x = 0,1,2
649c  a200    LDX #$00                   ; starting with the LSB
.label fuel_used_loop:
649e  b5a1    LDA fuel_used,X            ; add the amount of fuel drained
64a0  7537    ADC GenByte_0037,X         ; to the global @fuel_used
64a2  95a1    STA fuel_used,X            ; storing back in the global
64a4  e8      INX                        ; x++
64a5  88      DEY                        ; y--
64a6  10f6    BPL fuel_used_loop         ; if y isn't negative, do the next byte
.label fuel_drain_done:
64a8  d8      CLD                        ; Reset to binary mode (no more BCD)
64a9  60      RTS                        ; Return to the caller
```

The yaw routines burn a little bit of fuel, but most of the burn comes from the main engine.
This is handled here:

```
; While the main engine is thrusting, fuel is drained based on the lever position
.func fuel_drain_thrust:
6b71  a9da    LDA #$da                   ; Default is to lose 218 fuel per thrust unit
6b73  a40b    LDY thrust_value           ; If thrust mode is negative
6b75  3008    BMI fuel_thrust_multiply   ; then use the default
6b77  a623    LDX mission_difficulty     ; Otherwise if the mission is
6b79  e002    CPX #$02                   ; not equal to 2 ("Prime") with strong gravity
6b7b  d002    BNE fuel_thrust_multiply   ; then also use the default
6b7d  a990    LDA #$90                   ; Mission 2 gets a little less burn per thrust unit
.label fuel_thrust_multiply:
6b7f  20ef70  JSR mult16                 ; `A` = thrust cost `Y` = thrust setting
6b82  aa      TAX                        ; Ignores the low bits, uses just the high byte of the result
6b83  a000    LDY #$00                   ; Only use the bits in `X`
6b85  8437    STY GenByte_0037           ; So store 0 in gb37
6b87  a007    LDY #$07                   ; 8 digits requested
6b89  20c679  JSR dec_to_bcd             ; Converts the binary result to BCD
6b8c  a8      TAY                        ; Return is in `Y:X:A`, but @fuel_drain_16 wants `X:Y`
6b8d  4c6164  JMP fuel_drain_16          ; drains that much fuel (tail call)


; When the ship crashes, a random amount of fuel is lost
.func fuel_lost_to_crash_wrapper:
6b90  a55d    LDA ship_state_maybe       ; If any of the bottom bits in ship_state are set
6b92  290f    AND #$0f                   ; (bottom bits mean exploding?)
6b94  f049    BEQ rts_6bdf               ; then return immediately
.func fuel_lost_to_crash:
6b96  f8      SED                        ;
6b97  a59e    LDA score_bcd_maybe        ;
6b99  38      SEC                        ;
6b9a  e5a2    SBC fuel_used[1]           ;
6b9c  aa      TAX                        ;
6b9d  a59f    LDA Z9f                    ;
6b9f  e5a3    SBC fuel_used[2]           ;
6ba1  a8      TAY                        ;
6ba2  a5a0    LDA Za0                    ;
6ba4  e900    SBC #$00                   ;
6ba6  d8      CLD                        ;
6ba7  9036    BCC rts_6bdf               ;
6ba9  f004    BEQ L6baf                  ;
6bab  a299    LDX #$99                   ;
6bad  a099    LDY #$99                   ;
.label L6baf:
6baf  8a      TXA                        ;
6bb0  d003    BNE L6bb5                  ;
6bb2  98      TYA                        ;
6bb3  f02a    BEQ rts_6bdf               ;
.label L6bb5:
6bb5  98      TYA                        ;
6bb6  a4ad    LDY fuel_tank[1]           ;
6bb8  843a    STY GenByte_003a           ;
6bba  a4ae    LDY fuel_tank[2]           ;
6bbc  843b    STY GenByte_003b           ;
6bbe  a000    LDY #$00                   ;
6bc0  84a2    STY fuel_used[1]           ;
6bc2  84a3    STY fuel_used[2]           ;
6bc4  206364  JSR fuel_drain             ;
6bc7  a5a2    LDA fuel_used[1]           ;
6bc9  a6a3    LDX fuel_used[2]           ;
6bcb  2497    BIT fuel_state             ;
6bcd  3004    BMI L6bd3                  ;
6bcf  a53a    LDA GenByte_003a           ;
6bd1  a63b    LDX GenByte_003b           ;
.label L6bd3:
6bd3  8595    STA fuel_lost_bcd          ;
6bd5  8696    STX Z96                    ;
6bd7  0596    ORA Z96                    ;
6bd9  f004    BEQ rts_6bdf               ;
6bdb  a97f    LDA #$7f                   ;
6bdd  8590    STA fuel_lost_timeout      ;

; Another shared `RTS`
.func rts_6bdf:
6bdf  60      RTS                        ; Shared with a few nearby functions
```

### Thrust

```
.byte 0b thrust_value ; one of the 16 levels of thrust
```

```
.func thrust_smoothing_maybe:
6414  2422    BIT game_state_flags       ;
6416  5004    BVC L641c                  ;
6418  a556    LDA ship_abort             ;
641a  d044    BNE L6460                  ;
.label L641c:
641c  a584    LDA thrust_low             ;
641e  4a      LSR                        ;
641f  4a      LSR                        ;
6420  aa      TAX                        ;
6421  4a      LSR                        ;
6422  8537    STA GenByte_0037           ;
6424  a000    LDY #$00                   ;
6426  e482    CPX thrust_delta_last_raw  ;
6428  b01a    BCS L6444                  ;
642a  a584    LDA thrust_low             ;
642c  38      SEC                        ;
642d  e582    SBC thrust_delta_last_raw  ;
642f  a00f    LDY #$0f                   ;
6431  9011    BCC L6444                  ;
6433  c537    CMP GenByte_0037           ;
6435  900d    BCC L6444                  ;
6437  a582    LDA thrust_delta_last_raw  ;
6439  a484    LDY thrust_low             ;
643b  20c070  JSR divide                 ;
643e  8a      TXA                        ;
643f  4a      LSR                        ;
6440  4a      LSR                        ;
6441  4a      LSR                        ;
6442  4a      LSR                        ;
6443  a8      TAY                        ;
.label L6444:
6444  8401    STY actual_thrust_maybe    ;
6446  a000    LDY #$00                   ;
6448  a585    LDA thrust_something_counter ;
644a  c94b    CMP #$4b                   ;
644c  9008    BCC L6456                  ;
644e  e683    INC thrust_high            ;
6450  c684    DEC thrust_low             ;
6452  c684    DEC thrust_low             ;
6454  8485    STY thrust_something_counter ;
.label L6456:
6456  2497    BIT fuel_state             ;
6458  1004    BPL L645e                  ;
645a  a522    LDA game_state_flags       ;
645c  d002    BNE L6460                  ;
.label L645e:
645e  8401    STY actual_thrust_maybe    ;
.label L6460:
6460  60      RTS                        ; Return to caller
```

