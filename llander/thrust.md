## Thrust and Fuel

The player has a large lever that controls the thrust from the ship's engine.
More thrust burns more fuel and the game rewards good landings with more fuel.

### Fuel

The fuel is stored in BCD format, which means that each byte can represent up 00 - 99, so a
three byte value can represented 000000 to 999999.  The 6502 has a special mode in the ALU that
causes addition and subtraction to produce results in this format.  Games often used it
for scores since they wanted to display a base-10 value for the player.

The remaining fuel is stored as a 3-byte BCD amount, which gives a maximum of 6 digits in base 10.
It is stored in reverse order, so fuel_tank[0] is the LSB and fuel_tank[2] is MSB.

Various functions in the code will spend fuel, and they either call @fuel_drain_16 to drain a
two-byte amount, or the full @fuel_drain that takes a three-byte amount.  This is in BCD and
the `A:X:Y` calling convention is different from some other functions that work on multi-byte arguments.

```
; Drain a 16-bit BCD `X:Y` amount of fuel from the ship.
; This tail calls into @fuel_drain
.func fuel_drain_16:
6461  a900    lda #$00                   ;

; Drain a 24-bit BCD `A:X:Y` amount of fuel from the ship
;
.func fuel_drain:
6463  f8      sed                        ; Enable Decimal mode since the fuel is in BCD
6464  8539    sta TEMP3                  ; Cache the MSB of the argument into GenBytes 39
6466  8638    stx TEMP2                  ; ... the middle byte into 38
6468  8437    sty TEMP1                  ; ... the lowest byte into 37
646a  a5ac    lda FUEL[0]                ; Load LSB of fuel
646c  38      sec                        ; Clear the carry (to start a SBC chain)
646d  e537    sbc TEMP1                  ; fuel_tank[0] - GenByte37
646f  a8      tay                        ; -> Y
6470  a5ad    lda FUEL[1]                ; Load the middle byte of fuel
6472  e538    sbc TEMP2                  ; fuel_tank[1] - GenByte38
6474  aa      tax                        ; -> X
6475  a5ae    lda FUEL[2]                ; Load the MSB of fuel
6477  e539    sbc TEMP3                  ; fuel_tank[2] - GenByte39 -> A
6479  b014    bcs fuel_no_underflow      ; If carry is not set, the remaining fule did not go below zero
.label low_fuel:
647b  2497    bit CRDTFLG                ; Read the credit_flag global
647d  1029    bpl fuel_drain_done        ; If bit 7 is not set, then we've already run out of fuel
647f  a940    lda #$40                   ; Store 0x40 indicting out of fuel
6481  8597    sta CRDTFLG                ; into credit_flag
6483  a900    lda #$00                   ; Write 00:00:00 into fuel_tank
6485  85ac    sta FUEL[0]                ; no fuel
6487  85ad    sta FUEL[1]                ; so sad
6489  85ae    sta FUEL[2]                ; burma shave
648b  858d    sta TIMER                  ; stop the clock?
648d  f00a    beq fuel_track_used        ; always taken
.label fuel_no_underflow:
648f  84ac    sty FUEL[0]                ; Store LSB of the 3-byte remaining fuel
6491  86ad    stx FUEL[1]                ; Store the middle byte
6493  85ae    sta FUEL[2]                ; Store the MSB of fuel_tank back in the global
6495  05ad    ora FUEL[1]                ; Are both the middle and MSB zero?
6497  f0e2    beq low_fuel               ; If so we are in a low fuel state
.label fuel_track_used:
6499  18      clc                        ; clear the carry to start an ADC chain
649a  a002    ldy #$02                   ; for x = 0,1,2
649c  a200    ldx #$00                   ; starting with the LSB
.label fuel_used_loop:
649e  b5a1    lda FLUSE[0],X             ; add the amount of fuel drained
64a0  7537    adc TEMP1,X                ; to the global fuel_used
64a2  95a1    sta FLUSE[0],X             ; storing back in the global
64a4  e8      inx                        ; x++
64a5  88      dey                        ; y--
64a6  10f6    bpl fuel_used_loop         ; if y isn't negative, do the next byte
.label fuel_drain_done:
64a8  d8      cld                        ; Reset to binary mode (no more BCD)
64a9  60      rts                        ; Return to the caller
```

The yaw routines burn a little bit of fuel, but most of the burn comes from the main engine.
This is handled here:

