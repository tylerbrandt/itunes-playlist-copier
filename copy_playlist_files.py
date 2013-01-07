from __future__ import print_function

import argparse
import codecs
import csv
import os
import shutil
import sys

class PlaylistCopier:
	def __init__(self, args):
		self.args = args

	def copy(self):
		self.playlist_file = self.args.playlist
		self.input_dir, playlist_basename = os.path.split(self.playlist_file)

		if not os.path.exists(self.playlist_file):
			print("File not found:", self.playlist_file)
			sys.exit(1)

		playlist_name, format = os.path.splitext(playlist_basename)

		self.initialize_output_dir(playlist_name)

		self.output_filename = os.path.join(self.dirname, playlist_basename)

		self.index = 0
		if format == ".txt":
			self.parse_txt()
		elif format == ".m3u":
			self.parse_m3u()
		else:
			print("Unrecognized format:", format)

	def initialize_output_dir(self, playlist_name):
		"""Create/clean the directory specified (default is playlist_name)"""
		self.dirname = self.args.directory or os.path.join(self.input_dir, playlist_name)
		if not os.path.exists(self.dirname):
			os.mkdir(self.dirname)
			print("Created directory:", self.dirname)
		else:
			for existing_file in os.listdir(self.dirname):
				os.unlink(os.path.join(self.dirname, existing_file))
				if self.args.verbose:
					print("Deleted:", existing_file)
			print("Deleted contents of:", self.dirname)

	def parse_m3u(self):
		"""Parse m3u file of the form:

		    #EXTM3U
			#EXTINF:258,Can't Hold Us (feat. Ray Dalton) - Macklemore & Ryan Lewis
			/Users/tyler/Music/iTunes/iTunes Media/Music/Macklemore & Ryan Lewis/The Heist (Deluxe Edition)/02 Can't Hold Us (feat. Ray Dalton).mp3
			#EXTINF:266,Other People - Beach House
			/Users/tyler/Music/iTunes/iTunes Media/Music/Beach House/Bloom/04 Other People.mp3
		"""
		with open(self.playlist_file, 'r') as infile, open(self.output_filename, 'w') as outfile:
			# readlines doesn't behave properly with these files
			lines = infile.readline().split('\r')
			for line in lines:
				if line:
					if line[0] == "#":
						# just copy directive lines
						outfile.write(line + '\r')
					else:
						# file path
						path = line.strip()
						new_path = self.replace_filename(path)
						outfile.write(new_path + '\r')
						self.index += 1
						self.update_progress()
			print('Done')

	def parse_txt(self):
		"""Parse 'Unicode Text' CSV-ish format from iTunes"""
		with codecs.open(self.playlist_file, 'r', self.args.encoding) as infile:
			with codecs.open(self.output_filename, 'w', self.args.encoding) as outfile:
				reader = csv.DictReader(infile, delimiter='\t')
				writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames, delimiter='\t')

				# write column names row
				writer.writerow(dict((col,col) for col in reader.fieldnames))
				
				for row in reader:
					location = row['Location'].replace(':', '/')

					new_location = self.replace_filename(location)

					write_row = dict(row)
					write_row['Location'] = new_location
					writer.writerow(write_row)

					self.index += 1
					self.update_progress()			
				print('Done')

	def replace_filename(self, path):
		"""Copy file to output dir and return new file location which will be written to the new playlist file"""
		if os.path.exists(os.path.join(self.input_dir, path)):
			# relative path
			path = os.path.join(self.input_dir, path)
		else:
			# absolute path
			path = os.path.join('/Volumes', path)	
		
		if self.args.verbose:
			print("Copying:", path)
		try:
			shutil.copy(path, self.dirname)
		except IOError, e:
			print("ERROR copying file '%s' (IEError: %s)" % (path, str(e)))

		new_path = os.path.basename(path)
		return new_path

	def update_progress(self):
		"""Simple indicator that something is happening"""
		if self.index % 10 == 0:
			print('.', end='')
			sys.stdout.flush()

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description=
		"Read an iTunes-formatted m3u or txt playlist file, copy the music files, and create new portable playlist file")
	parser.add_argument('playlist')
	parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
	parser.add_argument('-d', '--directory', help='Directory to output to')
	parser.add_argument('-e', '--encoding', default='utf-16', help='Encoding for input file (txt only)')
	args = parser.parse_args()
	copier = PlaylistCopier(args)
	copier.copy()
