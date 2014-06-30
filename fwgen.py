#!/usr/bin/env python3
import sys
import struct
import xml.etree.ElementTree as ET

import sys
import binascii
 
class SigmadDSPFirmwareGen(object):

	CHUNK_TYPE_DATA = 0
	CHUNK_TYPE_CONTROL = 1
	CHUNK_TYPE_SAMPLERATES = 2

	CHUNK_HEADER_SIZE = 12
	CHUNK_DATA_HEADER_SIZE = CHUNK_HEADER_SIZE + 2
	CHUNK_CONTROL_HEADER_SIZE = CHUNK_HEADER_SIZE + 6

	def __init__(self, in_files, out_file):
		self.crcsum = 0xffffffff
		self.size = 12
		self.out = open(out_file, "wb")

		self.out.write(b"ADISIGM")
		self.out.write(struct.pack("<BI", 2, 0x0000)) # checksum, will be overwritten latter

		samplerates = []
		samplerate_mask = 1

		for in_file, samplerate in in_files:
			samplerates.append(samplerate)
			self.parse_input_file(in_file, samplerate_mask)
			samplerate_mask <<= 1

		self.write_samplerates_chunk(samplerates)

		self.out.seek(8)
		# binascii.crc32() inverts the bits interally here we intert it back
		self.crcsum ^= 0xffffffff
		self.out.write(struct.pack('<I', self.crcsum))
		self.out.close()

	def parse_input_file(self, filename, samplerate_mask):
		tree = ET.parse(filename)
	
		for child in tree.getroot().iter("Program"):
			name = child.find("Name").text
			if name != "Program Data":
				continue
			self.write_data_chunk(child, samplerate_mask)

		for child in tree.getroot().iter("Register"):
			name = child.find("Name").text
			if name != "Param":
				continue
			self.write_data_chunk(child, samplerate_mask)

		for child in tree.getroot().iter("Module"):
			name = child.find("CellName").text
			for para in child.iter("ModuleParameter"):
				self.write_control_chunk(para, name, samplerate_mask)

	def write(self, data):
		self.out.write(data)
		self.crcsum = binascii.crc32(data, self.crcsum)
		self.size += len(data)

	def write_chunk_header(self, size, type, samplerate_mask):
		# The start of a chunk is 4bytes aligned
		padding = ((self.size + 3) & ~3) - self.size
		for i in range(0, padding):
			self.write(b"\xaa")
		self.write(struct.pack("<III", size, type, samplerate_mask))

	def write_data_chunk(self, node, samplerate_mask):
		addr = int(node.find("Address").text)
		size = int(node.find("Size").text)

		data = node.find("Data").text
		data = bytes([int(x.strip(), 16) for x in data.split(",") if x.strip()])

		size += self.CHUNK_DATA_HEADER_SIZE

		self.write_chunk_header(size, self.CHUNK_TYPE_DATA, samplerate_mask)
		self.write(struct.pack("<H", addr))
		self.write(data)	

	def write_control_chunk(self, node, name, samplerate_mask):
		pname = node.find("Name").text
		addr = int(node.find("Address").text)
		length = int(node.find("Size").text)
		name_len = len("%s %s" % (name, pname))

		size = self.CHUNK_CONTROL_HEADER_SIZE + name_len

		self.write_chunk_header(size, self.CHUNK_TYPE_CONTROL, samplerate_mask)
		self.write(struct.pack("<HHH", 0, addr, length))
		self.write(bytearray("%s %s" % (name, pname), "ascii"))

	def write_samplerates_chunk(self, samplerates):
		size = self.CHUNK_HEADER_SIZE + len(samplerates) * 4
		self.write_chunk_header(size, self.CHUNK_TYPE_SAMPLERATES, 0)
		for samplerate in samplerates:
			self.write(struct.pack("<I", samplerate))

if __name__ == "__main__":
	if len(sys.argv) % 2 != 0 or len(sys.argv) < 4:
		sys.exit(1)

	in_files = []
	for i in range(1, len(sys.argv) - 2, 2):
		in_files.append((sys.argv[i], int(sys.argv[i+1])))

	SigmadDSPFirmwareGen(in_files, sys.argv[-1])
