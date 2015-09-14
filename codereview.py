#coding=cp1251
import re
import sys
import subprocess
import os
import pprint

import Tkinter as tk # for clipboard
import tkFont

from patch_file import PatchFile
from codereview_rules import CodeReviewRules


class CodeReview:
	def __init__ (self, text = None):

		if not (text is None): 
			self.letter = text
		else: # from clipboard
			r = tk.Tk()
			r.withdraw()
			self.letter = r.clipboard_get()

		# Use this to 
		self.editor_exe  = r'C:\george\apps\npp.6.7\notepad++.exe'
		self.editor_exe  = r'c:\george\distr\AkelPad\AkelPad.exe'
		self.editor_exe  = r'c:\george\distr\vim\gvim.exe'

		self.cmdToroise  = r'"C:\Program Files\TortoiseSVN\bin\TortoiseProc.exe"'

		svn1             = r'"c:\Program Files\TortoiseSVN\bin\svn.exe"'
		svn2             = r'"c:\Program Files\SlikSvn\bin\svn.exe"'


		# not in use now
		self.cmdPatch   = r'"c:\george\apps\unixTools\usr\local\wbin\patch.exe"'
		#self.cmdMerge   = r'"C:\Program Files (x86)\WinMerge\WinMergeU.exe"'
		self.cmdMerge   = r'"C:\Program Files\Araxis\Araxis Merge\Merge.exe"'


		self.svn = svn1 if os.path.isfile(svn1) else svn2
		# cheching if editor.exe file exists or use notepad instead
		if not os.path.isfile (self.editor_exe):
			self.editor_exe = "notepad.exe"

		self.tmpFolder = r'c:\temp\codereview'
		if not os.path.exists (self.tmpFolder): # creating temp folder if its not exists
			os.makedirs (self.tmpFolder)

		self.applyPath = os.getcwd()
		(self.svn_path, self.svn_repo) = self.get_svn_path (self.applyPath)

		self.colsole = None
		self.window  = None
		self.lbFiles = None

		#print "repo = %s\npath=%s" % (self.svn_repo, self.svn_path)

		self.patch        = None
		self.deploy       = None
		self.rollback     = None
		self.patchFile    = None
		self.deployFile   = None
		self.rollbackFile = None
		self.patch_object = None

		self.deploy_files = []
		self.deploy_files_base = []
		self.patch_files  = []
		self.patch_files_base  = []
		self.diffResults  = []
		self.patched_files = []

		self.work()


	def parse(self):
		# only first found item by now...
		self.cprint ("Parsing clipboard text...")

		patch_result = re.findall('(https?\:\/\/svn.*?\.patch)', self.letter, re.I)
		self.patch = patch_result[0] if len (patch_result) > 0 else None
			
		deploy_result = re.findall('(https?\:\/\/svn.*?deploy.*?\.txt)', self.letter, re.I)
		self.deploy = deploy_result[0] if len (deploy_result) > 0 else None
			
		rollback_result = re.findall('(https?\:\/\/svn.*?rollback.*?\.txt)', self.letter, re.I)
		self.rollback = rollback_result[0] if len (rollback_result) > 0 else None

		self.cprint ("\tPatch:\t\t%s\n\tDeploy:\t\t%s\n\tRollback:\t\t%s" % (self.patch, self.deploy, self.rollback))


	def print_result(self):
		pass


	def get_svn_files(self):
		self.cprint("Getting files from SVN...")
		if not (self.patch is None):
			cmd = '%s export "%s" "%s" --force' % (self.svn, self.patch, self.tmpFolder)
			p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
			for l in p.stdout.readlines():
				if l.split()[0] == 'A':
					self.patchFile = ' '.join(l.split()[1:])
					break

		if not (self.deploy is None):
			cmd = '%s export "%s" "%s" --force' % (self.svn, self.deploy, self.tmpFolder)
			p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
			for l in p.stdout.readlines():
				if l.split()[0] == 'A':
					self.deployFile = ' '.join(l.split()[1:])
					break

		if not (self.rollback is None):
			cmd = '%s export "%s" "%s" --force' % (self.svn, self.rollback, self.tmpFolder)
			p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
			for l in p.stdout.readlines():
				if l.split()[0] == 'A':
					self.rollbackFile = ' '.join(l.split()[1:])
					break

		self.cprint("\tPatch local file:\t\t%s\n\tDeploy local file:\t\t%s\n\tRollback local file:\t\t%s" % (self.patchFile, self.deployFile, self.rollbackFile))


	def parse_deploy(self):
		with open(self.deployFile, u'r') as fl:
			for line in fl:
				if len(line) > 1:
					logging.info ("found deploy.txt item: [%s]" % line)
					self.deploy_files.append (line)
					self.deploy_files_base.append(os.path.basename(line.strip().lower()))


	def parse_patch(self):
		with open(self.patchFile, 'r') as fl:
			for line in fl:
				if line.startswith('Index: '):
					fileName = ("%s" % (re.findall('Index: (.*)', line)[0])).strip()
					self.patch_files.append(fileName)
					self.patch_files_base.append(os.path.basename(fileName.strip().lower()))


	def get_svn_path(self, dir):
		cmd = "%s info %s" % (self.svn, dir)
		#print cmd
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr = subprocess.PIPE)
		url = repo = None
		for l in p.stdout.readlines():
			if l.startswith('URL: '):
				url = re.findall('URL: (.*)', l)[0].strip()
			if l.startswith('Repository Root: '):
				repo = re.findall('Repository Root: (.*)', l)[0].strip()
		return (url, repo)	

	def get_local_file_name(self, svn_link):
		for f in self.patch_files:
			guess = self.svn_path + '/' + f
			if guess.strip().lower() == svn_link.strip().lower():
				return (self.applyPath + os.path.sep + f).replace('/', os.sep).replace('\\', os.sep)
		return None
		
	def cprint (self, text):
		print text
		try:
			if self.window:	self.console.insert (tk.END, text + "\n")
		except TclError:
			pass # supress errors
		finally:
			pass # supress errors


	def prepare_gui(self):
		font = tkFont.Font(family='Ubuntu Mono', size = 6)

		self.window = tk.Tk()
		self.window.geometry("800x600")
		self.window.title("CodeReview Helper :: deploy.txt")

		self.window.bind("<Escape>", lambda e: e.widget.quit())

		scrollbar = tk.Scrollbar(self.window, orient="vertical")
		self.lbFiles = tk.Listbox(self.window, width=50, height=50, yscrollcommand=scrollbar.set, font=font)
		scrollbar.config(command=self.lbFiles.yview)		
		self.console = tk.Text (self.window, font=font)

		self.console.pack (side="top", expand = True, fill="both")
		scrollbar.pack(side="right", fill="y")
		self.lbFiles.pack(side="left", fill="both", expand=True)

		self.lbFiles.focus_set()

		self.lbFiles.bind("<Double-Button-1>", self.onSelectAction)
		self.lbFiles.bind("<Return>", self.onSelectAction)


	def display_gui(self):
		pass

		for item in self.deploy_files:
			self.lbFiles.insert(tk.END, item)

		self.window.mainloop()


	def onSelectAction (self, event):
		widget = event.widget
		selection=widget.curselection()

		logging.info ('Trying to open DIFF for selected item [%s]' % (widget.get(selection[0])).strip())

		if len (selection) > 0:
			value = widget.get(selection[0]) # full deploy.txt file name... Wounder what to do with that			
			local_file = self.get_local_file_name (value)
#!!!!			#print "Trying to open diff for file '%s' ... %s" % (value, local_file)
			# cheching for new file...
			l, r = self.get_svn_path (local_file)			
			if not (local_file is None):
				# preverification
				self.cprint ("%s (%s):" % (value.strip(), local_file))
				cr = CodeReviewRules (local_file)
				#self.cprint (cr)
				if not cr.check_all():
					self.cprint ("\tPreverification results: \n%s" % cr.get_results("\t\t"))
				else:
					self.cprint ("\tPreverification complete")

				if not (l is None): # if file exists in svn
					cmd = "%s /command:diff /path:\"%s\"" % (self.cmdToroise, local_file)
					pa = subprocess.Popen (cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
					pa.wait()
				else: # if its a new file - launch editor instead of DIFF
					cmd = "\"%s\" \"%s\"" % (self.editor_exe, local_file)
					pa = subprocess.Popen (cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
					pa.wait()
				# copiing file name to clipboard
				#r = tk.Tk()
				#r.withdraw()
				#r.clipboard_clear()
				#r.clipboard_append(value)
				#r.destroy()






	def check_files(self):
		self.diffResults = []

		for f in self.patch_files:
			if not os.path.basename(f.strip()).lower() in self.deploy_files_base:
				self.diffResults.append ({'filename': f.strip(), 'reason': 'not found in deploy file'})

		for f in self.deploy_files:
			if not os.path.basename(f.strip()).lower() in self.patch_files_base:
				self.diffResults.append ({'filename': f.strip(), 'reason': 'not found in patch file'})
		return True if len(self.diffResults) == 0 else False

	def printdiff(self):
		# printing diff between patch and deploy file lists
		self.cprint ("\nDeploy.txt items not found in .patch file: ")
		for f in [f['filename'] for f in self.diffResults if f['reason'] == 'not found in patch file']:
			self.cprint ("\t%s" % f)
		self.cprint ("\n.patch items not found in deploy.txt file: ")
		for f in [f['filename'] for f in self.diffResults if f['reason'] == 'not found in deploy file']:
			self.cprint ("\t%s" % f)


	def apply_patch_exe(self):
		print "\nPatching files:"
		rejectFile = self.tmpFolder + os.path.sep +  'reject.file'
		cmd = '"%s" -p0 --unified --force -r "%s" --no-backup-if-mismatch < "%s"' % (self.cmdPatch, rejectFile, self.patchFile)
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		for l in p.stdout.readlines():
			self.cprint (l)
			if (l.find ('patching file') != -1):
				fName = "%s\\%s" % (self.applyPath, re.findall('`(.*)\'', l)[0])
				#print "\t%s\n\t\t%s" % (l, fName)
				self.patched_files.append (fName)
		self.cprint ("\n")


	def revert_files_exe(self):
		self.cprint ("\nReverting files:")
		for l in self.patched_files:
			self.cprint ("\t- %s" % l)
			cmd = '%s revert "%s"' % (self.svn, l)		
			pa = subprocess.Popen (cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			pa.wait()

	def apply_patch(self):
		#self.patch_object = patch.fromfile(self.patchFile)
		#self.patch_object.apply(0, root = self.applyPath)
		self.patch_object = PatchFile (self.patchFile, root = self.applyPath)
		self.patch_object.apply()


	def revert_files(self):
		self.cprint ("\nReverting files...")
		#self.patch_object.revert(0, root = self.applyPath)
		if not self.patch_object is None:
			self.patch_object.revert()


	def delete_tmp_files(self):
		if self.patchFile:
			if os.path.exists(self.patchFile):
				os.remove(self.patchFile)
		if self.deployFile:
			if os.path.exists(self.deployFile):
				os.remove(self.deployFile)
		if self.rollbackFile:
			if os.path.exists(self.rollbackFile):
				os.remove(self.rollbackFile)


	def work(self):
		self.prepare_gui()
		#parsign input to files
		self.parse()

		exit = False

		if self.patch is None:
			self.cprint ("\nERROR: No patch file found!")
			exit = True
		if self.deploy is None:
			self.cprint ("\nERROR: No deploy file found!")
			exit = True

		if not exit:
			self.get_svn_files()
			self.parse_deploy()
			self.parse_patch()

			if not self.check_files():
				self.cprint ("\n\nErrors while checking deploy and patch files:")
				self.printdiff()

		try:
			if not exit:
				self.apply_patch()
			try:
				self.display_gui()
			except KeyboardInterrupt:
				print "Interrupted... trying to exit carefully..."
				self.window.quit()

		finally:
			if not exit:				
				self.revert_files()
				self.delete_tmp_files()



if __name__=='__main__':	
	import logging
	logging.basicConfig(format = '%(levelname)8s %(message)s', level = logging.INFO)

	#logging.basicConfig(format='%(levelname)8s %(message)s', level=logging.DEBUG)
	CodeReview().print_result()