```
; While the main engine is thrusting, fuel is drained based on the lever position
.func fuel_drain_thrust:
6b71  a9da    lda #$da                   ; Default is to lose 218 fuel per thrust unit
6b73  a40b    ldy THRSTLV                ; If thrust mode is negative
6b75  3008    bmi fuel_thrust_multiply   ; then use the default
6b77  a623    ldx PLYMOD                 ; Otherwise if the mission is
6b79  e002    cpx #$02                   ; not equal to 2 ("Prime") with strong gravity
6b7b  d002    bne fuel_thrust_multiply   ; then also use the default
6b7d  a990    lda #$90                   ; Mission 2 gets a little less burn per thrust unit
.label fuel_thrust_multiply:
6b7f  20ef70  jsr mult16                 ; `A` = thrust cost `Y` = thrust setting
6b82  aa      tax                        ; Ignores the low bits, uses just the high byte of the result
6b83  a000    ldy #$00                   ; Only use the bits in `X`
6b85  8437    sty TEMP1                  ; So store 0 in gb37
6b87  a007    ldy #$07                   ; 8 digits requested
6b89  20c679  jsr dec_to_bcd             ; Converts the binary result to BCD
6b8c  a8      tay                        ; Return is in `Y:X:A`, but @fuel_drain_16 wants `X:Y`
6b8d  4c6164  jmp fuel_drain_16          ; drains that much fuel (tail call)


; When the ship crashes, a random amount of fuel is lost
.func fuel_lost_to_crash_wrapper:
6b90  a55d    lda COLFLG                 ; If any of the bottom bits in ship_state are set
6b92  290f    and #$0f                   ; (bottom bits mean exploding?)
6b94  f049    beq rts_6bdf               ; then return immediately
.func fuel_lost_to_crash:
6b96  f8      sed                        ;
6b97  a59e    lda FLMIN[0]               ;
6b99  38      sec                        ;
6b9a  e5a2    sbc FLUSE[1]               ;
6b9c  aa      tax                        ;
6b9d  a59f    lda FLMIN[1]               ;
6b9f  e5a3    sbc FLUSE[2]               ;
6ba1  a8      tay                        ;
6ba2  a5a0    lda FLMIN[2]               ;
6ba4  e900    sbc #$00                   ;
6ba6  d8      cld                        ;
6ba7  9036    bcc rts_6bdf               ;
6ba9  f004    beq L6baf                  ;
6bab  a299    ldx #$99                   ;
6bad  a099    ldy #$99                   ;
.label L6baf:
6baf  8a      txa                        ;
6bb0  d003    bne L6bb5                  ;
6bb2  98      tya                        ;
6bb3  f02a    beq rts_6bdf               ;
.label L6bb5:
6bb5  98      tya                        ;
6bb6  a4ad    ldy FUEL[1]                ;
6bb8  843a    sty TEMP4                  ;
6bba  a4ae    ldy FUEL[2]                ;
6bbc  843b    sty TEMP5                  ;
6bbe  a000    ldy #$00                   ;
6bc0  84a2    sty FLUSE[1]               ;
6bc2  84a3    sty FLUSE[2]               ;
6bc4  206364  jsr fuel_drain             ;
6bc7  a5a2    lda FLUSE[1]               ;
6bc9  a6a3    ldx FLUSE[2]               ;
6bcb  2497    bit CRDTFLG                ;
6bcd  3004    bmi L6bd3                  ;
6bcf  a53a    lda TEMP4                  ;
6bd1  a63b    ldx TEMP5                  ;
.label L6bd3:
6bd3  8595    sta FLDED[0]               ;
6bd5  8696    stx FLDED[1]               ;
6bd7  0596    ora FLDED[1]               ;
6bd9  f004    beq rts_6bdf               ;
6bdb  a97f    lda #$7f                   ;
6bdd  8590    sta MSCNT1                 ;

; Another shared `RTS`
.func rts_6bdf:
6bdf  60      rts                        ; Shared with a few nearby functions
```

### Thrust

```
.func thrust_smoothing_maybe:
6414  2422    bit GAMODE                 ;
6416  5004    bvc L641c                  ;
6418  a556    lda INDEX                  ;
641a  d044    bne L6460                  ;
.label L641c:
641c  a584    lda PTRNGE                 ;
641e  4a      lsr                        ;
641f  4a      lsr                        ;
6420  aa      tax                        ;
6421  4a      lsr                        ;
6422  8537    sta TEMP1                  ;
6424  a000    ldy #$00                   ;
6426  e482    cpx POTVAL                 ;
6428  b01a    bcs L6444                  ;
642a  a584    lda PTRNGE                 ;
642c  38      sec                        ;
642d  e582    sbc POTVAL                 ;
642f  a00f    ldy #$0f                   ;
6431  9011    bcc L6444                  ;
6433  c537    cmp TEMP1                  ;
6435  900d    bcc L6444                  ;
6437  a582    lda POTVAL                 ;
6439  a484    ldy PTRNGE                 ;
643b  20c070  jsr divide                 ;
643e  8a      txa                        ;
643f  4a      lsr                        ;
6440  4a      lsr                        ;
6441  4a      lsr                        ;
6442  4a      lsr                        ;
6443  a8      tay                        ;
.label L6444:
6444  8401    sty THRUST                 ;
6446  a000    ldy #$00                   ;
6448  a585    lda POTUSE                 ;
644a  c94b    cmp #$4b                   ;
644c  9008    bcc L6456                  ;
644e  e683    inc POTMIN                 ;
6450  c684    dec PTRNGE                 ;
6452  c684    dec PTRNGE                 ;
6454  8485    sty POTUSE                 ;
.label L6456:
6456  2497    bit CRDTFLG                ;
6458  1004    bpl L645e                  ;
645a  a522    lda GAMODE                 ;
645c  d002    bne L6460                  ;
.label L645e:
645e  8401    sty THRUST                 ;
.label L6460:
6460  60      rts                        ; Return to caller
```

