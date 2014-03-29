#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
import curses
import curses_ext
import logging
import svnclient
from locale import *
import time
import pysvn

global app
global client
username = None
password = None

def date_format(date):
	return time.strftime('%Y-%m-%d %A %X %Z',time.localtime(date))

def init_content_window(window):
	global app
	window.show(True)
	global end_revision
	global log_author
	end_revision = None
	log_author = None

	def cursor_changed(win):
		global log_author
		cursor = win.get_cursor()
		info = win.get_line_info(cursor)
		if not info: return

		winFileList = app.get_window("filelist")
		winFileList.clear()
		winFileList.show(True)
		log = info["log"]
		for changePath in log.changed_paths:
			winFileList.add_line_str(changePath.path, log=log, path=changePath.path)
		if (win.get_rows() - win.get_cursor()) < 5:
			cmd_log(win, log_author)

	def show_user_log(win):
		cursor = win.get_cursor()
		info = win.get_line_info(cursor)
		if not info: return
		log = info["log"]
		logging.debug("show user log=%s", log.author)
		win.clear()
		cmd_log(win, log.author)


	def cmd_log(win, author=None):
		global log_author
		global end_revision
		log_author = author
		#win.set_title("svn log")
		logging.debug("cmd log")
		logs, end_revision = client.log(end_revision, log_author)
		if not len(logs): return
		for log in logs:
			message = "%s %s %s"%(log.author, date_format(log.date), log.message)
			line = curses_ext.line()
			line.append_region(date_format(log.date), 40, "TEXT_BLUE")
			line.append_region(log.author, 15, "TEXT_RED")
			line.append_region("%d"%log.revision.number, 15, "TEXT_BLUE")
			line.append_region(log.message, 50, "TEXT_RED")
			win.add_line(line, log=log)

	def on_key_enter(win):
		#resultWin.clear()
		cursor = win.get_cursor()
		info = win.get_line_info(cursor)
		if not info: return

		win = app.get_window("result")
		win.clear()
		win.show(True)
		log = info["log"]
		#prev = pysvn.Revision(pysvn.opt_revision_kind.committed)
		prev = pysvn.Revision(pysvn.opt_revision_kind.number, log.revision.number - 1)
		diff_text = client.diff(log.revision, prev)
		for text_line in diff_text.splitlines():
			# logging.debug("diff_text = %s", text_line)
			win.add_line_str(text_line)

	def save_log(win):
		win.save()

	def hook(self, ch):
		if ch == 'q':
			app.quit()
		elif ch == 'd':
			cmd_log(self)
		elif ch == 's':
			save_log(self)
		elif ch == 'u':
			show_user_log(self)
		elif ch == "KEY_ENTER":
			on_key_enter(self)
	window.bind_keys(['q', 's', 'd', 'u', 'KEY_ENTER'], hook)
	window.bind_cursor_changed(cursor_changed)

def init_result_window(window):
	def hook(self, ch):
		if ch == 'q':
			self.show(False)

	window.bind_keys(['q'], hook)

def init_filelist_window(window):
	def cursor_changed(win):
		cursor = win.get_cursor()
		info = win.get_line_info(cursor)
		if not info: return
		log = info["log"]
		path = info["path"]

		resultWin = app.get_window("result")
		resultWin.clear()
		resultWin.show(True)
		resultWin.add_line_str(path)

	def hook(self, ch):
		if ch == 'q':
			self.show(False)

	window.bind_keys(['q'], hook)
	window.bind_cursor_changed(cursor_changed)

def login():
	global username
	global password
	global client

	win = app.new_edit("input", 0.5, 0.53, 0.4, 0.6)
	win.active(True)
	def on_result_password(edit, result):
		global password
		password = result
		edit.show(False)

	def on_result_username(edit, result):
		global password
		global username
		username = result
		if not password:
			edit.set_prefix("password:")
			edit.on_result(on_result_password)
			edit.on_active(True)

	win.on_result(on_result_username)
	win.set_prefix("username:")
	win.on_active()
	#logging.debug("username:%s,password:%s", username, password)
	client = svnclient.client(username, password)

def run():
	global app

	#init color scheme
	colorScheme = app.get_color_scheme()
	colorScheme.create_color("TEXT_BLUE", curses.COLOR_BLUE, -1)
	colorScheme.create_color("TEXT_RED", curses.COLOR_RED, -1)


	#init windows
	win = app.new_window("content", 0, 40)
	init_content_window(win)
	win.set_title("content")
	win.active(True)

	win = app.new_window("result", 0.5, 0.5)
	init_result_window(win)
	win.set_title("result")

	win = app.new_window("filelist", 0, 0.4, 0.7)
	win.border()
	init_filelist_window(win)
	win.set_title("filelist")

	#enter loop
	app.loop()

def end(err):
	global app
	app.cleanup_curses()
	tb = traceback.print_exc()
	if tb:
		print tb
	if err:
		print err


if __name__ == "__main__":
	global app
	setlocale(LC_ALL,"")
	app = curses_ext.app()
	error = None
	try:
		login()
		run()
	except Exception, err:
		error = err
	end(error)
