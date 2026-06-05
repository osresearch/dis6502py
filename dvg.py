#!/usr/bin/env python3 
# Emulate the Atari Digital Vector Generator
# and output an SVG rendering of a command stream
# https://computerarcheology.com/Arcade/Asteroids/DVG.html
import drawsvg as draw
import struct
import sys
from hashlib import sha256

class DVG:
	def __init__(self, rom, width=1024, height=1024):
		# ROM starts at 0x800
		self.rom = rom
		self.debug = False
		self.reset()

		self.d = draw.Drawing(
			width, height,
			origin=(0,0),
			style="background-color:black",
		)

	def reset(self):
		self.pc = 0
		self.x = 0
		self.y = 0
		self.s = 3
		self.stack = []
		self.trace_log = []

	def svg(self):
		return self.d.as_svg()

	def trace(self, s):
		if self.debug:
			print(s, file=sys.stderr)
		self.trace_log.append(s)

	def add_line(self, bright, scale, sx, x, sy, y):
		if sx: x = -x
		if sy: y = -y

		scale = 2 ** (10 - self.s - scale)
		nx = self.x + x / scale
		ny = self.y - y / scale

		if bright != 0:
			self.d.append(draw.Lines(
				self.x, self.y, nx, ny,
				fill='none',
				stroke_width=2,
				stroke='#%01x%01x%01x' % (bright,bright,bright),
			))
		else:
			self.d.append(draw.Circle(nx, ny, 1, fill='#888'))

		self.x = nx
		self.y = ny

	def read16(self,addr):
		if addr < 0x800:
			if addr > len(self.ram) - 1:
				return None
			(word,) = struct.unpack("<H", self.ram[addr:addr+2])
		else:
			addr -= 0x800
			if addr > len(self.rom) - 1:
				return None
			(word,) = struct.unpack("<H", self.rom[addr:addr+2])
		return word

	def process(self, ram):
		self.ram = ram
		while self.execute(self.pc):
			pass
		return self.svg()

	def execute(self, cmd):
		cmd = self.read16(self.pc)
		if not cmd:
			return False
		self.pc += 2

		c = (cmd >> 12) & 0xF
		if c <= 0x9:
			# VEC
			cmd2 = self.read16(self.pc)
			self.pc += 2
			scale = (cmd >> 12) & 0xF
			sy = (cmd >> 10) & 1
			y = (cmd >> 0) & 0x3FF
			bright = (cmd2 >> 12) & 0xF
			sx = (cmd2 >> 10) & 1
			x = (cmd2 >> 0) & 0x3FF
			self.trace(f"VCTR {scale=} {sx=} {x=} {bright=} {sy=} {y=}")
			self.add_line(bright, scale, sx, x, sy, y)
		elif c == 0xA:
			# LABS
			# this sets the global scale factor and moves ox,oy
			cmd2 = self.read16(self.pc)
			self.pc += 2
			self.y = (cmd >> 0) & 0x3FF
			self.x = (cmd2 >> 0) & 0x3FF
			self.s = (cmd2 >> 12) & 0xF
			self.trace(f"LABS scale={self.s} x={self.x} y={self.y}")
		elif c == 0xB:
			# HALT
			self.trace("HALT")
			return False
		elif c == 0xC:
			# JSR
			self.stack.append(self.pc)
			self.pc = ((cmd & 0xFFF) << 1)
			self.trace("JSRL %04x (%04x)" % (self.pc, cmd))
		elif c == 0xD:
			# RTS
			self.trace("RTSL")
			if len(self.stack) == 0:
				return False
			self.pc = self.stack[-1]
			self.stack = self.stack[0:-1]
		elif c == 0xE:
			# JMP
			self.pc = ((cmd & 0xFFF) << 1)
			self.trace("JMPL %04x (%04x)" % (self.pc, cmd))
		elif c == 0xF:
			# SVEC
			s1 = (cmd >> 11) & 0x1
			sy = (cmd >> 10) & 0x1
			y  = (cmd >>  8) & 0x3
			b  = (cmd >>  4) & 0xF
			s2 = (cmd >>  3) & 0x1
			sx = (cmd >>  2) & 0x1
			x  = (cmd >>  0) & 0x3

			scale = (s2 << 1 | s1)
			self.trace(f"SVEC s=%3d b=%01x x=%+3d y=%+3d" % (
				2**scale, b,
				-x if sx else +x,
				-y if sy else +y,
			))
			self.add_line(b, 2**scale, sx, x, sy, y)

		return True
		
#d.save_svg("output.svg")


if __name__ == "__main__":
	rom = open("llander/llander-0x4800.bin", "rb").read()
	rom = rom[:0x6000-0x4800]

	dvg = DVG(rom, width=1024, height=64)

	font_addr = 0x57a4 - 0x4800
	font = rom[font_addr:font_addr+92]

	dvg.s = 11
	dvg.x = 0
	dvg.y = 60
	print(dvg.process(font))
