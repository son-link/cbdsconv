#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  cbdsconv.py
#
#  Copyright 2012 Alfonso Saavedra "Son Link" <sonlink.dourden@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
import Image, zipfile, rarfile

from os import access, path, R_OK, W_OK, makedirs, walk, remove
from sys import argv
from shutil import rmtree, move, copy
from subprocess import Popen

class CBDS():

	def __init__(self):
		self.destdir = ''
		self.tmpdir = '/tmp/cdbs'
		self.cdbsdirs = ['IMAGE', 'SMALL_N', 'THMB_N', 'SMALL_R', 'THMB_R', 'NAME']
		self.cbdsname = ''
		self.totalpags = 0

		for comic in argv[1:]:
			for d in self.cdbsdirs:
				if not path.exists(self.tmpdir+'/'+d):
					makedirs(self.tmpdir+'/'+d)

			self.destdir = path.dirname(comic)
			if path.isdir(comic):
				self.cbdsname = path.basename(comic)
				print 'Convirtiendo:', self.cbdsname
				self.fromDir(comic)

			elif path.isfile(comic):
				tempdir = self.tmpdir+'/temp'
				if not path.exists(tempdir):
					print 'Creando directoriotemporal'
					makedirs(tempdir)

				self.cbdsname = path.splitext(path.split(comic)[1])[0]
				print 'Convirtiendo:', self.cbdsname
				try:
					zip = zipfile.ZipFile(comic)
					zip.extractall(tempdir)
					self.fromDir(tempdir)

				except zipfile.BadZipfile:
					if rarfile.is_rarfile(comic):
						rar = rarfile.RarFile(comic)
						if rar.needs_password():
							try:
								passwd = raw_input('Contraseña del RAR: ')
								rar.setpassword(passwd)
								rar.extractall(tempdir)
								self.fromDir(self.tmpdir)
							except rarfile.RarCRCError:
								print 'Contraseña del rar invalida o archivo dañado'

						else:
							rar.extractall(tempdir)
							self.fromDir(self.tmpdir)
					elif comic.endswith('.pdf'):
						pipe = 'pdfimages -j %s %s/' % (comic, tempdir)
						cmd = Popen(pipe.split())
						cmd.wait()
						self.fromDir(self.tmpdir)

					else:
						print 'Archivo no valido o dañado'

	def fromDir(self, directory):
		pags = []
		for root,dirs,files in walk(directory):
			for file in [f for f in files]:
				try:
					Image.open(path.join(root, file))
					pags.append(path.join(root, file))
				except:
					pass
		pags.sort()
		i = 1
		scales = ((700,1054), (127,192), (30,46), (256,169), (62,40))
		for p in pags:
			try:
				img = Image.open(p)
				for m in range(0, 5):
					if m == 3:
						img = img.rotate(-90)

					size = self.calc_size(img, scales[m])
					width = size[0]
					height = size[1]
					dest_img = img.resize((width, height), Image.ANTIALIAS)
					dest_img.save('%s/%s/%i.jpg' % (self.tmpdir, self.cdbsdirs[m], i))

				f = open('%s/NAME/%i.txt' % (self.tmpdir, i), 'w')
				f.write(p)
				f.close()
			except:
				pass

			i += 1

		self.totalpags = i

		if path.exists(self.tmpdir+'/temp'):
			rmtree(self.tmpdir+'/temp')

		self.writeINI()
		self.makeCDBS()

	def resize(mode, img):
		width = size[0]
		height = size[1]
		img = img.resize((width, height), Image.ANTIALIAS)
		img.save()

	def calc_size(self, img, size):
		width = size[0]
		height = size[1]

		if img.size[0] > img.size[1]:
			height = width * img.size[1] / img.size[0]
		elif img.size[1] > img.size[0]:
			width = height * img.size[0] / img.size[1]
		else:
			if width > height:
				width = height * img.size[0] / img.size[1]
			else:
				height = width * img.size[1] / img.size[0]

		return [width, height]

	def makeCDBS(self):
		print 'Comprimiendo: '+self.cbdsname+'.cbds'
		zip = zipfile.ZipFile(self.destdir+'/'+self.cbdsname+'.cbds', 'w', zipfile.ZIP_DEFLATED)
		rootlen = len(self.tmpdir) + 1
		for base, dirs, files in walk(self.tmpdir):
			for file in files:
				fn = path.join(base, file)
				zip.write(fn, fn[rootlen:])
		#rmtree(self.tmpdir)

	def writeINI(self):
		ini = """; ComicBookDS ini file
; 1st line displayed in the credits (usually the ComicBook name)
CbCredits1 = %s
; 2nd line displayed in the credits (usually the ComicBook author)
CbCredits2 = Unknown
; 3rd line displayed in the credits (usually the ComicBook provider)
CbCredits3 = Unknown
; Left To Right reading mode [RightToLeft=0,LeftToRight=1]
LeftToRight = 1
; The number of pages contained in this comic book
NbPages = %i
; The compatibility version of this comic book
Version = 200
iHeight = 1400
iQuality = 90
iSize = 860000
iWidth = 700
oHeight = 192
oQuality = 90
oSize = 0
oWidth = 256
thHeight = 46
thQuality = 90
thSize = 0
thWidth = 62""" % (self.cbdsname, self.totalpags)
		f = open(self.tmpdir+'/ComicBookDS_book.ini', 'w')
		f.write(ini)
		f.close()

if __name__ == '__main__':
	if len(argv) >= 2:
		CBDS()
	else:
		print 'Debe de indicar al menos una carpeta o archivo'

