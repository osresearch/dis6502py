.title Lunar Lander 1979 annotated disassembly
.header
# Lunar Lander (1979) disassembly

This is an intro the the disassembly of Atari's 1979 Lunar Lander vector arcade game.
There is also the full listing, [`llander.asm`](llander.html).

.binary llander-0x4800.bin 0x4800
.vector 0x8000
.symbols llander.sym
.trace

## Intro to assembly

It's helpful to have the [instruction set reference](https://www.pagetable.com/c64ref/6502/)
open in another tab to help answer any questions about the semantics of each instruction and the addressing modes.

Some common idioms in the code:

* Arithmetic comparisons and branches (note that the `C` flag seems backwards since it is set if `A` is greater or equal to the comparison value, not the other way around)
<pre>
	LDA variable	; Read the global variable into the A register
	BMI if_neg	; If A < 0, take this branch
	BPL if_pos	; If A >= 0, take this branch
	BEQ if_zero	; If A == 0, take this branch
	CMP #$25	; Compute A - 0x25, but do not store the result.  Set the flags N, Z, and C
	BEQ if_eq	; If A == 0x25, the result was zero, so take this branch
	BNE if_ne	; If A != 0x25, the result was non-zero, so take this one
	BCS if_gt	; If A >= 0x25, take this branch (see note above)
	BCC if_lt	; If A <  0x25, take this branch (see note above)
</pre>

* Bit tests of the two top bits
<pre>
	BIT variable	; Read the global variable, set the N and V status flags (also Z, but it's complicated)
	BMI if_bit7	; If the 7th bit is set, take this branch
	BPL if_not_bit7	; If the 7th bit is not set, take this branch
	BVS if_bit6	; If the 6th bit is set, take this one
	BVC if_not_bit6	; If the 6th bit is not set, take this one
</pre>

* Bit tests of all bits
<pre>
	LDA variable	; Read the global variable into the A register, set the N and Z flags
	BNE if_any_bits	; If any bits are set, take this branch
	BEQ if_no_bits	; If no bits are set, take this branch
</pre>

* 16-bit increment of a global variable
<pre>
	INC variable
	BCC skip_inc
	INC variable_high
skip_in:
	/* more stuff */
</pre>

* 16-bit addition of two global variables `v1` and `v2`, writing into `v2
<pre>
	CLC		; start with the carry flag clear
	LDA v1_low
	ADC v2_low	; if the results overflows, the carry flag will be set
	STA v2_low
	LDA v1_high	; LDA does not change the carry flag
	ADC v2_high	; carry flag added to the high bytes
	STA v2_high
</pre>

* For loops indexing into an array (in this case computing the sum into A)
<pre>
	LDX #$03	; for x = 3, 2, 1, 0 == four passes through the loop
loop:
	CLC		; don't carry
	ADC array,X	; A += array[X]
	DEX		; x--
	BPL loop	; if x >= 0 go again
</pre>
