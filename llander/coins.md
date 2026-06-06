## Coin handling

This is interesting because it has to deal with potential (physical) attacks on the coin slots,
which apparently was a problem with some other arcade cabinets.  The memory mapped coin detectors
are discussed in the button handling section.

### Coin insertion switches

The coin drop switches are only valid if they have been through
0016      .byte 00                       ;

```
; There are three coin buttons with active high coin detectors.
; They are potentially bouncy, so timers are used to try to avoid multiple triggers.
; And the player might be slamming the cabinet to try to trigger the sensor,
; so also check the vibration sensor.
;
; Note that only the two coin slots are used (0 and 2)
;
; Returns a set carry flag if a coin was detected.
;
.func CheckCoinsInserted:
78d3  a202    ldx #$02                   ; for each coin slot = 2, 0: (middle one is ignored)
.label check_coin:
78d5  bd0124  lda IO_in1_coin[0],X       ; read coin[i] from external device
78d8  0a      asl                        ; move bit 7 into the carry flag (0 == no coin, 1 == coin)
78d9  b5b7    lda _CNCT[2],X             ; read the debounce timer for this coin slot
78db  291f    and #$1f                   ; mask out the bottom bits of the debounce
78dd  b037    bcs CheckDropTimerVal      ; if carry flag is set (coin) check how long it has been active
78df  f010    beq CheckSlamSw            ; if the debounce timer is 0, check if the slam switch has been triggered
78e1  c91b    cmp #$1b                   ; if the debounce timer is less than 0x1b
78e3  b00a    bcs DecDropTimer           ; then goto debounce timer decrement
78e5  a8      tay                        ; store the debounce timer in `Y`
78e6  a5ba    lda TEST                   ; only decrement the debounce timer every
78e8  2907    and #$07                   ; eight NMI clock cycles
78ea  c907    cmp #$07                   ; which is 250/8 or about 30 Hz
78ec  98      tya                        ; restore the debounce timer
78ed  9002    bcc CheckSlamSw            ; skip the decrement until the eight NMI clock
.label DecDropTimer:
78ef  e901    sbc #$01                   ; decrement the debounce timer
.label CheckSlamSw:
78f1  95b7    sta _CNCT[2],X             ; store the (possibly updated) debounce timer
78f3  ad0020  lda IO_in0                 ; read the memory mapped switches at 0x2000
78f6  2904    and #$04                   ; check bit 2, the slam switch
78f8  d004    bne CheckSlamTimer         ; if it is not set, goto the slam timer check
78fa  a9f0    lda #$f0                   ; it is set, set the slam timer counter at 0xF0
78fc  85b4    sta _LMTIM                 ; and store it
.label CheckSlamTimer:
78fe  a5b4    lda _LMTIM                 ; Read the slam timer
7900  f008    beq CheckWaitTimer         ; If it is zero, check to see how the coin debouncers are doing
7902  c6b4    dec _LMTIM                 ; We're still waiting for slam timer to expire, so
7904  a900    lda #$00                   ; zero out the debounce counters
7906  95b7    sta _CNCT[2],X             ; for this coin slot
7908  95b3    sta _PSTSL,X               ; so that no coins will be accepted
.label CheckWaitTimer:
790a  18      clc                        ; clear carry flag
790b  b5b3    lda _PSTSL,X               ; is this coin slot in a cool down?
790d  f023    beq CheckNextMech          ; yes, goto check the next slot
790f  d6b3    dec _PSTSL,X               ; decrement the cool down timer
7911  d01f    bne CheckNextMech          ; if it is not yet zero, check the next coin slot
7913  38      sec                        ; set carry (indicating no coins from this slot)
7914  b01c    bcs CheckNextMech          ; and go check the next coin slot
.label CheckDropTimerVal:
7916  c91b    cmp #$1b                   ;
7918  b009    bcs ResetDropTimer         ;
791a  b5b7    lda _CNCT[2],X             ;
791c  6920    adc #$20                   ;
791e  90d1    bcc CheckSlamSw            ;
7920  f001    beq ResetDropTimer         ;
7922  18      clc                        ; clear carry (no coins)
.label ResetDropTimer:
7923  a91f    lda #$1f                   ;
7925  b0ca    bcs CheckSlamSw            ;
7927  95b7    sta _CNCT[2],X             ; Reset the debounce timer for this slot
7929  b5b3    lda _PSTSL,X               ; and the check if the cool down timer
792b  f001    beq SetWaitTimer           ; is zero (which means we haven't been waiting for a coin) so don't set the carry flag
792d  38      sec                        ; cool down was non-zero, so it is time to give them a credit by setting the carry
.label SetWaitTimer:
792e  a978    lda #$78                   ; Initialze the cool down timer to 120
7930  95b3    sta _PSTSL,X               ; which is about 1/2 a second between coins
.label CheckNextMech:
7932  9004    bcc DoNextCoinMech         ; if carry is not set, there is no coin in this slot, go to the next one
7934  f6b6    inc _CNCT[1],X             ; carry was set, so increment the number of credits for this slot!
7936  e6b2    inc _CCTIM                 ; and also increment the total number of coins inserted
.label DoNextCoinMech:
7938  ca      dex                        ; double decrement the index
7939  ca      dex                        ; since the middle one is ignored
793a  1099    bpl check_coin             ; if it is non-negative, make another loop
793c  e6ba    inc TEST                   ; increment our counter for each time the function is called
793e  a5ba    lda TEST                   ; Re read it the number of calls
7940  4a      lsr                        ; Shift the bottom bit of the counter into the carry
7941  a5b2    lda _CCTIM                 ; Read the number of valid coins
7943  b00c    bcs EndCoinCheck           ; if this is an odd numbered call, goto EndCoinCheck
7945  f00a    beq EndCoinCheck           ; if there are no valid coins, goto EndCoinCheck
7947  c910    cmp #$10                   ; if the valid coins are more than 10
7949  b002    bcs NextValidCoin_maybe    ; ??
794b  69ff    adc #$ff                   ; ??
.label NextValidCoin_maybe:
794d  69ef    adc #$ef                   ; ??
794f  85b2    sta _CCTIM                 ; Store this result back in ValidCoins
.label EndCoinCheck:
7951  0a      asl                        ; Shift it left (into the carry)
7952  60      rts                        ; and return the result to the caller
```

