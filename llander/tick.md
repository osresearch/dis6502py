## Game tick

The mainboard is configured with an external timer that is running at 250 Hz and triggers and
[NMI](https://en.wikipedia.org/wiki/Non-maskable_interrupt) that is used to drive the main timing
loop.  When an NMI is received, the 6502 will push some state on the stack, read the pointer
from `0xFFa` and jump to that address


```
.word 7ffa NMI_vector ; NMI vector pointer
.byte 83 thrust_high ; High point for the thrust level (used for smoothing)
.byte 84 thrust_low ; Low point for the thrust level (used for smoothing)
.byte 73 dvg_timer ; Waits for acks from the vector generator
.byte 74 nmi_counter ; Track how many NMI have been received
.byte 87 nmi_counter_250 ; Count every 250 NMI's to create a 1 Hz counter
.byte 8d time_in_seconds ; Increments once per second, triggered by @nmi_counter_250 going to zero
.byte 9e score_bcd_maybe 3 ; BCD score value (6 digits, not sure how different from a4)
.byte 9c time_bcd 2 ; BCD mission timer (4 digits, first byte is seconds, second byte is minutes)

; 7------- Exploding?
; -6------ Game playing?
; --5----- Start screen
; ---4---- Attract mode?
.byte 22 game_state_flags ; Bitmask of the current game mode
```

```
; NMI Handler invoked at 250 Hz
; This is the core game tick that invokes all of the ship updates and reads from the player.
; It ensures that the vector drawing system is making progress
; and also pets the watchdog to ensure that the system doesn't reset.
.func NMI_handler:
7aa8  48      PHA                        ; Push the accumulator onto the stack
7aa9  8a      TXA                        ; Move X to A
7aaa  48      PHA                        ; Push X to the stack
7aab  98      TYA                        ; Move Y to A
7aac  48      PHA                        ; Push Y to the stack
7aad  d8      CLD                        ; Clear decimal mode
.label nmi_thrust_process:
7aae  ad002c  LDA IO_thrust              ; Read the thrust potentiometer for low pass smoothing
7ab1  38      SEC                        ; Clear carry for SBC
7ab2  e583    SBC thrust_high            ; if IO_thrust > thrust_high
7ab4  b004    BCS thrust_higher          ; skip decrement
7ab6  c683    DEC thrust_high            ; decay @thrust_high towards the reading
7ab8  a900    LDA #$00                   ; force skip increment
.label thrust_higher:
7aba  c584    CMP thrust_low             ; if IO_thrust < thrust_low
7abc  9004    BCC thrust_lower           ;  skip increment
7abe  e684    INC thrust_low             ; Increase @thrust_low towards the reading
7ac0  a584    LDA thrust_low             ;
.label thrust_lower:
7ac2  aa      TAX                        ;
7ac3  38      SEC                        ; Clear carry for SBC
7ac4  e582    SBC thrust_delta_last_raw  ;
7ac6  900a    BCC L7ad2                  ;
7ac8  4a      LSR                        ;
7ac9  4a      LSR                        ;
7aca  f00a    BEQ nmi_check_dvg          ;
.label L7acc:
7acc  8682    STX thrust_delta_last_raw  ;
7ace  e685    INC thrust_something_counter ;
7ad0  d004    BNE nmi_check_dvg          ;
.label L7ad2:
7ad2  6903    ADC #$03                   ;
7ad4  30f6    BMI L7acc                  ;
.label nmi_check_dvg:
7ad6  e674    INC nmi_counter            ; Track the number of NMI's received
7ad8  a573    LDA dvg_timer              ; If the vector generator has been stalled
7ada  c903    CMP #$03                   ; for more than 4 NMI's
7adc  b00d    BCS wait_for_watchdog      ; then just wait for the watchdog
7ade  8d0034  STA IO_watchdog            ; else pet the watchdog
7ae1  a500    LDA state_00               ;
7ae3  45c1    EOR state_c1               ;
7ae5  45c2    EOR state_c2               ;
7ae7  c985    CMP #$85                   ;
7ae9  f003    BEQ nmi_check_coins        ;
.label wait_for_watchdog:
7aeb  4ceb7a  JMP wait_for_watchdog      ; Infinite loop, waiting for the watchdog to bark
.label nmi_check_coins:
7aee  20d378  JSR CheckCoinsInserted     ; Has the player inserted any new coins?
7af1  9006    BCC nmi_no_coins           ; Carry clear == no coins, goto
7af3  a220    LDX #$20                   ; set coin counter output lamp
7af5  a9ff    LDA #$ff                   ; keep all the other lamps the same
7af7  d004    BNE nmi_update_lights      ; (always taken)
.label nmi_no_coins:
7af9  a9df    LDA #$df                   ; unset coin counter output lamp
7afb  a200    LDX #$00                   ; also reset the rest of them
.label nmi_update_lights:
7afd  205f79  JSR io_lamps_set           ; update the lamps based on if a coin was received
7b00  2422    BIT game_state_flags       ; Is there a game in progress?
7b02  502f    BVC not_a_second           ; If bit 6 is not set (no game playing) do not update the per second timer
7b04  c687    DEC nmi_counter_250        ; Decrement the 250 divider
7b06  d02b    BNE not_a_second           ; if it is non zero, skip ahead
7b08  a9fa    LDA #$fa                   ; Reset the divider with 250 (0xFA)
7b0a  8587    STA nmi_counter_250        ; and store it in the global
7b0c  e68d    INC time_in_seconds        ; Increment our once-per-second counter
7b0e  f8      SED                        ; Enable decimal mode to increment score
7b0f  18      CLC                        ; Clear the carry for the addition
7b10  a200    LDX #$00                   ; for x = 0, 1, 2
7b12  a002    LDY #$02                   ; (although y is used for the counter)
7b14  a908    LDA #$08                   ; add 8 to the score
.label nmi_score_bcd_update:
7b16  759e    ADC score_bcd_maybe[0],X   ; add `A` to the bcd score[X]
7b18  959e    STA score_bcd_maybe[0],X   ; and store it back in bcd store[X]
7b1a  a900    LDA #$00                   ; zero A
7b1c  e8      INX                        ; x++
7b1d  88      DEY                        ; y--
7b1e  10f6    BPL nmi_score_bcd_update   ; if y > 0 do another digit
.label nmi_time_bcd_update:
7b20  a59c    LDA time_bcd[0]            ; get the first digit of the BCD timer
7b22  18      CLC                        ; clear the carry
7b23  6901    ADC #$01                   ; add one to the seconds timer
7b25  c960    CMP #$60                   ; if it has not reached 60
7b27  9002    BCC nmi_time_seconds_no_overflow ; then goto no overflow
7b29  a900    LDA #$00                   ; otherwise zero the seconds
.label nmi_time_seconds_no_overflow:
7b2b  859c    STA time_bcd[0]            ; and store it back in the LSB
7b2d  a59d    LDA time_bcd[1]            ; load the minutes of the timer
7b2f  6900    ADC #$00                   ; and if the seconds overflowed 60, add it to the minutes
7b31  859d    STA time_bcd[1]            ; store it back in the MSB
.label not_a_second:
7b33  d8      CLD                        ; exit decimal mode (whew)
7b34  a522    LDA game_state_flags       ; read the current game state
7b36  d00e    BNE L7b46                  ; if any bits are set,
7b38  a574    LDA nmi_counter            ; game state is zero, so no game right now
7b3a  a21f    LDX #$1f                   ; let's make the lights flash (1F == *all the lamps*)
7b3c  4a      LSR                        ; shift the bottom bit from the nmi counter into carry
7b3d  9002    BCC L7b41                  ; every other NMI turn on all the lamps
7b3f  a210    LDX #$10                   ; and every odd one turn off all the lamps
.label L7b41:
7b41  a900    LDA #$00                   ; don't keep any of the old bits
7b43  205f79  JSR io_lamps_set           ; and toggle the lamps
.label L7b46:
7b46  c68a    DEC delay_6                ; divide the NMI counter by 6 for the vector generator timer
7b48  d006    BNE nmi_rti                ; if it is not zero, just return
7b4a  a906    LDA #$06                   ; reset the dvg divisor
7b4c  858a    STA delay_6                ; store it back in the delay counter
7b4e  e673    INC dvg_timer              ; and increment the vector generator timer
.label nmi_rti:
7b50  68      PLA                        ; Pop the CPU state from the stack
7b51  a8      TAY                        ; -> Y
7b52  68      PLA                        ; and
7b53  aa      TAX                        ; -> X
7b54  68      PLA                        ; -> A
7b55  40      RTI                        ; Return from interrupt
```
