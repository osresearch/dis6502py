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
	WORD_LOW = auto()	# Data is 16-bits wide, low byte
	WORD_HIGH = auto()	# Data is 16-bits wide, high byte
	ARRAY = auto()		# Data is part of an array
	PTR = auto()		# Data is a 16-bit pointer (also a word)

# sign extend an 8-bit value
def sign8(op):
	return (op & 0x7F) - (op & 0x80)

class Dis6502:
	max_addr = 0x10000

	def __init__(self):
		self.ram = bytearray(self.max_addr)
		self.flags = [ Flags(0) for i in range(0,self.max_addr) ]
		self.names = {}
		self.arrays = {}
		self.all_names = {}
		self.refs = {}
		self.comments = {}
		self.trace_queue = deque()

	def load_binary(self, filename, base):
		file = open(filename, "rb").read()
		self.ram[base:base + len(file)] = file
		for i in range(base, base+len(file)):
			self.flags[i] |= Flags.LOADED

	def vector(self, vector_address):
		reset = vector_address - 4
		irq = vector_address - 2
		nmi = vector_address - 6

		if self.loaded_addr(reset):
			self.start_trace(self.read16(reset), "RESET_handler")
		if self.loaded_addr(irq):
			self.start_trace(self.read16(irq), "IRQ_handler")
		if self.loaded_addr(nmi):
			self.start_trace(self.read16(nmi), "NMI_handler")

	def loaded_addr(self, i):
		return 0 <= i \
		and i < self.max_addr - 1 \
		and self.flags[i] & Flags.LOADED \
		and self.flags[i+1] & Flags.LOADED
	def is_op(self, i):
		return 0 <= i \
		and i < self.max_addr - 1 \
		and (self.flags[i] & Flags.ISOP) != 0

	def read8(self, i):
		return self.ram[i]
	def read16(self, i):
		return self.ram[i+1] << 8 | self.ram[i]

	# Returns true if the name was saved, false if it already exists
	def save_name(self, addr, name, data_type=None, array_size=None, force=False):
		# force a rename
		if old_name := self.names.get(addr) and not force:
			if old_name != name:
				print("%04x: Not renaming to %s from %s" % (addr, name, old_name), file=sys.stderr)
			return False
		self.flags[addr] |= Flags.NAMED
		self.names[addr] = name

		old_data = self.all_names.get(name)
		if not old_data:
			self.all_names[name] = [addr, data_type, array_size]
			return True

		if old_data[0] != addr \
		or (old_data[1] and old_data[1] != data_type) \
		or old_data[2] != array_size:
			raise RuntimeError(f"Refusing to redefine {name}. Delete from symbol table" + str(old_data))

		# already exists, do not recreate
		return False

	def name(self, addr, use_default=False):
		flags = self.flags[addr]
		if flags & Flags.ARRAY:
			# need to find the array this belongs to
			# this is higher priority than NAMED so that
			# the 0th index will be correctly shown
			return self.name_array(addr)
		if flags & Flags.NAMED:
			return self.names[addr]
		if flags & Flags.WORD_HIGH:
			return self.names[addr-1] + "_high"
		if flags & Flags.SREF:
			return "S%04x" % (addr)
		if flags & Flags.JREF:
			return "L%04x" % (addr)
		if flags & Flags.DREF:
			if addr < 0x100:
				return "Z%02x" % (addr)
			else:
				return "D%04x" % (addr)

		if use_default:
			return "X%04x" % (addr)
		return None

	def name_relative(self, addr):
		for i in range(addr, addr-1024, -1):
			if i < 0 or self.flags[i] == 0:
				break
			if self.flags[i] & Flags.SREF:
				return "%s+%x" % (self.name(i), addr - i)
		return "%04x" % (addr)

	def array_ref(self, addr):
		array_start = self.arrays[addr]
		if array_start & 0x10000:
			array_start = addr
		array_index = addr - array_start
		return (array_start,array_index)
		
	def name_array(self, addr):
		# arrays always have names
		(array_start,array_index) = self.array_ref(addr)
		name = self.names[array_start]

		flags = self.flags[addr]
		if flags & Flags.WORD_HIGH:
			name += "_high"
		if flags & (Flags.WORD_LOW | Flags.WORD_HIGH):
			array_index //= 2

