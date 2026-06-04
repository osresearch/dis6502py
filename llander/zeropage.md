## Zero Page data

On the 6502 global variables are often stored on the "zero page" since it is possible to reference
the bottom 256 bytes of memory with shorter instruction sequences.  It is initialized to zero or
a static value in the @RESET code.

```data
.byte 02 ship_angle_modulo			; Ship angle mod 90 degrees, from 0 - 31.
.byte 42 mult_y					; Argument 1 to multiply
.byte 43 mult_a					; Argument 2 to multiply
.word 44 mult_acc				; Multiply accumulator
.word 66 ship_angle				; 16-bit Ship angle
.word 7d min16_a				; Arg 1 for min16
.word 7f min16_b				; Arg 2 for min16
```