### Credits per coin and other config

There are switches that select how many credits the player receives for each coin, how much
fuel per credit, and the desired language (if the language ROM is installed).

```
.func coin_and_language_config:
796b  ad0328  lda IO_dsw1_RightCoin      ; Read the coin config switches
796e  2903    and #$03                   ; Mask out everything but the bottom two bits
7970  aa      tax                        ; .
7971  bd9b79  lda CoinMultTbl[0],X       ; Read the number of credits per coin from the table
7974  8599    sta M2_OPT                 ; And store it in the global for later
7976  a200    ldx #$00                   ;
7978  ee0058  inc string_table_language_offset[0] ; If reading the language ROM gives 0xFF,
797b  f006    beq set_language           ; then default to using language 0 == English
797d  ad0228  lda IO_dsw1_2              ; Read the language configuration switches
7980  2903    and #$03                   ; Mask out everything but the bottom two bits
7982  aa      tax                        ; .
.label set_language:
7983  8621    stx LANG                   ; Store the language in the global
7985  38      sec                        ; Set the carry
7986  ad0128  lda IO_dsw1_1              ; Load the fuel configuration switches
7989  2a      rol                        ;
798a  2a      rol                        ;
798b  2d0028  and IO_dsw1_0              ;
798e  290f    and #$0f                   ;
7990  6900    adc #$00                   ;
7992  c909    cmp #$09                   ;
7994  9002    bcc L7998                  ;
7996  a900    lda #$00                   ;
.label L7998:
7998  8598    sta C_OPT                  ;
799a  60      rts                        ;

.byte 799b CoinMultTbl 4 ; Coin multiplier table

.func draw_insert_coin_screen:
799f  a20c    ldx #$0c                   ;
79a1  a598    lda C_OPT                  ;
79a3  18      clc                        ;
79a4  6918    adc #$18                   ;
79a6  20347a  jsr WriteText_xy           ;
79a9  a917    lda #$17                   ;
79ab  204f7a  jsr WriteText              ;
79ae  a905    lda #$05                   ;
79b0  204f7a  jsr WriteText              ;
79b3  a586    lda FRAME                  ;
79b5  2920    and #$20                   ;
79b7  f007    beq L79c0                  ;
79b9  a200    ldx #$00                   ;
79bb  a904    lda #$04                   ;
79bd  4c347a  jmp WriteText_xy           ;
.label L79c0:
79c0  60      rts                        ;
```
