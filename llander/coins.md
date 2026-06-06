## Coin handling

This is interesting because it has to deal with potential (physical) attacks on the coin slots,
which apparently was a problem with some other arcade cabinets.  The memory mapped coin detectors
are discussed in the button handling section.

### Coin insertion switches

```
; The coin drop switches are only valid if they have been through
; 16 debounce timers, which is 16 * NMI/8, or about 0.5 seconds
.byte b7 CoinDropTimers 3 ; Debounce timer for each coin slot

.byte b3 WaitCoinTimer_0 ; This is actually an array, but the slam timer is in the middle
.byte b4 SlamTimer ; Counter for the vibration / tilt switch to detect cheating
.byte b4 WaitCoinTimer_2 ; Coin slot 2 timer
.byte ba coin_check_counter ; Track how often the coin handling routine is called
```

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
78d3  a202    LDX #$02                   ; for each coin slot = 2, 0: (middle one is ignored)
.label check_coin:
78d5  bd0124  LDA IO_in1_coin[0],X       ; read coin[i] from external device
78d8  0a      ASL                        ; move bit 7 into the carry flag (0 == no coin, 1 == coin)
78d9  b5b7    LDA CoinDropTimers[0],X    ; read the debounce timer for this coin slot
78db  291f    AND #$1f                   ; mask out the bottom bits of the debounce
78dd  b037    BCS CheckDropTimerVal      ; if carry flag is set (coin) check how long it has been active
78df  f010    BEQ CheckSlamSw            ; if the debounce timer is 0, check if the slam switch has been triggered
78e1  c91b    CMP #$1b                   ; if the debounce timer is less than 0x1b
78e3  b00a    BCS DecDropTimer           ; then goto debounce timer decrement
78e5  a8      TAY                        ; store the debounce timer in `Y`
78e6  a5ba    LDA coin_check_counter     ; only decrement the debounce timer every
78e8  2907    AND #$07                   ; eight NMI clock cycles
78ea  c907    CMP #$07                   ; which is 250/8 or about 30 Hz
78ec  98      TYA                        ; restore the debounce timer
78ed  9002    BCC CheckSlamSw            ; skip the decrement until the eight NMI clock
.label DecDropTimer:
78ef  e901    SBC #$01                   ; decrement the debounce timer
.label CheckSlamSw:
78f1  95b7    STA CoinDropTimers[0],X    ; store the (possibly updated) debounce timer
78f3  ad0020  LDA IO_in0                 ; read the memory mapped switches at 0x2000
78f6  2904    AND #$04                   ; check bit 2, the slam switch
78f8  d004    BNE CheckSlamTimer         ; if it is not set, goto the slam timer check
78fa  a9f0    LDA #$f0                   ; it is set, set the slam timer counter at 0xF0
78fc  85b4    STA WaitCoinTimer_2        ; and store it
.label CheckSlamTimer:
78fe  a5b4    LDA WaitCoinTimer_2        ; Read the slam timer
7900  f008    BEQ CheckWaitTimer         ; If it is zero, check to see how the coin debouncers are doing
7902  c6b4    DEC WaitCoinTimer_2        ; We're still waiting for slam timer to expire, so
7904  a900    LDA #$00                   ; zero out the debounce counters
7906  95b7    STA CoinDropTimers[0],X    ; for this coin slot
7908  95b3    STA WaitCoinTimer_0,X      ; so that no coins will be accepted
.label CheckWaitTimer:
790a  18      CLC                        ; clear carry flag
790b  b5b3    LDA WaitCoinTimer_0,X      ; is this coin slot in a cool down?
790d  f023    BEQ CheckNextMech          ; yes, goto check the next slot
790f  d6b3    DEC WaitCoinTimer_0,X      ; decrement the cool down timer
7911  d01f    BNE CheckNextMech          ; if it is not yet zero, check the next coin slot
7913  38      SEC                        ; set carry (indicating no coins from this slot)
7914  b01c    BCS CheckNextMech          ; and go check the next coin slot
.label CheckDropTimerVal:
7916  c91b    CMP #$1b                   ;
7918  b009    BCS ResetDropTimer         ;
791a  b5b7    LDA CoinDropTimers[0],X    ;
791c  6920    ADC #$20                   ;
791e  90d1    BCC CheckSlamSw            ;
7920  f001    BEQ ResetDropTimer         ;
7922  18      CLC                        ; clear carry (no coins)
.label ResetDropTimer:
7923  a91f    LDA #$1f                   ;
7925  b0ca    BCS CheckSlamSw            ;
7927  95b7    STA CoinDropTimers[0],X    ; Reset the debounce timer for this slot
7929  b5b3    LDA WaitCoinTimer_0,X      ; and the check if the cool down timer
792b  f001    BEQ SetWaitTimer           ; is zero (which means we haven't been waiting for a coin) so don't set the carry flag
792d  38      SEC                        ; cool down was non-zero, so it is time to give them a credit by setting the carry
.label SetWaitTimer:
792e  a978    LDA #$78                   ; Initialze the cool down timer to 120
7930  95b3    STA WaitCoinTimer_0,X      ; which is about 1/2 a second between coins
.label CheckNextMech:
7932  9004    BCC DoNextCoinMech         ; if carry is not set, there is no coin in this slot, go to the next one
7934  f6b6    INC NumCredits_maybe,X     ; carry was set, so increment the number of credits for this slot!
7936  e6b2    INC ValidCoins             ; and also increment the total number of coins inserted
.label DoNextCoinMech:
7938  ca      DEX                        ; double decrement the index
7939  ca      DEX                        ; since the middle one is ignored
793a  1099    BPL check_coin             ; if it is non-negative, make another loop
793c  e6ba    INC coin_check_counter     ; increment our counter for each time the function is called
793e  a5ba    LDA coin_check_counter     ; Re read it the number of calls
7940  4a      LSR                        ; Shift the bottom bit of the counter into the carry
7941  a5b2    LDA ValidCoins             ; Read the number of valid coins
7943  b00c    BCS EndCoinCheck           ; if this is an odd numbered call, goto EndCoinCheck
7945  f00a    BEQ EndCoinCheck           ; if there are no valid coins, goto EndCoinCheck
7947  c910    CMP #$10                   ; if the valid coins are more than 10
7949  b002    BCS NextValidCoin_maybe    ; ??
794b  69ff    ADC #$ff                   ; ??
.label NextValidCoin_maybe:
794d  69ef    ADC #$ef                   ; ??
794f  85b2    STA ValidCoins             ; Store this result back in ValidCoins
.label EndCoinCheck:
7951  0a      ASL                        ; Shift it left (into the carry)
7952  60      RTS                        ; and return the result to the caller
```

### Credits per coin and other config

There are switches that select how many credits the player receives for each coin, how much
fuel per credit, and the desired language (if the language ROM is installed).

```
.func coin_and_language_config:
796b  ad0328  LDA IO_dsw1_RightCoin      ; Read the coin config switches
796e  2903    AND #$03                   ; Mask out everything but the bottom two bits
7970  aa      TAX                        ; .
7971  bd9b79  LDA CoinMultTbl[0],X       ; Read the number of credits per coin from the table
7974  8599    STA credits_per_coin       ; And store it in the global for later
7976  a200    LDX #$00                   ;
7978  ee0058  INC string_table_language_offset[0] ; If reading the language ROM gives 0xFF,
797b  f006    BEQ set_language                  ; then default to using language 0 == English
797d  ad0228  LDA IO_dsw1_2              ; Read the language configuration switches
7980  2903    AND #$03                   ; Mask out everything but the bottom two bits
7982  aa      TAX                        ; .
.label set_language:
7983  8621    STX language_setting       ; Store the language in the global
7985  38      SEC                        ; Set the carry
7986  ad0128  LDA IO_dsw1_1              ; Load the fuel configuration switches
7989  2a      ROL                        ;
798a  2a      ROL                        ;
798b  2d0028  AND IO_dsw1_0              ;
798e  290f    AND #$0f                   ;
7990  6900    ADC #$00                   ;
7992  c909    CMP #$09                   ;
7994  9002    BCC L7998                  ;
7996  a900    LDA #$00                   ;
.label L7998:
7998  8598    STA fuel_per_coin          ;
799a  60      RTS                        ;

.byte 799b CoinMultTbl 4 ; Coin multiplier table

.func draw_insert_coin_screen:
799f  a20c    LDX #$0c                   ;
79a1  a598    LDA fuel_per_coin          ;
79a3  18      CLC                        ;
79a4  6918    ADC #$18                   ;
79a6  20347a  JSR WriteText_xy           ;
79a9  a917    LDA #$17                   ;
79ab  204f7a  JSR WriteText              ;
79ae  a905    LDA #$05                   ;
79b0  204f7a  JSR WriteText              ;
79b3  a586    LDA FrameCounter           ;
79b5  2920    AND #$20                   ;
79b7  f007    BEQ L79c0                  ;
79b9  a200    LDX #$00                   ;
79bb  a904    LDA #$04                   ;
79bd  4c347a  JMP WriteText_xy           ;
.label L79c0:
79c0  60      RTS                        ;
```
