all: llander.sym llander.asm

llander.sym: FORCE
	../annotate6502.py \
		header.dis \
		buttons.dis \
		rotation.dis \
		math.dis \
		zeropage.dis \
		footer.dis \
		> index.html

llander.asm: llander.sym
	../dis6502.py > $@ llander-0x4800.bin llander.sym 0x4800

FORCE:
