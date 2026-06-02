all: index.html

index.html: FORCE
	../annotate6502.py > $@ \
		header.dis \
		rotation.dis \
		zeropage.dis \
		footer.dis \

llander.asm: FORCE
	../dis6502.py > $@ llander-0x4800.bin 0x4800

FORCE:
