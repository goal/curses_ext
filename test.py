#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
import curses
import curses_ext
import logging

logging.basicConfig(level=logging.DEBUG,
		format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                    filename='/tmp/svnview.log',
                    filemode='w')

global app


def add_line(win, str, process):
	win.add_line(str, process = process)

def deal_line(win, line):
	(str, info) = win.get_line(line)
	if not info: return
	if not info["process"]: return
	info["process"](win, str)

def cmd_df(showWin, resultWin):
	showWin.set_title("df info")
	def process(win, line):
		#resultWin.clear()
		resultWin.show(True)
		resultWin.add_line(line)

	for line in os.popen("df").read().splitlines():
		add_line(showWin, line, process)

def init_content_window(window):
	global app
	window.show(True)

	def hook(self, ch):
		if ch == 'q':
			app.quit()
		elif ch == 'd':
			cmd_df(self, app.get_window("result"))
		elif ch == 'j':
			self.cursor_shift(1)
		elif ch == 'k':
			self.cursor_shift(-1)
		elif ch == "KEY_ENTER":
			deal_line(self, self.get_cursor())
	window.bind_keys([], hook)

def init_result_window(window):
	def hook(self, ch):
		if ch == 'q':
			self.show(False)
		elif ch == 'j':
			self.cursor_shift(1)
		elif ch == 'k':
			self.cursor_shift(-1)

	window.bind_keys([], hook)

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
	app = curses_ext.app()
	error = None
	try:
		run()
	except Exception, err:
		logging.error(err)
		error = err
	end(error)
