#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import subprocess
import os

def svnlog():
	buf = os.popen("svn log -l 100").read()
	print buf

class CommandExcute():#threading.Thread):
	def __init__(self, command, onDone, workingDir ="", **kwargs):
		#threading.Thread.__init__(self)
		self.command = command
		self.onDone = onDone
		self.workingDir = workingDir or os.getcwd()
		self.stdin = kwargs and kwargs["stdin"] or None
		self.stdout = kwargs and kwargs["stdout"] or subprocess.PIPE
		self.kwargs = kwargs

	def run(self):
		try:
			# Ignore directories that no longer exist
			if not os.path.isdir(self.workingDir):
				return

			shell = os.name == 'nt'
			if self.workingDir != "":
				os.chdir(self.workingDir)
			proc = subprocess.Popen(self.command,
				stdout=self.stdout, stderr=subprocess.STDOUT,
				stdin=subprocess.PIPE,
				shell=shell, universal_newlines=True)
			output = proc.communicate(self.stdin)[0]
			if not output:
				output = ''
			if self.onDone:
				self.onDone(output)
		except subprocess.CalledProcessError, e:
			#main_thread(self.on_done, e.returncode)
			raise e
		except OSError, e:
			raise e

class SvnCommand(object):
	def run_command(self, command, callback=None, **kwargs):
		callback = callback or self.generic_done
		thread = CommandExcute(command, callback, **kwargs)
		#thread.start()
		thread.run()
	def generic_done(self, result):
		print result

if __name__ == "__main__":
	a = SvnCommand()
	a.run_command(["svn", "info"])
