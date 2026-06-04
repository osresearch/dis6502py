all: llander.sym llander.asm

llander.sym: FORCE
	../annotate6502.py \
		index.md \
		buttons.md \
		rotation.md \
		math.md \
		zeropage.md \
		footer.md \
		> index.html

llander.asm: llander.sym
	../dis6502.py > $@ llander-0x4800.bin llander.sym 0x4800

FORCE:
