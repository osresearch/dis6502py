#!/usr/bin/env python3
# Annotate a 6502 disassembly using the dis6502py to take it apart
# and markup language to comment on the code.

import os
import sys
import re
from dis6502 import Dis6502, Flags
from opcodes import opcode_table, OpcodeFlags
from dvg import DVG

header = """<!doctype html>
<html><head>
<meta charset=utf-8>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="../static/style.css">
</head>
<body>
"""

footer = """<!-- footer -->
<script src="../static/highlight.js"></script>
</body>
</html>
"""

class Annotator:
	def __init__(self):
		self.addr = None
		self.mode = "text"
		self.title = "Annotated Disassembly"
		self.dis = Dis6502()
		self.filename = None
		self.symbols_filename = None
		self.last_name = None
		self.block_comment = ''
		self.block_comments = {}
		self.dvg = None
		self.dvg_rom = None

	def warn(self, s):
		print(f"{self.filename}:{self.line_num}: {'%04x' % (self.addr if self.addr else 0x0)} {s}", file=sys.stderr)

	def annotate_file(self, filename):
		self.line_num = 1
		self.filename = filename
		with open(file, "r") as f:
			while (line := f.readline()):
				try:
					self.annotate(line)
					self.line_num += 1
				except Exception as e:
					self.warn("error")
					raise(e)

	# update the hex dumps and labels in a file with the current symbols
	def rewrite_file(self, filename):
		self.line_num = 1
		self.filename = filename
		lines = open(filename, "r").readlines()
		os.rename(filename, filename + ".bak")
		with open(filename, "w") as f:
			for line in lines:
				line = line.rstrip()
				m = re.match(r"([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s*([^;]+)(;.*)?", line)
				if not m:
					print(line, file=f)
					continue

				# this is a hex dump line; disassemble the instruction
				addr = int(m[1],16)
				comment = m[4] if m[4] else ";"
				(len,text) = self.dis.disassemble(addr, include_label=False)

				# pad the text so that the correct number of tabs lines it up
				text = text.ljust(40)
				print(text, comment, file=f)


	def annotate(self, line):
		line = line.rstrip()
		words = line.split()
		if len(words) == 0:
			if self.mode == "text":
				print("<p>")
		elif words[0] == ".title":
			self.title = ' '.join(words[1:])
