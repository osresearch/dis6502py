all: llander.sym llander.asm

llander.sym: FORCE
	../annotate6502.py \
		index.md \
		math.md \
		buttons.md \
		rotation.md \
		thrust.md \
		vectors.md \
		strings.md \
		zeropage.md \
		coins.md \
		tick.md \
		selftest.md \
		footer.md \
		> index.html

llander.asm: llander.sym
	../dis6502.py > $@ llander-0x4800.bin llander.sym 0x4800

FORCE:
