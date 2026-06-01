#!/usr/bin/env python3
import sys
import os
from collections import deque, namedtuple
from enum import IntFlag, IntEnum, auto
from opcodes import OpcodeFlags, opcode_table


class Flags(IntFlag):
	LOADED = auto()		# Location loaded
	JREF = auto()		# Referenced as a jump/branch dest
	DREF = auto()		# Referenced as data
	SREF = auto()		# Referenced as subroutine dest
	NAMED = auto()		# Has a name
	TDONE = auto()		# has been traced
	ISOP = auto()		# Is a valid instruction opcode
	OFFSET = auto()		# should be printed as an offset

# sign extend an 8-bit value
def sign8(op):
	return (op & 0x7F) - (op & 0x80)

class Dis6502:
	max_addr = 0x10000

	def __init__(self):
		self.ram = bytearray(self.max_addr)
		self.flags = [ Flags(0) for i in range(0,self.max_addr) ]
		self.names = {}
		self.refs = {}
		self.trace_queue = deque()

	def load_binary(self, filename, base_address, vector_address):
		file = open(filename, "rb").read()
		self.ram[base:base + len(file)] = file
		for i in range(base, base+len(file)):
			self.flags[i] |= Flags.LOADED

		reset = vector_address - 4
		irq = vector_address - 2
		nmi = vector_address - 6

		if self.loaded_addr(reset):
			self.start_trace(self.read16(reset), "RESET")
		if self.loaded_addr(irq):
			self.start_trace(self.read16(irq), "IRQ")
		if self.loaded_addr(nmi):
			self.start_trace(self.read16(nmi), "NMI")

	def loaded_addr(self, i):
		return 0 <= i \
		and i < self.max_addr - 1 \
		and self.flags[i] & Flags.LOADED \
		and self.flags[i+1] & Flags.LOADED

	def read8(self, i):
		return self.ram[i]
	def read16(self, i):
		return self.ram[i+1] << 8 | self.ram[i]

	def save_name(self, loc, name):
		if loc in self.names:
			return
		self.flags[loc] |= Flags.NAMED
		self.names[loc] = name

	def name(self, loc, use_default=False):
		if self.flags[loc] & Flags.NAMED:
			return self.names[loc]
		if self.flags[loc] & Flags.SREF:
			return "S%04x" % (loc)
		if self.flags[loc] & Flags.JREF:
			return "L%04x" % (loc)
		if self.flags[loc] & Flags.DREF:
			if loc < 0x100:
				return "Z%02x" % (loc)
			else:
				return "D%04x" % (loc)

		if use_default:
			return "X%04x" % (loc)
		return None

	def save_ref(self, refer, refee):
		if not refee in self.refs:
			self.refs[refee] = []
		self.refs[refee].append(refer)

	def start_trace(self, loc, name):
		print("Trace: %04x %s" % (loc, name))
		self.flags[loc] |= Flags.SREF
		self.save_name(loc, name)
		self.refs[loc] = []
		self.add_trace(loc)

	def add_trace(self, addr):
		if self.flags[addr] & Flags.TDONE:
			return
		self.trace_queue.append(addr)

	def trace_all(self):
		while len(self.trace_queue) > 0:
			self.trace_instr(self.trace_queue.popleft())

	def trace_one_inst(self, addr):
		if self.flags[addr] & Flags.TDONE:
			return None
		self.flags[addr] |= Flags.TDONE
		istart = addr
		opcode = self.ram[addr]
		ip = opcode_table[opcode]

		# illegal instruction, do not process anything further
		if ip.flags & OpcodeFlags.ILL:
			return None

		self.flags[addr] |= Flags.ISOP

		if ip.length == 1:
			operand = 0
		elif ip.length == 2:
			operand = self.read8(addr+1)
			self.flags[addr+1] |= Flags.TDONE
		elif ip.length == 3:
			operand = self.read16(addr+1)
			self.flags[addr+1] |= Flags.TDONE
			self.flags[addr+2] |= Flags.TDONE
		else:
			pass

		addr += ip.length

		# mark data references
		if ip.flags & (OpcodeFlags.IMM | OpcodeFlags.ACC | OpcodeFlags.IMP | OpcodeFlags.REL):
			pass
		elif ip.flags & (OpcodeFlags.ABS | OpcodeFlags.ABX | OpcodeFlags.ABY | OpcodeFlags.IND | OpcodeFlags.INX | OpcodeFlags.INY | OpcodeFlags.ZPG | OpcodeFlags.ZPI | OpcodeFlags.ZPX | OpcodeFlags.ZPY):
			if not (ip.flags & (OpcodeFlags.JUMP | OpcodeFlags.FORK)):
				self.flags[operand] |= Flags.DREF
				self.save_ref(istart, operand)
		else:
			self.crash("unknown addressing mode")

		# Trace the next instruction
		if ip.flags & OpcodeFlags.NORM:
			pass
		elif ip.flags & OpcodeFlags.JUMP:
			self.flags[operand] |= Flags.JREF
			self.save_ref(istart, operand)
			self.trace_queue.append(operand)
		elif ip.flags & OpcodeFlags.FORK:
			if ip.flags & OpcodeFlags.REL:
				operand = sign8(operand) + addr
				self.flags[operand] |= Flags.JREF
			else:
				self.flags[operand] |= Flags.SREF
			self.save_ref(istart, operand)
			self.trace_queue.append(operand)
		elif ip.flags & OpcodeFlags.STOP:
			return None
		else:
			self.crash("unknown control flow in opcode table")

		return addr

	def trace_instr(self, addr):
		while addr is not None:
			addr = self.trace_one_inst(addr)

	def instr_len(self, addr):
		if self.flags[addr] & Flags.ISOP == 0:
			return 1
		ip = opcode_table[self.read8(addr)]
		return ip.length

	def print_bytes(self, addr):
		if self.flags[addr] & Flags.ISOP == 0:
			return (1,'')
		ip = opcode_table[self.read8(addr)]
		return (ip.length,self.ram[addr:addr+ip.length].hex())

	def print_data(self, addr):
		rc = "%02x" % (self.read8(addr))
		for j in range(1,8):
			if self.flags[addr+j] & (Flags.JREF | Flags.SREF | Flags.DREF | Flags.ISOP):
				break
			rc += ",%02x" % (self.read8(addr+j))
		return (j,rc)
	def print_instr(self, addr):
		opcode = self.read8(addr)
		ip = opcode_table[opcode]
		rc = ip.name + "\t"
		if ip.length == 1:
			operand = 0
		elif ip.length == 2:
			operand = self.read8(addr+ 1)
		elif ip.length == 3:
			operand = self.read16(addr + 1)
		addr += ip.length

		if ip.flags & OpcodeFlags.REL:
			operand = sign8(operand) + addr

		if ip.flags & OpcodeFlags.IMM:
			rc += "#$%02x" % (operand)
		elif ip.flags & (OpcodeFlags.ACC | OpcodeFlags.IMP):
			pass
		elif ip.flags & (OpcodeFlags.REL | OpcodeFlags.ABS | OpcodeFlags.ZPG):
			rc += "%s" % (self.name(operand, 1))
		elif ip.flags & (OpcodeFlags.IND | OpcodeFlags.ZPI):
			rc += "(%s)" % (self.name(operand, 1))
		elif ip.flags & (OpcodeFlags.ABX | OpcodeFlags.ZPX):
			rc += "%s,X" % (self.name(operand, 1))
		elif ip.flags & (OpcodeFlags.ABY | OpcodeFlags.ZPY):
			rc += "%s,Y" % (self.name(operand, 1))
		elif ip.flags & (OpcodeFlags.INX):
			rc += "(%s,X)" % (self.name(operand, 1))
		elif ip.flags & (OpcodeFlags.INY):
			rc += "(%s),Y" % (self.name(operand, 1))
		else:
			rc += '???'

		return rc

	def disassemble(self, addr):
		rc = ''
		name = self.name(addr)
		if name:
			if self.flags[addr] & Flags.SREF:
				rc += "\n"
			rc += "\t%s:\n" % (name)

		if self.flags[addr] & Flags.ISOP:
			(len,hexdump) = self.print_bytes(addr)
			rc += "%04x\t%-6s\t" % (addr, hexdump)
			rc += self.print_instr(addr)
		else:
			(len,hexdump) = self.print_data(addr)
			rc += "%04x\t%s" % (addr, hexdump)
		return (len, rc)
	def dumpitout(self):
		addr = 0
		while addr < self.max_addr:
			if self.flags[addr] == 0:
				addr += 1
				continue
			(len,text) = self.disassemble(addr)
			print(text)
			addr += len


	def load_symbols(self, filename):
		with open(filename, "r") as f:
			while (line := f.readline()):
				# address label optional-comment
				words = line.split(maxsplit=2)
				address = int(words[0], 16)
				label = words[1]
				self.save_name(address, label)


if __name__ == "__main__":
	base = 0x4800
	vector = 0x8000

	filename = sys.argv[1]
	dis = Dis6502()
	dis.load_binary(filename, base, vector)

	if len(sys.argv) > 2:
		dis.load_symbols(sys.argv[2])
	dis.trace_all()
	dis.dumpitout()


