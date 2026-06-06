## Reset vector

The reset vector is stored at `0xFFFC` and points to the function that should be called when the 6502 comes out of reset.
This is bare metal, so there is no operating system or other services.  This code is responsible for initializing all of
the hardware and RAM, and then jumping into the game or self test routine.

```
; First function called when powering up
.func RESET:
7b84  a2ff    ldx #$ff                   ; Set the initial stack pointer
7b86  9a      txs                        ; to the stop of the stack page (`0x1FF`)
7b87  d8      cld                        ; Ensure binary mode
7b88  a900    lda #$00                   ; Store 0x00
7b8a  8d003c  sta IO_audio_latch         ; to the audio output to stop any noises
7b8d  aa      tax                        ; For x = 0 ... 256:
.label bzero_zeropage:
7b8e  9500    sta SOFT_0,X               ; RAM[X] = 0
7b90  e8      inx                        ; X++
7b91  d0fb    bne bzero_zeropage         ; if X != 0 (hasn't yet overflowed) keep zeroing
7b93  ad0020  lda IO_in0                 ; Read the IO peripheral
7b96  4a      lsr                        ; shift it right twice
7b97  4a      lsr                        ; .
7b98  b003    bcs normal_startup         ; If bit 1, the diagonstic test switch is pressed
7b9a  4cb97b  jmp DoSelfTest             ; then do the self test routines
.label normal_startup:
7b9d  a985    lda #$85                   ; Normal code goes here..
7b9f  8500    sta SOFT_0                 ; Store 0x85 in the state variables?
7ba1  85c1    sta SOFT.1                 ; .
7ba3  85c2    sta SOFT.1_high            ; .
7ba5  a9ff    lda #$ff                   ; Initialize the high reading for thrust lever
7ba7  8583    sta POTMIN                 ; at 0xff
7ba9  a906    lda #$06                   ; Start the 6 NMI counter
7bab  858a    sta VGCOUNT                ; at 6.
7bad  a902    lda #$02                   ; store 0x02 in
7baf  859a    sta ARRWX                  ; some variables I don't know yet
7bb1  859b    sta ARRWY                  ; what are these?
7bb3  8d0034  sta IO_watchdog            ; Pet the watchdog
7bb6  4c0160  jmp start                  ; And jump to the game initialization routine...
```


## Self Test

This section isn't as heavily documented.  I haven't really walked through all of the code yet.


```
.func io_in0_diagstep:
7e95  2c0020  bit IO_in0                 ; Read the @IO_in0 peripheral
7e98  3003    bmi diagstep_pressed       ; If bit 7 is set, the tech is pressing the diag button
7e9a  0626    asl diag_step_debounce     ; Shift the debounce counter to the left
.label diagstep_done:
7e9c  60      rts                        ; Return to the caller
.label diagstep_pressed:
7e9d  a920    lda #$20                   ; Reset the debounce counter to `0x20`
7e9f  8526    sta diag_step_debounce     ; which will take three cycles to clear
7ea1  18      clc                        ; clear carry
7ea2  90f8    bcc diagstep_done          ; always taken
```

```
.byte 26 diag_step_debounce ; Counter for the single step button to ensure that it isn't bouncing
```


