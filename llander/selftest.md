## Reset vector

The reset vector is stored at `0xFFFC` and points to the function that should be called when the 6502 comes out of reset.
This is bare metal, so there is no operating system or other services.  This code is responsible for initializing all of
the hardware and RAM, and then jumping into the game or self test routine.

```
; First function called when powering up
.func RESET:
7b84  a2ff    LDX #$ff                   ; Set the initial stack pointer
7b86  9a      TXS                        ; to the stop of the stack page (`0x1FF`)
7b87  d8      CLD                        ; Ensure binary mode
7b88  a900    LDA #$00                   ; Store 0x00
7b8a  8d003c  STA IO_audio_latch         ; to the audio output to stop any noises
7b8d  aa      TAX                        ; For x = 0 ... 256:
.label bzero_zeropage:
7b8e  9500    STA state_00,X             ; RAM[X] = 0
7b90  e8      INX                        ; X++
7b91  d0fb    BNE bzero_zeropage         ; if X != 0 (hasn't yet overflowed) keep zeroing
7b93  ad0020  LDA IO_in0                 ; Read the IO peripheral
7b96  4a      LSR                        ; shift it right twice
7b97  4a      LSR                        ; .
7b98  b003    BCS normal_startup         ; If bit 1, the diagonstic test switch is pressed
7b9a  4cb97b  JMP DoSelfTest             ; then do the self test routines
.label normal_startup:
7b9d  a985    LDA #$85                   ; Normal code goes here..
7b9f  8500    STA state_00               ; Store 0x85 in the state variables?
7ba1  85c1    STA state_c1               ; .
7ba3  85c2    STA state_c2               ; .
7ba5  a9ff    LDA #$ff                   ; Initialize the high reading for thrust lever
7ba7  8583    STA thrust_high            ; at 0xff
7ba9  a906    LDA #$06                   ; Start the 6 NMI counter
7bab  858a    STA delay_6                ; at 6.
7bad  a902    LDA #$02                   ; store 0x02 in
7baf  859a    STA Z9a                    ; some variables I don't know yet
7bb1  859b    STA Z9b                    ; what are these?
7bb3  8d0034  STA IO_watchdog            ; Pet the watchdog
7bb6  4c0160  JMP InitGame               ; And jump to the game initialization routine...
```


## Self Test

This section isn't as heavily documented.  I haven't really walked through all of the code yet.


```
.func io_in0_diagstep:
7e95  2c0020  BIT IO_in0                 ; Read the @IO_in0 peripheral
7e98  3003    BMI diagstep_pressed       ; If bit 7 is set, the tech is pressing the diag button
7e9a  0626    ASL diag_step_debounce     ; Shift the debounce counter to the left
.label diagstep_done:
7e9c  60      RTS                        ; Return to the caller
.label diagstep_pressed:
7e9d  a920    LDA #$20                   ; Reset the debounce counter to `0x20`
7e9f  8526    STA diag_step_debounce     ; which will take three cycles to clear
7ea1  18      CLC                        ; clear carry
7ea2  90f8    BCC diagstep_done          ; always taken
```

```
.byte 26 diag_step_debounce ; Counter for the single step button to ensure that it isn't bouncing
```


