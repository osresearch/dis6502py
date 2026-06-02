#!/usr/bin/env python3
# Annotate a 6502 disassembly using the dis6502py to take it apart
# and markup language to comment on the code.

import os
import sys
from dis6502 import Dis6502


class Annotator:
	def __init__(self):
		self.addr = 0
		self.mode = "text"
		self.dis = Dis6502()

	def binary(self, file, addr):
		self.dis.load_binary(file, addr)
	def vector(self, addr):
		self.dis.vector(addr)
	def symbols(self, filename):
		self.dis.load_symbols(filename)

	def annotate(self, line):
		words = line.rstrip().split()
		if len(words) == 0:
			print()
		elif words[0] == ".text":
			self.mode = "text"
		elif words[0] == ".binary":
			self.binary(words[1], int(words[2],0))
		elif words[0] == ".vector":
			self.vector(int(words[1],0))
		elif words[0] == ".symbols":
			self.symbols(words[1])
		elif words[0][0] == ".":
			raise RuntimeError("Unknown directive " + words[0])
		else:
			print(line, end='')
		

annotate = Annotator()

for file in sys.argv[1:]:
	with open(file, "r") as f:
		line_num = 1
		while (line := f.readline()):
			try:
				annotate.annotate(line)
				line_num += 1
			except Exception as e:
				print(f"{file}:{line_num}: error")
				raise(e)
