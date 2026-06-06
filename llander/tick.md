## Game tick

The mainboard is configured with an external timer that is running at 250 Hz and triggers and
[NMI](https://en.wikipedia.org/wiki/Non-maskable_interrupt) that is used to drive the main timing
loop.  When an NMI is received, the 6502 will push some state on the stack, read the pointer
from `0xFFa` and jump to that address


```
:word 7ffa NMI_vector ; NMI vector pointer
:byte 83 thrust_high ; High point for the thrust level (used for smoothing)
:byte 84 thrust_low ; Low point for the thrust level (used for smoothing)
:byte 73 dvg_timer ; Waits for acks from the vector generator
:byte 74 nmi_counter ; Track how many NMI have been received
:byte 87 nmi_counter_250 ; Count every 250 NMI's to create a 1 Hz counter
:byte 8d time_in_seconds ; Increments once per second, triggered by nmi_counter_250 going to zero
:byte 9e score_bcd_maybe 3 ; BCD score value (6 digits, not sure how different from a4)
:byte 9c time_bcd 2 ; BCD mission timer (4 digits, first byte is seconds, second byte is minutes)

; 7------- Exploding?
; -6------ Game playing?
; --5----- Start screen
; ---4---- Attract mode?
:byte 22 game_mode ; Bitmask of the current game mode
```

```
;
;       INTERRUPT OCCURS EVERY 4 MS. [FROM HARDWARE]
;
.func NMI_handler:
7aa8  48      pha                        ; SAVE REGISTERS
7aa9  8a      txa                        ; Move X to A
7aaa  48      pha                        ; Push X to the stack
7aab  98      tya                        ; Move Y to A
7aac  48      pha                        ; Push Y to the stack
7aad  d8      cld                        ; Clear decimal mode
;
; POT CONVERSION ROUTINE
;
7aae  ad002c  lda IO_thrust              ; GET POT READING
7ab1  38      sec                        ; A = POT READING
7ab2  e583    sbc POTMIN                 ; CHK MIN
7ab4  b004    bcs thrust_higher          ; BRANCH > MIN
7ab6  c683    dec POTMIN                 ; LOWER MIN
7ab8  a900    lda #$00                   ; .
.label thrust_higher:
7aba  c584    cmp PTRNGE                 ; CHK RANGE
7abc  9004    bcc thrust_lower           ; BRANCH - WITHIN
7abe  e684    inc PTRNGE                 ; INCREASE RANGE
7ac0  a584    lda PTRNGE                 ;
.label thrust_lower:
7ac2  aa      tax                        ;
7ac3  38      sec                        ;
7ac4  e582    sbc POTVAL                 ;
7ac6  900a    bcc L7ad2                  ; CHECK -3 IF BORROW
7ac8  4a      lsr                        ; ELSE CHECK +3
7ac9  4a      lsr                        ;
7aca  f00a    beq nmtime                 ; NO CHANGE
.label L7acc:
7acc  8682    stx POTVAL                 ; UPDATE POT VALUE
7ace  e685    inc POTUSE                 ;
7ad0  d004    bne nmtime                 ; ALWAYS
.label L7ad2:
7ad2  6903    adc #$03                   ; CARRY IS CLR
7ad4  30f6    bmi L7acc                  ; BEYOND NOISE
.label nmtime:
7ad6  e674    inc INTCNT                 ; INCREMENT INT (4 MS) COUNTER
7ad8  a573    lda INTFLG                 ; CHK FRAME(S)
7ada  c903    cmp #$03                   ;
7adc  b00d    bcs wait_for_watchdog      ; 60 MS W/O FRAME
7ade  8d0034  sta IO_watchdog            ; CLR WATCHDOG
7ae1  a500    lda SOFT_0                 ; CHK RAM 'WATCH' LOCATIONS
7ae3  45c1    eor SOFT.1                 ;
7ae5  45c2    eor SOFT.1_high            ;
7ae7  c985    cmp #$85                   ; $85 = SOFTWD
7ae9  f003    beq nmi_check_coins        ; BRANK IF OK
.label wait_for_watchdog:
7aeb  4ceb7a  jmp wait_for_watchdog      ; WAIT FOR WATCHDOG TO RESTART
.label nmi_check_coins:
7aee  20d378  jsr CheckCoinsInserted     ; COIN ROUTINE
7af1  9006    bcc nmi_no_coins           ;
7af3  a220    ldx #$20                   ; SET COIN COUNTER
7af5  a9ff    lda #$ff                   ;
7af7  d004    bne nmi_update_lights      ; ALWAYS BRANCH
.label nmi_no_coins:
7af9  a9df    lda #$df                   ; $DF = NCNCNTR
7afb  a200    ldx #$00                   ;
.label nmi_update_lights:
7afd  205f79  jsr io_lamps_set           ; SET COIN COUNTER AS APPROPRIATE
7b00  2422    bit GAMODE                 ;
7b02  502f    bvc not_a_second           ; BRANCH - NOT PLAY
7b04  c687    dec TIMVAL                 ; COUNT TIME IN PLAY MODE
7b06  d02b    bne not_a_second           ;
7b08  a9fa    lda #$fa                   ; $FA = 250 = SECCNT
7b0a  8587    sta TIMVAL                 ;
7b0c  e68d    inc TIMER                  ; COUNT GAME SECONDS
7b0e  f8      sed                        ;
7b0f  18      clc                        ; Clear the carry for the addition
7b10  a200    ldx #$00                   ; for x = 0, 1, 2
7b12  a002    ldy #$02                   ; (although y is used for the counter)
7b14  a908    lda #$08                   ; add 8 to the score
.label nmi_score_bcd_update:
7b16  759e    adc FLMIN[0],X             ; add `A` to the bcd score[X]
7b18  959e    sta FLMIN[0],X             ; and store it back in bcd store[X]
7b1a  a900    lda #$00                   ; zero A
7b1c  e8      inx                        ; x++
7b1d  88      dey                        ; y--
7b1e  10f6    bpl nmi_score_bcd_update   ; if y > 0 do another digit
.label nmi_time_bcd_update:
7b20  a59c    lda GMTIME[0]              ; GAME PLAY TIME
7b22  18      clc                        ; clear the carry
7b23  6901    adc #$01                   ; add one to the seconds timer
7b25  c960    cmp #$60                   ; if it has not reached 60
7b27  9002    bcc nmi_seconds_no_overflow ; then goto no overflow
7b29  a900    lda #$00                   ; otherwise zero the seconds
.label nmi_seconds_no_overflow:
7b2b  859c    sta GMTIME[0]              ;
7b2d  a59d    lda GMTIME[1]              ;
7b2f  6900    adc #$00                   ; ADD 1 (IF CARRY SET)
7b31  859d    sta GMTIME[1]              ;
.label not_a_second:
7b33  d8      cld                        ; CLEAR DECIMAL MODE
7b34  a522    lda GAMODE                 ; MODULATE GAME TYPE LAMPS
7b36  d00e    bne L7b46                  ; IN ATTRACT
7b38  a574    lda INTCNT                 ; 50 % DUTY CYCLE
7b3a  a21f    ldx #$1f                   ; ASSUME SET ON
7b3c  4a      lsr                        ;
7b3d  9002    bcc L7b41                  ; SET ON
7b3f  a210    ldx #$10                   ; ELSE - TURN OFF
.label L7b41:
7b41  a900    lda #$00                   ;
7b43  205f79  jsr io_lamps_set           ; SET LEDS
.label L7b46:
7b46  c68a    dec VGCOUNT                ; CHECK FOR EOF [END OF FRAME]
7b48  d006    bne nmexit                 ;
7b4a  a906    lda #$06                   ; 6 = FRMECNT
7b4c  858a    sta VGCOUNT                ; RESET FRAME COUNT
7b4e  e673    inc INTFLG                 ; FRAME SYNC [EVERY 24MS]
.label nmexit:
7b50  68      pla                        ; RESTORE REGISTERS
7b51  a8      tay                        ;
7b52  68      pla                        ;
7b53  aa      tax                        ;
7b54  68      pla                        ;
7b55  40      rti                        ;
```
