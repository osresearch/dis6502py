from collections import namedtuple
from enum import IntEnum

class OpcodeFlags(IntEnum):
	# where control goes
	NORM = (1 << 0)
	JUMP = (1 << 1)
	FORK = (1 << 2)
	STOP = (1 << 3)
	CTLMASK = NORM | JUMP | FORK | STOP

	CMOS = (1 << 4)

	# instruction format
	IMM = (1 << 5)
	ABS = (1 << 6)
	ACC = (1 << 7)
	IMP = (1 << 8)
	INX = (1 << 9)
	INY = (1 << 10)
	ZPX = (1 << 11)
	ABX = (1 << 12)
	ABY = (1 << 13)
	REL = (1 << 14)
	IND = (1 << 15)
	ZPY = (1 << 16)
	ZPG = (1 << 17)
	ZPI = (1 << 18)
	ILL = (1 << 19)

	ADRMASK = IMM|ABS|ACC|IMP|INX|INY|ZPX|ABX|ABY|REL|IND|ZPY|ZPG|ZPI|ILL

Opcode = namedtuple("Opcode", ['name', 'length', 'flags'])

opcode_table = [
Opcode("BRK", 1, OpcodeFlags.IMP | OpcodeFlags.STOP), #     /* 00 */    
Opcode("ORA", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* 01 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 02 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 03 */    
Opcode("TSB", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 04 */    
Opcode("ORA", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 05 */    
Opcode("ASL", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 06 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 07 */    
Opcode("PHP", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 08 */    
Opcode("ORA", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* 09 */    
Opcode("ASL", 1, OpcodeFlags.ACC | OpcodeFlags.NORM), #     /* 0a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 0b */    
Opcode("TSB", 3, OpcodeFlags.ABS | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 0c */    
Opcode("ORA", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 0d */    
Opcode("ASL", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 0e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 0f */    
Opcode("BPL", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* 10 */    
Opcode("ORA", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* 11 */    
Opcode("ORA", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 12 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 13 */    
Opcode("TRB", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 14 */    
Opcode("ORA", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 15 */    
Opcode("ASL", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 16 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 17 */    
Opcode("CLC", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 18 */    
Opcode("ORA", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* 19 */    
Opcode("INC", 1, OpcodeFlags.ACC | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 1a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 1b */    
Opcode("TRB", 3, OpcodeFlags.ABS | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 1c */    
Opcode("ORA", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 1d */    
Opcode("ASL", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 1e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 1f */    
Opcode("JSR", 3, OpcodeFlags.ABS | OpcodeFlags.FORK), #     /* 20 */    
Opcode("AND", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* 21 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 22 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 23 */    
Opcode("BIT", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 24 */    
Opcode("AND", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 25 */    
Opcode("ROL", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 26 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 27 */    
Opcode("PLP", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 28 */    
Opcode("AND", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* 29 */    
Opcode("ROL", 1, OpcodeFlags.ACC | OpcodeFlags.NORM), #     /* 2a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 2b */    
Opcode("BIT", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 2c */    
Opcode("AND", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 2d */    
Opcode("ROL", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 2e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 2f */    
Opcode("BMI", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* 30 */    
Opcode("AND", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* 31 */    
Opcode("AND", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 32 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 33 */    
Opcode("BIT", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 34 */    
Opcode("AND", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 35 */    
Opcode("ROL", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 36 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 37 */    
Opcode("SEC", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 38 */    
Opcode("AND", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* 39 */    
Opcode("DEC", 1, OpcodeFlags.ACC | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 3a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 3b */    
Opcode("BIT", 3, OpcodeFlags.ABX | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 3c */    
Opcode("AND", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 3d */    
Opcode("ROL", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 3e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 3f */    
Opcode("RTI", 1, OpcodeFlags.IMP | OpcodeFlags.STOP), #     /* 40 */    
Opcode("EOR", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* 41 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 42 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 43 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 44 */    
Opcode("EOR", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 45 */    
Opcode("LSR", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 46 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 47 */    
Opcode("PHA", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 48 */    
Opcode("EOR", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* 49 */    
Opcode("LSR", 1, OpcodeFlags.ACC | OpcodeFlags.NORM), #     /* 4a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 4b */    
Opcode("JMP", 3, OpcodeFlags.ABS | OpcodeFlags.JUMP), #     /* 4c */    
Opcode("EOR", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 4d */    
Opcode("LSR", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 4e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 4f */    
Opcode("BVC", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* 50 */    
Opcode("EOR", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* 51 */    
Opcode("EOR", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 52 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 53 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 54 */    
Opcode("EOR", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 55 */    
Opcode("LSR", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 56 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 57 */    
Opcode("CLI", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 58 */    
Opcode("EOR", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* 59 */    
Opcode("PHY", 1, OpcodeFlags.IMP | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 5a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 5b */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 5c */    
Opcode("EOR", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 5d */    
Opcode("LSR", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 5e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 5f */    
Opcode("RTS", 1, OpcodeFlags.IMP | OpcodeFlags.STOP), #     /* 60 */    
Opcode("ADC", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* 61 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 62 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 63 */    
Opcode("STZ", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 64 */    
Opcode("ADC", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 65 */    
Opcode("ROR", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 66 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 67 */    
Opcode("PLA", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 68 */    
Opcode("ADC", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* 69 */    
Opcode("ROR", 1, OpcodeFlags.ACC | OpcodeFlags.NORM), #     /* 6a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 6b */    
Opcode("JMP", 3, OpcodeFlags.IND | OpcodeFlags.STOP), #     /* 6c */    
Opcode("ADC", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 6d */    
Opcode("ROR", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 6e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 6f */    
Opcode("BVS", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* 70 */    
Opcode("ADC", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* 71 */    
Opcode("ADC", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 72 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 73 */    
Opcode("STZ", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 74 */    
Opcode("ADC", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 75 */    
Opcode("ROR", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 76 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 77 */    
Opcode("SEI", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 78 */    
Opcode("ADC", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* 79 */    
Opcode("PLY", 1, OpcodeFlags.IMP | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 7a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 7b */    
Opcode("JMP", 3, OpcodeFlags.INX | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 7c */    
Opcode("ADC", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 7d */    
Opcode("ROR", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 7e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 7f */    
Opcode("BRA", 2, OpcodeFlags.REL | OpcodeFlags.FORK | OpcodeFlags.CMOS), #     /* 80 */    
Opcode("STA", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* 81 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 82 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 83 */    
Opcode("STY", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 84 */    
Opcode("STA", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 85 */    
Opcode("STX", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* 86 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 87 */    
Opcode("DEY", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 88 */    
Opcode("BIT", 2, OpcodeFlags.IMM | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 89 */    
Opcode("TXA", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 8a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 8b */    
Opcode("STY", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 8c */    
Opcode("STA", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 8d */    
Opcode("STX", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 8e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 8f */    
Opcode("BCC", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* 90 */    
Opcode("STA", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* 91 */    
Opcode("STA", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* 92 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 93 */    
Opcode("STY", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 94 */    
Opcode("STA", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* 95 */    
Opcode("STX", 2, OpcodeFlags.ZPY | OpcodeFlags.NORM), #     /* 96 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 97 */    
Opcode("TYA", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 98 */    
Opcode("STA", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* 99 */    
Opcode("TXS", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* 9a */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 9b */    
Opcode("STZ", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* 9c */    
Opcode("STA", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 9d */    
Opcode("STZ", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* 9e */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* 0f */    
Opcode("LDY", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* a0 */    
Opcode("LDA", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* a1 */    
Opcode("LDX", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* a2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* a3 */    
Opcode("LDY", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* a4 */    
Opcode("LDA", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* a5 */    
Opcode("LDX", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* a6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* a7 */    
Opcode("TAY", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* a8 */    
Opcode("LDA", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* a9 */    
Opcode("TAX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* aa */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* ab */    
Opcode("LDY", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ac */    
Opcode("LDA", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ad */    
Opcode("LDX", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ae */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* af */    
Opcode("BCS", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* b0 */    
Opcode("LDA", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* b1 */    
Opcode("LDA", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* b2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* b3 */    
Opcode("LDY", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* b4 */    
Opcode("LDA", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* b5 */    
Opcode("LDX", 2, OpcodeFlags.ZPY | OpcodeFlags.NORM), #     /* b6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* b7 */    
Opcode("CLV", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* b8 */    
Opcode("LDA", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* b9 */    
Opcode("TSX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* ba */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* bb */    
Opcode("LDY", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* bc */    
Opcode("LDA", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* bd */    
Opcode("LDX", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* be */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* bf */    
Opcode("CPY", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* c0 */    
Opcode("CMP", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* c1 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* c2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* c3 */    
Opcode("CPY", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* c4 */    
Opcode("CMP", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* c5 */    
Opcode("DEC", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* c6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* c7 */    
Opcode("INY", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* c8 */    
Opcode("CMP", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* c9 */    
Opcode("DEX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* ca */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* cb */    
Opcode("CPY", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* cc */    
Opcode("CMP", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* cd */    
Opcode("DEC", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ce */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* cf */    
Opcode("BNE", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* d0 */    
Opcode("CMP", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* d1 */    
Opcode("CMP", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* d2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* d3 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* d4 */    
Opcode("CMP", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* d5 */    
Opcode("DEC", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* d6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* d7 */    
Opcode("CLD", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* d8 */    
Opcode("CMP", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* d9 */    
Opcode("PHX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* da */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* db */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* dc */    
Opcode("CMP", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* dd */    
Opcode("DEC", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* de */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* df */    
Opcode("CPX", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* e0 */    
Opcode("SBC", 2, OpcodeFlags.INX | OpcodeFlags.NORM), #     /* e1 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* e2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* e3 */    
Opcode("CPX", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* e4 */    
Opcode("SBC", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* e5 */    
Opcode("INC", 2, OpcodeFlags.ZPG | OpcodeFlags.NORM), #     /* e6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* e7 */    
Opcode("INX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* e8 */    
Opcode("SBC", 2, OpcodeFlags.IMM | OpcodeFlags.NORM), #     /* e9 */    
Opcode("NOP", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* ea */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* eb */    
Opcode("CPX", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ec */    
Opcode("SBC", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ed */    
Opcode("INC", 3, OpcodeFlags.ABS | OpcodeFlags.NORM), #     /* ee */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* ef */    
Opcode("BEQ", 2, OpcodeFlags.REL | OpcodeFlags.FORK), #     /* f0 */    
Opcode("SBC", 2, OpcodeFlags.INY | OpcodeFlags.NORM), #     /* f1 */    
Opcode("SBC", 2, OpcodeFlags.ZPI | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* f2 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* f3 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* f4 */    
Opcode("SBC", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* f5 */    
Opcode("INC", 2, OpcodeFlags.ZPX | OpcodeFlags.NORM), #     /* f6 */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* f7 */    
Opcode("SED", 1, OpcodeFlags.IMP | OpcodeFlags.NORM), #     /* f8 */    
Opcode("SBC", 3, OpcodeFlags.ABY | OpcodeFlags.NORM), #     /* f9 */    
Opcode("PLX", 1, OpcodeFlags.IMP | OpcodeFlags.NORM | OpcodeFlags.CMOS), #     /* fa */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* fb */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* fc */    
Opcode("SBC", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* fd */    
Opcode("INC", 3, OpcodeFlags.ABX | OpcodeFlags.NORM), #     /* fe */    
Opcode("???", 1, OpcodeFlags.ILL | OpcodeFlags.NORM), #     /* ff */    
]
