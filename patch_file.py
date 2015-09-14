import re
import os
import logging
import warnings

class Item:
	def __init__(self):
		self.hunks     = []
		self.indexName = ''
		self.oldName   = ''
		self.newName   = ''
		self.isNewFile = False

	def __eq__(self, other):
		result = self.indexName == other.indexName
		result &= self.oldName == other.oldName
		result &= self.newName == other.newName
		result &= len(self.hunks) == len (other.hunks)
		result &= self.isNewFile == other.isNewFile
		return result

	def getHunk (self, line_number, revert = False):
		for h in self.hunks:
			if revert:
				f = h.new_number['from']
				t = h.new_number['from'] + h.new_number['len']
			else:
				f = h.old_number['from']
				t = h.old_number['from'] + h.old_number['len']
			if line_number >= f and line_number < t:
				return h
		return None


class Hunk:
	def __init__(self):
		self.old_number = {}
		self.new_number = {}
		self.old_lines  = []
		self.new_lines  = []

	def get_new_lines (self, revert = False):
		return self.old_lines if revert else self.new_lines

	def get_old_lines (self, revert = False):
		return self.new_lines if revert else self.old_lines

	def get_new_number (self, revert = False):
		return self.old_number if revert else self.new_number

	def get_old_number (self, revert = False):
		return self.new_number if revert else self.old_number



class PatchFile:
	def __init__(self, patch_file, root = None):
		#self.hunk_pattern = r'^@@\s-\s?(\d+\s?,\d?)\s?\+(\d+\s?,\d?)\s?@@.*$' # pattern to find new hunk "@@ -l,s +l,s @@ optional section heading"
		self.hunk_pattern = r'^@@\s-\s?(\d+\s*?,?\d*?)\s?\+(\d+\s*?,?\d*?)\s*?@@.*$'
		self.nn_pattern = r'^\+\+\+ (.*?)\t'
		self.on_pattern = r'^--- (.*?)\t'

		self.patchfile = patch_file
		self.root      = os.getcwd() if root is None else root
		self.items     = []
		self.folders   = []

		self.parse()

	def _compare_hunks (self, x, y):
		return x.old_number['from'] - y.old_number['from']

	def parse(self):
		expect_delimiter_line = False
		expect_old_name       = False
		expect_new_name       = False
		item = None
		hunk = None
		line_number = 0
		for line in open(self.patchfile):
			line_number += 1
			logging.debug ('parsing line [%d]: %s' % (line_number, line))

			if expect_delimiter_line:
				logging.debug ('expecting delimiter')
				if line.startswith('====='):
					logging.debug ('delimiter found')
					expect_old_name = True
					expect_delimiter_line = False
					continue
				else:
					print 'error in patch file: expecting delimiter line, found: %s' % line 
					continue

			if expect_old_name:
				logging.debug ('expecting old name')
				if line.startswith('---'):
					logging.debug ('old name found in line %d: %s' % (line_number, line))
					item.oldName = (re.findall(self.on_pattern, line)[0]).strip()
					expect_old_name = False
					expect_new_name = True
					continue
				else:
					print "error in patch file: expecting old name, found: %s" % line
					continue

			if expect_new_name:
				logging.debug ('expecting new name')
				if line.startswith('+++'):
					logging.debug ('new name found in line %d: %s' % (line_number, line))
					item.newName = (re.findall(self.nn_pattern, line)[0]).strip()
					expect_old_name = False
					expect_new_name = False
					continue
				else:
					print "error in patch file: expecting new name, found: %s" % line
					continue


			if line.startswith('Index: '):
				logging.debug ('new Item found at line %d. Old item = %s' % (line_number, item is None))
				# 1. saving old info as new Item
				if not (item is None):
					if not (hunk is None):
						item.hunks.append(hunk)
						hunk = None
					if item not in self.items:
						item.hunks = sorted (item.hunks, cmp = self._compare_hunks)
						self.items.append (item)
				# 2. staring new Item
				item = None
				item = Item()
				item.indexName = line

				expect_delimiter_line = True
				expect_old_name       = False
				expect_new_name       = False

				continue

			# hunks...
			h = re.match (self.hunk_pattern, line)
			if h:
				logging.debug ('new hunk found at line %d. To Item [%s]' % (line_number, item.indexName))
				# hunk found...
				if not (hunk is None):
					item.hunks.append (hunk)
					hunk = None
				hunk = Hunk()
				old = h.group(1)
				new = h.group(2)
				hunk.old_number['from'] = int(old.split(',')[0] if ',' in old else old)
				hunk.old_number['len']  = int(old.split(',')[1] if ',' in old else 1)
				hunk.new_number['from'] = int(new.split(',')[0] if ',' in new else new)
				hunk.new_number['len']  = int(new.split(',')[1] if ',' in new else 1)
				if old == '0,0':
					item.isNewFile = True
				continue

			# hunk_contents
			if not (hunk is None):
				if line.startswith(' ') | line.startswith ('-'):
					hunk.old_lines.append (line[1:])
				if line.startswith(' ') | line.startswith ('+'):
					hunk.new_lines.append (line[1:])
			else:
				print 'Error: trying to add lines with no Hunk active: %s ' % line

		# final check
		if len(hunk.old_number) > 1:
			item.hunks.append(hunk)
		if len(item.indexName) > 1:
			item.hunks = sorted (item.hunks, cmp = self._compare_hunks)
			self.items.append(item)


	def makedirs (self, path):
		if not os.path.exists (path):
			parent = os.path.dirname(path)
			if not os.path.exists (parent):
				self.makedirs (parent)
			logging.info ('creating folder : %s' % path)				
			os.mkdir (path)
			i = self.folders.index(parent) if parent in self.folders else len(self.folders)
			self.folders.insert (i, path)

	def removedirs(self):
		for f in self.folders:
			logging.info('removing folder [%s]' % f)
			os.rmdir(f)

	def _apply (self, revert):
		# saving current folder & changing it to ROOT folder
		prevdir = os.getcwd()
		os.chdir(self.root)
		action = 'revert' if revert else 'apply'

		for item in self.items:
			if item.isNewFile:
				filename = os.path.join (self.root, item.newName)
				logging.info ("%s new file %s" % (action, filename))
				if revert:
					if os.path.exists(filename):
						os.remove(filename)
				else:
					path = os.path.dirname (filename)
					self.makedirs(path) # create folder if its not exists
					f = open (filename, 'w')
					# write hunks to file
					for hunk in item.hunks:
						f.write(''.join(hunk.new_lines))
					f.close() # closing file
			else: # if editign file
				newfilename = os.path.join (self.root, item.newName)
				oldfilename = os.path.join (self.root, item.oldName)
				logging.info ("%s patch to file [%s] to [%s]" % (action, newfilename, oldfilename))
				newfile = []
				skip = -1
				h = None
				for n, l in enumerate(open(oldfilename, 'r')):
					n += 1 # enumerate generates line number from zero
					logging.debug('line %3d\t%s' % (n, l.strip()))
					if skip > 0:
						old = h.get_old_lines(revert)[-skip]
						if old != l:
							warnings.warn('Error patching item [%s]: line %d: file differs from patch' % (item.indexName, n) )
							break
						logging.debug('like %3d\tcheck & skip = %d; old = %s' % (n, skip, old))
						skip -= 1
						continue

					h = item.getHunk(n, revert)
					if not (h is None):
						logging.debug('line %3d\t!!found hunk: %s; skip = %d; old-len = %d; new-len = %d' % (n, h, h.get_old_number(revert)['len'], len(h.get_old_lines(revert)), len(h.get_new_lines(revert))))
						skip  = h.get_old_number(revert)['len'] - 1
						lines = h.get_new_lines(revert)
						continue
					if skip == 0:
						newfile.extend (lines)
						lines = []
						h = None

					if h is None:
						newfile.append(l)
				# delete old file
				# create new file
				os.remove(oldfilename)
				f = open(newfilename, 'w')
				f.write(''.join(newfile))
				f.close()
		# removing dirs
		if revert:
			self.removedirs()
		# return current folder to original setting
		os.chdir (prevdir)		

	def apply(self):
		self._apply(revert = False)

	def revert(self):
		self._apply(revert = True)


	def __str__(self):
		res = 'Item count in patch: %d\n' % len (self.items)
		for item in self.items:
			res += 'Item [%s] (Hunks: %d): %s\n\tOldName: %s\tNewName: %s\n' % ('New' if item.isNewFile else 'Edit', len(item.hunks), item.indexName, item.oldName, item.newName)
			for h in item.hunks:
				res += '\tHunk from %s to %s\n' % (h.old_number, h.new_number)
			#	res += '\t\t from:\n'
			#	for l in h.old_lines:
			#		res += '\t\t\t%s' % l
			#	res += '\t\t to:\n'
			#	for l in h.new_lines:
			#		res += '\t\t\t%s' % l

		return res



if __name__ == '__main__':
	test_file = r'c:\_tmp\_patches\DIASOFT-7097.patch'
	test_file = r'c:\_tmp\_patches\ReportUK.patch'
	test_file = r'c:\george\svn\Diasoft\AllScripts\Servers\XO\patches\20150306_COF-518.patch'
	test_file = r'c:\_tmp\_patches\20150707_DIASOFT-6885.patch'
	test_file = r'c:\george\tasks\ECC-10\test.patch'
	test_file = r'c:\_tmp\_patches\20150717_DIASOFT-7112.patch'
	root = r'c:\george\svn\Diasoft\AllScripts\Servers\XO\trunk'

	logging.basicConfig(level = logging.INFO)
	#logging.basicConfig(level = logging.DEBUG)

	pf = PatchFile (test_file, root = root)
	pf.apply()

	q = raw_input('Press any key to revert')

	pf.revert()

	#print pf

	