#		if array_index == 0:
#			return name
#		else:
		return f"{name}[{array_index}]"
		

	def save_ref(self, refer, refee):
		if not refee in self.refs:
			self.refs[refee] = []
		self.refs[refee].append(refer)

		# check for an array reference
		if not self.flags[refee] & Flags.ARRAY:
			return
		(refee,array_index) = self.array_ref(refee)
		if array_index == 0:
			return
		if not refee in self.refs:
			self.refs[refee] = []
		self.refs[refee].append(refer)

	def start_trace(self, loc, name):
		print("Trace: %04x %s" % (loc, name), file=sys.stderr)
		self.flags[loc] |= Flags.SREF
		self.save_name(loc, name, "func", force=True)
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
		# special case that we will always decode a BRK
		opcode = self.ram[addr]
		if self.flags[addr] & Flags.TDONE:
#			if opcode == 0 and self.flags[addr] & Flags.ISOP:
#				pass
#			else:
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
		if not self.is_op(addr):
			return 1
		ip = opcode_table[self.read8(addr)]
		return ip.length

	def print_bytes(self, addr):
		if not self.is_op(addr):
			return (1,'')
		ip = opcode_table[self.read8(addr)]
		return (ip.length,self.ram[addr:addr+ip.length].hex())

	def print_data(self, addr):
		if self.flags[addr] & Flags.WORD_LOW:
			step = 2
			rc = ".word %04x" % (self.read16(addr))
		else:
			step = 1
			rc = ".byte %02x" % (self.read8(addr))
		for j in range(step,8,step):
			if addr + j >= self.max_addr:
				break
			if self.flags[addr+j] & (Flags.JREF | Flags.SREF | Flags.DREF | Flags.ISOP | Flags.NAMED):
				break
			if self.flags[addr] & Flags.WORD_LOW:
				rc += ",%04x" % (self.read16(addr+j))
			else:
				rc += ",%02x" % (self.read8(addr+j))
		return (j,rc)

	# returns the instruction format string, the name of the target if any, and the target address or operand
	def dis_instr(self, addr):
		opcode = self.read8(addr)
		ip = opcode_table[opcode]
		fmt = ip.name.lower()
		if ip.length == 1:
			operand = 0
		elif ip.length == 2:
			operand = self.read8(addr+ 1)
		elif ip.length == 3:
			operand = self.read16(addr + 1)
		addr += ip.length

		if ip.flags & OpcodeFlags.REL:
			operand = sign8(operand) + addr

		name = self.name(operand, 1)

		if ip.flags & OpcodeFlags.IMM:
			# put the literal operand; should we do a constant lookup?
			fmt += " #$%02x" % (operand)
			name = None
		elif ip.flags & (OpcodeFlags.ACC | OpcodeFlags.IMP):
			name = None
		elif ip.flags & (OpcodeFlags.REL | OpcodeFlags.ABS | OpcodeFlags.ZPG):
			fmt += " %s"
		elif ip.flags & (OpcodeFlags.IND | OpcodeFlags.ZPI):
			fmt += " (%s)"
		elif ip.flags & (OpcodeFlags.ABX | OpcodeFlags.ZPX):
			fmt += " %s,X"
		elif ip.flags & (OpcodeFlags.ABY | OpcodeFlags.ZPY):
			fmt += " %s,Y"
		elif ip.flags & (OpcodeFlags.INX):
			fmt += " (%s,X)"
		elif ip.flags & (OpcodeFlags.INY):
			fmt += " (%s),Y"
		else:
			fmt += ' ???'
			name = None

		return (fmt, name, operand)

	def print_instr(self, addr):
		(fmt,name,operand) = self.dis_instr(addr)
		if name:
			return fmt % (name)
		else:
			return fmt

	def disassemble(self, addr, include_label=True):
		rc = ''
		name = self.name(addr)
		if name and include_label:
			if self.flags[addr] & Flags.SREF:
				rc += "\n"
			rc += "\t%s:\n" % (name)

		if self.is_op(addr):
			(len,hexdump) = self.print_bytes(addr)
			rc += "%04x  %-6s  " % (addr, hexdump)
			rc += self.print_instr(addr)
		else:
			(len,hexdump) = self.print_data(addr)
			rc += "%04x      %s" % (addr, hexdump)
		return (len, rc)

	def disassemble_html(self, addr):
		rc = "<div id=%04x>" % (addr)
		name = self.name(addr)
		if name:
			flags = self.flags[addr]
			c = "func" if flags & Flags.SREF else "label"
			rc += f"<div class={c} id={name}>{name}:</div>"
			for ref in self.refs.get(addr,[]):
				ref_addr = "%04x" % (ref)
				ref_name = ref_addr

				if flags & (Flags.SREF | Flags.DREF):
					ref_name = self.name_relative(ref)
				rc += f"<a class='xref link' href=#{ref_addr}>{ref_name}</a>"
			rc += "<br/>\n"
		#rc += f"<span class=anchor id=%04x></span>" % (addr)
		rc += "<div class=addr>%04x</div>" % (addr)
		if self.is_op(addr):
			(len,hexdump) = self.print_bytes(addr)
			instr = self.print_instr(addr, do_html=True)
			rc += f"<div class=bytes>{hexdump}</div><div class=instr>{instr}</div>"
		else:
			(len,hexdump) = self.print_data(addr)
			rc += f"<div class=bytes>{hexdump}</div>"

		rc += "</div>"

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

	# Returns false if the symbol failed to be added (but true if it already exists)
	def add_symbol(self, addr, name, data_type, array_size):
		if not self.save_name(addr, name, data_type, array_size, force=True):
			return True

		if array_size is None:
			array_size = 1
			array_flag = 0
		else:
			array_flag = Flags.ARRAY
			self.arrays[addr] = array_size | 0x10000

		if data_type == "ptr":
			is_ptr = True
			array_flag |= Flags.PTR
		else:
			is_ptr = False

		if data_type == "word" or is_ptr:
			array_size *= 2

		for i in range(0,array_size):
			el_addr = addr + i
			if i == 0:
				pass
			elif array_flag:
				if el_addr in self.arrays or el_addr in self.names:
					raise RuntimeError("%04x %s %d: overlaps existing variable at %s %04x?" % (addr, name, array_size, self.name(el_addr), el_addr))
				self.arrays[el_addr] = addr
			else:
				if self.flags[el_addr] & Flags.ARRAY:
					raise RuntimeError("%04x %s %d: overlaps existing array at %04x?" % (el_addr, name, array_size, self.arrays[el_addr]))

			if data_type is None or data_type == "byte":
				#self.flags[el_addr] |= Flags.DREF | array_flag
				self.flags[el_addr] |= array_flag
			elif data_type == "func" or data_type == "label":
				self.flags[el_addr] |= Flags.SREF
			elif data_type == "word" or is_ptr:
				self.flags[el_addr] |= Flags.DREF | array_flag \
					| (Flags.WORD_HIGH if i % 2 else Flags.WORD_LOW)
			else:
				raise RuntimeError(f"unknown data type '{data_type}'")

			# add a data reference for each ptr word
			if is_ptr and i % 2 == 0:
				dest = self.read16(el_addr)
				#print("ptr ref %04x -> %04x" % (addr, dest), file=sys.stderr)
				self.save_ref(addr, dest)

		return True
	def load_symbols(self, filename):
		with open(filename, "r") as f:
			line_num = 0
			while (line := f.readline()):
				# address label optional-type
				line_num += 1
				words = line.rstrip().split()
				addr = int(words[0], 16)
				name = words[1]
				data_type = words[2] if len(words) > 2 else None
				array_size = int(words[3],0) if len(words) > 3 else None

				if not self.add_symbol(addr, name, data_type, array_size):
					raise RuntimeError(f"{filename}:{line_num}: Unknown type {words[2]}")
					

if __name__ == "__main__":

	if len(sys.argv) <= 1:
		print(f"""Usage:
{sys.argv[0]} filename.bin [filename.sym] [base_addr] [vector_addr]
""", file=sys.stderr)
		sys.exit(-1)

	filename = sys.argv[1]
	symbols = sys.argv[2] if len(sys.argv) > 2 else None
	base = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0x4800
	vector = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x8000

	dis = Dis6502()
	dis.load_binary(filename, base)
	dis.vector(vector)

	if symbols:
		dis.load_symbols(symbols)

	dis.trace_all()

	dis.dumpitout()