#		elif words[0] == ".text":
#			self.mode = "text"
#			print("<br/><p>")
		elif words[0] == ".header":
			print(header % (self.title))
		elif words[0] == ".footer":
			print(footer)

		# commands to the disassembler
		elif words[0] == ".binary":
			self.dis.load_binary(words[1], int(words[2],0))
		elif words[0] == ".vector":
			self.dis.vector(int(words[1],0))
		elif words[0] == ".symbols":
			self.symbols_filename = words[1]
			self.dis.load_symbols(words[1])
		elif words[0] == ".save_symbols":
			self.save_symbols()
		elif words[0] == ".trace":
			self.dis.trace_all()
		elif words[0] == ".dump":
			self.dump(words[1])

		# formatting commands
		elif words[0].startswith("```"):
			self.mode = "text" if self.mode != "text" else "code"
		elif words[0] == ';':
			self.block_comment += self.fake_markdown(line) + "<br/>\n"
		elif words[0] == ".func":
			self.start_func(words[1])
		elif words[0] == ".label":
			self.add_label(words[1])
		elif words[0] == ".byte":
			self.add_data("byte", words[1:])
		elif words[0] == ".word":
			self.add_data("word", words[1:])
		elif words[0] == ".ptr":
			self.add_data("ptr", words[1:])
		elif words[0] == ".dvg":
			self.process_dvg(words[1:])
		elif words[0] == ".dvg_parse":
			self.dvg_parse(words[1:])
		elif words[0][0] == ".":
			raise RuntimeError("Unknown directive " + words[0])
		elif self.mode == "dis" or self.mode == "func" or self.mode == "label":
			self.disassemble(line) #int(words[0],16), words[1:])
		else:
			print(self.fake_markdown(line))

	# create a link to a reference
	def make_ref_link(self, ref, ref_addr):
		ref_addr = "%04x" % (ref_addr)
		return f"<a class=link href=#{ref_addr}>{ref}</a>"

	# apply some markdown like functions to the line
	def fake_markdown(self, line):
		def lookup_ref(m):
			ref = m[1]
			if re.match(r"^(0x)?[0-9A-Fa-f]+$", ref):
				ref_addr = int(ref,16)
			else:
				ref_addr = self.dis.all_names.get(ref,[None])[0]
			if not ref_addr:
				raise RuntimeError(f"reference '@{ref}' not found")
			return self.make_ref_link(ref, ref_addr)

		# should also build a TOC while doing this...
		line = re.sub(r'^####\s*(.*)$', r'<h4>\1</h4>', line)
		line = re.sub(r'^###\s*(.*)$', r'<h3>\1</h4>', line)
		line = re.sub(r'^##\s*(.*)$', r'<h2>\1</h4>', line)
		line = re.sub(r'^#\s*(.*)$', r'<h1>\1</h4>', line)

		# turn `foo` into fixed format
		line = re.sub(r'`(.+?)`', r'<tt>\1</tt>', line)

		# turn @foo into links to addresses or symbols
		line = re.sub(r'@([^!()[,.\s]+)', lookup_ref, line)

		# ![caption](image-link)
		line = re.sub(r'^!\[(.*?)\]\((.*?)\)\s*$',
			r'<a href="\2"><img src="\2" width=50% alt="\1"/></a>',
			line
		)

		# [text](link)
		line = re.sub(r'\[(.*?)\]\((.*?)\)',
			r'<a href="\2">\1</a>',
			line
		)

		# bulleted lists (need to make this work better)
		line = re.sub(r'^\*\s+(.*)', r'<li>\1', line)

		return line


	def start_func(self, name):
		name = name.rstrip(":")
		self.mode = "func"
		self.last_name = name
		self.addr = None

	def add_label(self, name):
		name = name.rstrip(":")
		self.mode = "label"
		self.last_name = name

	def make_label(self, addr):
		# is this address a function or label?
		name = self.dis.name(addr)
		if not name:
			return ''

		flags = self.dis.flags[addr]
		div_class = "data_label"
		if flags & Flags.SREF:
			div_class = "func"
		elif flags & Flags.ISOP:
			div_class = "label"

		rc = f"\n\t<div class={div_class} id={name}>{name}:</div>"

		for ref in self.dis.refs.get(addr,[]):
			ref_addr = "%04x" % (ref)
			ref_name = ref_addr

			if flags & (Flags.SREF | Flags.DREF):
				ref_name = self.dis.name_relative(ref)
			rc += f"<a class='xref link' href=#{ref_addr}>{ref_name}</a>"

		return rc + "<br/>"

	# a line that starts with a hex address
	def disassemble(self, line):
		m = re.match(r"([0-9a-fA-F]+)\s*([0-9a-fA-F]+)\s*([^;]+)(;.*)?", line)
		if not m:
			raise RuntimeError("unable to parse disassembly")
		addr = int(m[1],16)
		dis_hexdump = m[2]
		dis_instr = m[3]
		comment = m[4]

		# if we are in function or label mode, this new address
		# is gets a new name.
		if self.mode == "func" or self.mode == "label":
			self.dis.save_name(addr, self.last_name, self.mode, force=True)
			if self.mode == "func":
				self.dis.flags[addr] |= Flags.SREF;
			self.mode = "dis"

		# the assumption is that the addresses will continue monotonically
		if not self.addr is None and self.addr != addr:
			self.warn("Expected address %04x not %04x" % (self.addr, addr))

		# make sure we are in a function
		if not self.dis.is_op(addr):
			self.warn("Address %04x is not an instruction" % (addr))

		# the next word should be the hex dump of the instructions
		(len,hexdump) = self.dis.print_bytes(addr)
		if dis_hexdump != hexdump:
			self.warn(f"Expected hexdump {hexdump} not {dis_hexdump}")

		# looks like we're good; disassemble it!
		self.addr = addr + len

		print(self.disassemble_instr(addr, comment))

	def make_address_div(self, addr, interior):
		label_div = self.make_label(addr)
		comment_div = ""
		block_comment_div = ""

		if comment := self.dis.comments.get(addr):
			comment_div = f"\n\t<div class=comment>{self.fake_markdown(comment)}</div>"

		if comment := self.block_comments.get(addr):
			block_comment_div = f"\n\t<div class=block_comment>{comment}</div>"

		addr_hex = "%04x" % (addr)

		return f"""
	<div id={addr_hex}>{block_comment_div}{label_div}
		<div class=addr>{addr_hex}</div>
		{interior}{comment_div}
	</div>"""

	def disassemble_instr(self, addr, comment):
		# disassemble the instruction and hyperlink the destination if there is one
		(fmt,op_name,operand) = self.dis.dis_instr(addr)

		instr = fmt
		if op_name:
			if self.dis.flags[operand] & Flags.ARRAY:
				(operand,_) = self.dis.array_ref(operand)
			elif self.dis.flags[operand] & Flags.WORD_HIGH:
				operand -= 1

			# for branches, add an arrow for the direction
			opflags = opcode_table[self.dis.ram[addr]].flags
			if not opflags & (OpcodeFlags.FORK | OpcodeFlags.JUMP):
				arrow = ""
			elif operand > addr:
				arrow = "&darr;"
			elif operand < addr:
				arrow = "&uarr;"
			else:
				arrow = "&olarr;"

			op_name = "<a class=link href=#%04x>%s%s</a>" % (operand,op_name, arrow)
			instr = fmt % (op_name)

		if self.block_comment != '':
			self.block_comments[addr] = self.block_comment
			self.block_comment = ''
		if comment:
			self.dis.comments[addr] = comment

		(_,hexdump) = self.dis.print_bytes(addr)

		return self.make_address_div(addr, f"""
	<div class=bytes>{hexdump}</div>
	<div class=instr>{instr}</div>"""
		)

	def save_symbols(self):
		if not self.symbols_filename:
			return

		# backup the old one
		os.rename(self.symbols_filename, self.symbols_filename + ".bak")

		# write the new symbols
		with open(self.symbols_filename, "w") as f:
			for addr in range(0,self.dis.max_addr):
				flags = self.dis.flags[addr]
				if flags & Flags.NAMED == 0:
					continue
				name = self.dis.names[addr]

				if flags & Flags.SREF:
					data_type = " func"
				elif flags & Flags.WORD_LOW and flags & Flags.PTR:
					data_type = " ptr"
				elif flags & Flags.WORD_LOW:
					data_type = " word"
				else:
					data_type = ""

				if flags & Flags.ARRAY:
					array_size = self.dis.arrays[addr]
					if array_size & 0x10000 == 0:
						raise RuntimeError("%s %04x: named memory in array?" % (name, addr))
					array_size = " %d" % (array_size & 0xFFFF)
					if data_type == "":
						data_type = " byte"
				else:
					array_size = ""

				print("%04x %s%s%s" % (addr, name, data_type, array_size), file=f)

	def add_data(self, data_type, words):
		# addr name [optional-array-size] [; optional comment]
		line = ' '.join(words)
		m = re.match(r"((?:0x)?[0-9A-Fa-f]+)\s+([^\s]+)\s+(0x[0-9A-Fa-f]+|[0-9]+)?\s*(;.*)$", line)
		if not m:
			raise RuntimeError(f"unable to parse data definition '{line}'")

		addr = int(m[1],16)
		name = m[2]
		array_len = int(m[3],0) if m[3] else None
		comment = m[4]

		self.dis.add_symbol(addr, name, data_type, array_len)

		if self.block_comment != '':
			self.block_comments[addr] = self.block_comment
			self.block_comment = ''

		(data_len,div) = self.print_data(addr, comment)
		print(div)

	def print_data(self, addr, comment):
		array_text = ""
		hexdump = ""

		if comment:
			self.dis.comments[addr] = comment
			comment_div = f"\n\t<div class=comment>{self.fake_markdown(comment)}</div>"

		addr_hex = "%04x" % (addr)

		flags = self.dis.flags[addr]

		if flags & Flags.PTR:
			data_type = "ptr"
			element_size = 2
		elif flags & Flags.WORD_LOW:
			data_type = "word"
			element_size = 2
		else:
			data_type = "byte"
			element_size = 1

		array_len = self.dis.arrays.get(addr, 1) & 0xFFFF

		if flags & Flags.LOADED:
			hexdump = []
			for i in range(0,array_len):
				el_addr = addr + element_size * i
				if data_type == "word":
					hexdump.append("%04x" % self.dis.read16(el_addr))
				elif data_type == "ptr":
					ref_addr = self.dis.read16(el_addr)
					hexdump.append(self.make_ref_link(self.dis.name(ref_addr), ref_addr))
				else:
					hexdump.append("%02x" % self.dis.read8(el_addr))
			hexdump = ' ' + (', '.join(hexdump))

		if array_len > 1:
			array_text = "[%d]" % (array_len)

		data_size = array_len * element_size
		return (data_size, self.make_address_div(addr, f"""<div class=hexdump>.{data_type}{array_text}{hexdump}</div>"""))

	# produce a consolidated dump (along with stats)
	def dump(self, filename):
		with open(filename, "w") as f:
			print(header % (self.title), file=f)
			self.addr = 0

			total_ops = 0
			op_comments = 0
			total_data = 0
			data_comments = 0

			while self.addr < self.dis.max_addr:
				if self.dis.flags[self.addr] == 0:
					self.addr += 1
					continue

				comment = self.dis.comments.get(self.addr)
				flags = self.dis.flags[self.addr]

				if flags & Flags.ISOP:
					print(self.disassemble_instr(self.addr, comment), file=f)
					self.addr += self.dis.instr_len(self.addr)
					total_ops += 1

					# don't include empty comments, which are added automatically
					if comment and len(comment) > 1:
						op_comments += 1
				elif flags & Flags.DREF:
					(data_len,div) = self.print_data(self.addr, comment)
					print(div, file=f)
					self.addr += data_len

					# treat arrays as a single item
					if comment and len(comment) > 1:
						data_comments += 1
					total_data += 1
				else:
					# TODO: handle data
					self.addr += 1
					total_data += 1
			print(footer, file=f)

		print("OPS %d comments / %d instructions %.2f%%" % (op_comments, total_ops, 100.0 * op_comments / total_ops), file=sys.stderr)
		print("DAT %d comments / %d data bytes %.2f%%" % (data_comments, total_data, 100.0 * data_comments / total_data), file=sys.stderr)

	# Generate an inline SVG of the Vector Generator output for some memory
	# dvg addr width height
	def process_dvg(self, words):
		if not self.dvg_rom:
			# if we haven't initialized it yet, create a DVG using the loaded binary
			self.dvg_rom = self.dis.ram[0x4800:0x6000]
		addr = int(words[0], 16)
		length = 2
		width = 1024
		height = 1024
		scale = 11

		if len(words) > 1:
			length = int(words[1], 0) * 2
		if len(words) > 2:
			width = int(words[2], 0)
		if len(words) > 3:
			height = int(words[3], 0)
		if len(words) > 4:
			scale = int(words[4], 0)
		cmd = self.dis.ram[addr:addr+length]

		dvg = DVG(self.dvg_rom, width=width, height=height)
		dvg.s = scale
		dvg.x = 0
		dvg.y = height - 2
		print("DVG %04x+%04x" % (addr, length), file=sys.stderr)
		print(dvg.process(cmd))

	def dvg_parse(self, words):
		if not self.dvg_rom:
			# if we haven't initialized it yet, create a DVG using the loaded binary
			self.dvg_rom = self.dis.ram[0x4800:0x6000]
		addr = int(words[0], 16)
		name = words[1]
		length = int(words[2], 0)
		dvg = DVG(self.dvg_rom)
		ram = self.dis.ram[addr:addr+2*length]
		dvg.process(ram, do_jumps=False)

		self.add_data("word", words)
		print("<ul><li>", "<li>".join(dvg.trace_log), "</ul>")


ann = Annotator()
for file in sys.argv[1:]:
	ann.annotate_file(file)
for file in sys.argv[1:]:
	ann.rewrite_file(file)
