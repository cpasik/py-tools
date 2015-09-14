#coding=cp1251
import re
import sys
import os
from pprint import pprint


class Settings():
	common_pattern              = 'trunk%scommon' % (os.sep)	
	script_pattern              = 'trunk%s_scripts' % (os.sep)

	object_name_pattern         = r'create\s+(\w+)\s+([\w#@]+(\.\w+)?)(;(\d+))?'
	object_name_pattern_flags   = re.I | re.M

	comments_1_pattern          = '/\*.*?\*/'
	comments_1_pattern_flags    = re.I | re.DOTALL | re.M

	comments_2_pattern          = '--.*?\n'
	comments_2_pattern_flags    = re.I

	special_chars_pattern       = '[\t]'
	special_chars_pattern_flags = re.I | re.M



class CodeReviewRules():
	def __init__ (self, fileName, isCommon = None):
		self.fileName = fileName		
		with open (fileName, 'r') as f:
			self.contents_all = f.read()


		self.contents = self.contents_all.split('\n')
		self.contents_no_comments = self.contents_all
		self.contents_no_comments = re.sub(re.compile (Settings.comments_1_pattern, Settings.comments_1_pattern_flags), '', self.contents_no_comments)
		self.contents_no_comments = re.sub(re.compile (Settings.comments_2_pattern, Settings.comments_2_pattern_flags), '', self.contents_no_comments)


		if isCommon is None:
			if self.fileName.lower().find (Settings.common_pattern) != -1:
				self.isCommon = True
			else:
				self.isCommon = False
		else:
			self.isCommon = isCommon

		if self.fileName.lower().find (Settings.script_pattern) != -1:
			self.isScript = True
		else:
			self.isScript = False

		self.object_type = ''
		self.object_name = ''
		self.objects = []
		self.db = []

		self.result = []
		self.bResult = True

		self.parse()

	def __str__(self):
		return 'CodeReviewRules:\n\tfileName\t=>\t%s\n\tisCommon\t=>\t%s\n\tisScript\t=>\t%s\n\tObjectType\t=>\t%s\n\tObjectName\t=>\t%s\n\tDataBases\t=>\t%s\n' % (self.fileName, self.isCommon, self.isScript, self.object_type, self.object_name, self.db)

	def parse(self):
		objs = re.findall(Settings.object_name_pattern, self.contents_no_comments, Settings.object_name_pattern_flags)

		for o in objs:
			object_type   = o[0].lower()
			object_name   = o[1]
			object_status = 'temp' if object_name.startswith('#') or object_name.startswith('@') else 'normal'
			object_number = o[4]
			obj = {'type': object_type, 'name': object_name, 'status': object_status, 'number': object_number}
			self.objects.append (obj)

		#print '\n\n'
		#pprint (self.objects)
		#print '\n\n'

		self.get_self_name()

	def get_self_name(self):
		for obj in self.objects:
			if obj['status'] == 'temp':
				continue
			self.object_type = obj['type']
			self.object_name = obj['name']
			break

	def add_message (self, proc, msg):
		self.result.append ({'proc': proc, 'message': msg})

	def get_results (self, prechar = ''):
		str = ''
		for res in self.result:
			str += "%s- %s (%s)\n" % (prechar, res['message'], res['proc'])
		return str

	def check_all(self):		
		self.bResult = self.bResult and self.check_object_name()
		self.bResult = self.bResult and self.check_db()
		self.bResult = self.bResult and self.check_special_chars()
		self.bResult = self.bResult and self.check_grant()
		self.bResult = self.bResult and self.check_folder()
		return self.bResult


	def check_db(self):
		db_line = self.contents[0]
		go_line = self.contents[1]
		r = True
		if self.isCommon:
			self.db = re.findall('DB=(.*?)[,*]', db_line)
		else:
			self.db = re.findall('use (.*)', db_line, re.IGNORECASE)
			if go_line.strip().lower() != 'go':
				r = False
				comment = 'Second line after DB define must be "GO"'
				self.add_message('check_db', comment)

		if len(self.db) == 0:
			r = False
			comment = 'First line in script must be USE <DB>. %s' % comment
			self.add_message('check_db', comment)

		return r
		

	def check_special_chars(self):
		spc = re.findall (Settings.special_chars_pattern, self.contents_all, Settings.special_chars_pattern_flags)
		r = True
		if len (spc) > 0:
			r = False
			comment = 'TAB symbols found in source code. Please, check'
			self.add_message('check_special_chars', comment)
		return r		


	def check_object_name(self):
		if self.isScript: 
			return True # не проверяем для скриптов, Так как нет объектов
		fName = os.path.splitext(os.path.basename(self.fileName))[0]

		r = True

		if fName.strip().lower() != self.object_name.strip().lower():
			r = False
			comment = "Object name doesn't match file name (fileName = %s; objectName = %s)" % (fName, self.object_name)
			self.add_message ('check_object_name', comment)

		if len(self.object_name.split('.')) != 2:
			r = False
			comment = "Object name must include schema name (like dbo.)"
			self.add_message ('check_object_name', comment)
		
		return r

	def check_folder(self):
		r = True
		if self.isScript:
			return True
		if self.isCommon:
			pattern = 'trunk%scommon' % (os.sep)
		else:
			pattern = 'trunk%s%s' % (os.sep, self.db[0].strip())

		if self.fileName.lower().find (pattern.lower().strip()) == -1:
			r = False
			if self.isCommon:
				comment = "Object path must contain [%s], because of multiple db (db = %s)" % (pattern, self.db) 
			else:
				comment = "Object path must contain [%s], because DB in file = [%s]" % (pattern, self.db[0])
			self.add_message ('check_folder', comment)

		return r


	def check_grant(self):
		return True






if __name__ == '__main__':
	if len(sys.argv) > 1:
		temp_file = sys.argv[1]
	else:
		temp_file = r'c:\george\tasks\ECC-10\PORTF\dbo.pEMIR_CB_Coupon_load.sql'
	cr = CodeReviewRules (temp_file)
	result = cr.check_all()
	print cr
	print 'Global check results: %s' % result
	print cr.get_results()

