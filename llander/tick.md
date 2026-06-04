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
7af1  9006    BCC L7af9                  ;
7af3  a220    LDX #$20                   ;
7af5  a9ff    LDA #$ff                   ;
7af7  d004    BNE L7afd                  ;
.label L7af9:
7af9  a9df    LDA #$df                   ;
7afb  a200    LDX #$00                   ;
.label L7afd:
7afd  205f79  JSR io_outlatch_set        ;
7b00  2422    BIT game_state_flags       ;
7b02  502f    BVC L7b33                  ;
7b04  c687    DEC nmi_counter_250        ;
7b06  d02b    BNE L7b33                  ;
7b08  a9fa    LDA #$fa                   ;
7b0a  8587    STA nmi_counter_250        ;
7b0c  e68d    INC time_in_seconds        ;
7b0e  f8      SED                        ;
7b0f  18      CLC                        ;
7b10  a200    LDX #$00                   ;
7b12  a002    LDY #$02                   ;
7b14  a908    LDA #$08                   ;
.label L7b16:
7b16  759e    ADC score_bcd_maybe,X      ;
7b18  959e    STA score_bcd_maybe,X      ;
7b1a  a900    LDA #$00                   ;
7b1c  e8      INX                        ;
7b1d  88      DEY                        ;
7b1e  10f6    BPL L7b16                  ;
7b20  a59c    LDA time_bcd_maybe         ;
7b22  18      CLC                        ;
7b23  6901    ADC #$01                   ;
7b25  c960    CMP #$60                   ;
7b27  9002    BCC L7b2b                  ;
7b29  a900    LDA #$00                   ;
.label L7b2b:
7b2b  859c    STA time_bcd_maybe         ;
7b2d  a59d    LDA Z9d                    ;
7b2f  6900    ADC #$00                   ;
7b31  859d    STA Z9d                    ;
.label L7b33:
7b33  d8      CLD                        ;
7b34  a522    LDA game_state_flags       ;
7b36  d00e    BNE L7b46                  ;
7b38  a574    LDA nmi_counter            ;
7b3a  a21f    LDX #$1f                   ;
7b3c  4a      LSR                        ;
7b3d  9002    BCC L7b41                  ;
7b3f  a210    LDX #$10                   ;
.label L7b41:
7b41  a900    LDA #$00                   ;
7b43  205f79  JSR io_outlatch_set        ;
.label L7b46:
7b46  c68a    DEC delay_6                ;
7b48  d006    BNE nmi_rti                ;
7b4a  a906    LDA #$06                   ;
7b4c  858a    STA delay_6                ;
7b4e  e673    INC dvg_timer              ;
.label nmi_rti:
7b50  68      PLA                        ; Pop the CPU state from the stack
7b51  a8      TAY                        ; -> Y
7b52  68      PLA                        ; and
7b53  aa      TAX                        ; -> X
7b54  68      PLA                        ; -> A
7b55  40      RTI                        ; Return from interrupt
```
