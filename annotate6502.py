#!/usr/bin/env python3
# Annotate a 6502 disassembly using the dis6502py to take it apart
# and markup language to comment on the code.

import os
import sys
import re
from dis6502 import Dis6502, Flags

header = """<!doctype html>
<html><head>
<meta charset=utf-8>
<title>%s</title>
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
"""

footer = """<!-- footer -->
<script src="highlight.js"></script>
</body>
</html>
"""

class Annotator:
	def __init__(self):
		self.addr = None
		self.mode = "text"
		self.title = "Annotated Disassembly"
		self.dis = Dis6502()

	def warn(self, s):
		print(f"{self.filename}:{self.line_num}: {s}", file=sys.stderr)

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


	def annotate(self, line):
		line = line.rstrip()
		words = line.split()
		if len(words) == 0:
			if self.mode == "text":
				print("<br/>")
		elif words[0] == ".title":
			self.title = ' '.join(words[1:])
		elif words[0] == ".text":
			self.mode = "text"
			print("<br/>")
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
			self.dis.load_symbols(words[1])
		elif words[0] == ".trace":
			self.dis.trace_all()

		# formatting commands
		elif words[0] == ".func":
			self.start_func(words[1])
		elif words[0] == ".label":
			self.add_label(words[1])
		elif words[0][0] == ".":
			raise RuntimeError("Unknown directive " + words[0])
		elif self.mode == "func": #re.match(r"[0-9a-fA-F]+", words[0]):
			self.disassemble(line) #int(words[0],16), words[1:])
		else:
			print(line, end='')


	def start_func(self, name):
		self.mode = "func"
		self.func = name
		self.addr = None
		#print(f"<div class=func id={name}>{name}</div>")

	def add_label(self, name):
		#print(f"<div class=label id={name}>{name}:</div>")
		pass

	def make_label(self, addr):
		# is this address a function or label?
		name = self.dis.name(addr)
		if not name:
			return ''

		flags = self.dis.flags[addr]
		div_class = "func" if flags & Flags.SREF else "label"

		rc = f"\n\t<div class={div_class} id={name}>{name}:</div>"

		for ref in self.dis.refs.get(addr,[]):
			ref_addr = "%04x" % (ref)
			ref_name = ref_addr

			if flags & (Flags.SREF | Flags.DREF):
				ref_name = self.dis.name_relative(ref)
			rc += f"<a class='xref link' href=#{ref_addr}>{ref_name}</a>"

		return rc + "<br/>"

		
		# check for xrefs for this address
	# a line that starts with a hex address
	def disassemble(self, line):
		m = re.match(r"([0-9a-fA-F]+)\s*([0-9a-fA-F]+)\s*([^;]+)(;.*)?", line)
		if not m:
			raise RuntimeError("unable to parse disassembly")
		addr = int(m[1],16)
		dis_hexdump = m[2]
		dis_instr = m[3]
		comment = m[4]

		# the assumption is that the addresses will continue monotonically
		if not self.addr is None and self.addr != addr:
			self.warn("Expected address %04x not %04x" % (self.addr, addr))
		addr_hex = "%04x" % (addr)

		# make sure we are in a function
		if not self.dis.is_op(addr):
			self.warn("Address %04x is not an instruction" % (addr))

		# the next word should be the hex dump of the instructions
		(len,hexdump) = self.dis.print_bytes(addr)
		if dis_hexdump != hexdump:
			self.warn(f"Expected hexdump {hexdump} not {dis_hexdump}")

		# disassemble the instruction and hyperlink the destination if there is one
		(fmt,op_name,operand) = self.dis.dis_instr(addr)
		if not op_name:
			instr = fmt
		else:
			op_name = "<a class=link href=#%04x>%s</a>" % (operand,op_name)
			instr = fmt % (op_name)

		label_div = self.make_label(addr)
		comment_div = f"\n\t<div class=comment>{comment}</div>" if comment else ""

		print(f"""<div id={addr_hex}>{label_div}
	<div class=addr>{addr_hex}</div>
	<div class=bytes>{hexdump}</div>
	<div class=instr>{instr}</div>{comment_div}
</div>""")

		self.addr = addr + len


for file in sys.argv[1:]:
	Annotator().annotate_file(file)
