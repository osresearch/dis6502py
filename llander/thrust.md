## Thrust and Fuel

The player has a large lever that controls the thrust from the ship's engine.
More thrust burns more fuel and the game rewards good landings with more fuel.

### Fuel

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

### Thrust


