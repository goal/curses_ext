#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import curses.textpad
import logging
import os

logging.basicConfig(level=logging.DEBUG,
		format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                    filename='/tmp/svnview.log',
                    filemode='w')
class line:
	regions = []
	def __init__(self):
		self.regions = []
	def append_region(self, str, endCol = 0, color = "TEXT"):
		self.regions.append((color, endCol, str.replace("\n", "")))
	def get_regions(self):
		return self.regions

class window_base:
	app = None
	screen = None
	showed = True
	actived = False
	colorScheme = None
	dirty = True
	name = ""
	key_hook_tbl = {}
	cursor_changed = None
	def __init__(self, app, screen, colorScheme):
		self.app = app
		self.screen = screen
		# self.screen.leaveok(0)
		# self.screen.move(20, 20)

		self.showed = True
		self.actived = False
		self.colorScheme = colorScheme
		self.dirty = True
		self.key_hook_tbl = {}

	def set_name(self, name):
		self.name = name

	def get_name(self):
		return self.name

	def show(self, bshow):
		if self.showed == bshow: return
		self.showed = bshow
		self.app.adjust_view()
		self.dirty = True
		self.app.view_notice_active(self, self.is_active())

	def active(self, bactive, bnotice = True):
		self.actived = bactive
		self.dirty = True
		if bnotice:
			self.app.view_notice_active(self, self.is_active())

	def is_show(self):
		return self.showed

	def is_active(self):
		return self.showed and self.actived

	def on_active(self):
		return

	def bind_keys(self, keys, hook):
		for key in keys:
			if not self.key_hook_tbl.has_key(key):
				self.key_hook_tbl[key] = []
			self.key_hook_tbl[key].append(hook)
	
	def on_key_input(self, ch):
		return False

	def dispatch_event(self, ch):
		if self.key_hook_tbl and self.key_hook_tbl.has_key(ch):
			for fun in self.key_hook_tbl[ch]:
				fun(self, ch)
			return True
		
		return self.on_key_input(ch)

	def draw(self):
		self.screen.clear()
		self.screen.refresh()

	def resize(self, maxRow, maxCol = None):
		(lastRow, lastCol) = self.screen.getmaxyx() 
		maxCol = maxCol or lastCol
		if maxRow <= 0 or maxCol <= 0 or (maxRow == lastRow and maxCol == lastCol):
			return False
		self.screen.resize(maxRow, maxCol or lastCol)
		return True

class window(window_base):
	on_cursor_changed = None
	def __init__(self, app, screen, colorScheme):
		window_base.__init__(self, app, screen, colorScheme)

		(maxRow, maxCol) = self.screen.getmaxyx() 
		#title line
		self.isBorder = False
		self.beginRow = 0
		self.endRow = maxRow
		self.clear()
	
	def border(self):
		self.isBorder = True
		(maxRow, maxCol) = self.screen.getmaxyx() 
		self.beginRow = 1
		self.endRow = maxRow - 1

	def clear(self):
		self.title = None
		self.lineList = []
		self.viewLine = 0
		self.cursor =  self.viewLine
		self.dirty = True

	def set_title(self, title, color = curses.COLOR_RED):
		self.title = title
		self.title_color = color 
		self.dirty = True

	def resize(self, maxRow, maxCol = None):
		if not window_base.resize(self, maxRow, maxCol):
			return
		self.endRow = maxRow
		self.adjust_cursor()

	def add_line_str(self, str, **lineinfo):
		li = line()
		li.append_region(str)
		self.lineList.append((li, lineinfo))
		self.dirty = True
		logging.debug("[%s] add line:%s", self.name, str)

	def add_line(self, line, **lineinfo):
		self.lineList.append((line, lineinfo))
		self.dirty = True

	def get_rows(self):
		return len(self.lineList)

	def get_line_info(self, lineno):
		if lineno < len(self.lineList):
			(line, info) = self.lineList[lineno]
			return info

	def get_cursor(self):
		return self.cursor

	def fill_string(self, str):
		str = str or ""
		(maxRow, maxCol) = self.screen.getmaxyx() 
		# return str + (maxCol - len(str)) * ' '
		return str.ljust(maxCol, ' ')

	def update(self):
		#draw title
		drawLine = self.beginRow

		if self.isBorder:
			self.screen.border()

		colorKey = self.is_active() and "ACTIVE_TITLE" or "TITLE"
		logging.debug("win(%s) active:%d", self.name, self.is_active())
		self.screen.addstr(drawLine, 1, self.fill_string(self.title), self.colorScheme.get_color(colorKey))
		drawLine += 1

		def draw_line(drawLine, line, lineRow):
			if drawLine >= self.endRow:
				return False
			beginCol = 0
			for (color, endCol, str) in line.regions:
				if self.cursor == lineRow:
					col = curses.A_REVERSE
				else:
					col = self.colorScheme.get_color(color)
				#logging.debug("line=%d,col=%d,str=%s,endCol=%d", drawLine, beginCol, str, endCol)
				self.screen.addstr(drawLine, beginCol, str.ljust(endCol), col)
				beginCol += endCol
			return True

		for i in range(self.viewLine, len(self.lineList)):
			(line, args) = self.lineList[i]
			if line and draw_line(drawLine, line, i):
				drawLine += 1
				continue
			break

	def draw(self):
		if self.dirty:
			# self.dirty = False
			self.screen.clear()
			if not self.is_show(): return
			self.update()
			self.screen.refresh()
	
	def adjust_cursor(self):
		def clamp(val, minVal, maxVal):
			return max(minVal, min(val, maxVal))

		oldCursor  = self.cursor
		drawRegion = self.endRow - self.beginRow
		maxPos = len(self.lineList) - 1
		self.cursor = clamp(self.cursor, 0, maxPos)
		self.viewLine = clamp(self.viewLine, max(self.cursor - drawRegion + 1, 0), min(self.cursor + drawRegion - 1, maxPos - drawRegion + 1))
		self.dirty = True
		logging.debug("cursor=%d,oldCursor=%s", self.cursor, oldCursor)
		if self.on_cursor_changed:
			self.on_cursor_changed(self)
	
	def cursor_shift(self, shiftVal):
		self.cursor = self.cursor + shiftVal
		drawRegion = self.endRow - self.beginRow
		interval = (self.viewLine + drawRegion - self.cursor) % drawRegion
		if interval >= 3:
			self.viewLine = self.viewLine + shiftVal
		self.adjust_cursor()
		self.dirty = True

	def on_key_input(self, ch):
		if ch == 'j':
			self.cursor_shift(1)
		elif ch == 'k':
			self.cursor_shift(-1)
		else:
			#TODO: page down and page up
			return False
		return True

	def bind_cursor_changed(self, on_changed):
		self.on_cursor_changed = on_changed


class color_scheme:
	def __init__(self):
		self.colors = {}

	def create_color(self, name, fcolor, bcolor):
		index = len(self.colors) + 1
		curses.init_pair(index, fcolor, bcolor)
		self.colors[name] = curses.color_pair(index)
		logging.debug("create color, %s, %d", name, index)

	def get_color(self, color):
		return self.colors[color]


class edit(window_base):
	prefix = ":"
	resultCallBack = None
	gatherStr = None
	
	def __init__(self, app, screen, colorScheme):
		window_base.__init__(self, app, screen, colorScheme)
		self.textbox = curses.textpad.Textbox(screen)
		(h, w) = self.screen.getmaxyx() 
		(y, x) = self.screen.getyx() 
		logging.debug("x=%d,y=%d,w=%d,h=%d", x, y, w-1, h)
		#curses.textpad.rectangle(screen,y,x,y+h,x+w)
	
	def hide_edit(self):
		self.screen.clear()
		self.gatherStr = None
		def show_gather():
			if self.gatherStr:
				self.screen.addstr(0, 0, self.gatherStr)
			else:
				self.screen.addstr(0, 0, self.prefix)
		def hide_gather():
			self.gatherStr = self.textbox.gather()[0:-1]
			prefixLen = len(self.prefix)
			replaceStr = self.prefix + (len(self.gatherStr) - len(self.prefix)) * '*'
			self.screen.addstr(0, 0, replaceStr)
			logging.debug("gather str=%s, %s", self.gatherStr, replaceStr)

		while 1:
			hide_gather()
			ch = self.screen.getch()
			show_gather()
			ret = self.textbox.do_command(ch)
			if not ret:
				break
		# self.screen.refresh()
	def nohide_edit(self):
		self.screen.clear()
		self.screen.addstr(0, 0, self.prefix)
		self.textbox.edit()
	def edit(self):
		self.nohide_edit()

	def gather(self):
		inputStr = self.textbox.gather()
		return inputStr[len(self.prefix):-1]

	def set_prefix(self, str):
		self.prefix = str

	def on_result(self, func):
		self.resultCallBack = func

	def on_active(self, hide=False):
		if self.is_active():
			if hide:
				self.hide_edit()
			else:
				self.nohide_edit()
			if self.resultCallBack:
				self.resultCallBack(self, self.gather())
			self.app.redraw()
			self.active(False, True)

# mode list
NORMAL_MODE = 0
SWITCH_MODE = 1
COMMAND_MODE = 2

class screen_view:
	beginRow = None
	endRow = None
	beginCol = None
	endCol = None
	name = ""
	win = None
	def __init__(self, app, name, beginRow = None, endRow = None, beginCol = None, endCol = None):
		self.beginRow = beginRow
		self.endRow = endRow
		self.beginCol = beginCol
		self.endCol = endCol
		self.name = name
		self.app = app

	def init_win(self):
		(beginRow, endRow, beginCol, endCol)  = self.get_view_region()
		logging.debug("new window, lines=%d,cols=%d,beginy=%d,beginx=%d", 
				endRow - beginRow, 
				endCol - beginCol, beginRow, beginCol)
		self.screen = self.app.stdscr.subwin(endRow - beginRow,
				endCol - beginCol, 
				beginRow, beginCol)
		self.win = window(self.app, self.screen, self.app.colorScheme)
		self.win.set_name(self.name)

	def init_edit(self):
		(beginRow, endRow, beginCol, endCol)  = self.get_view_region()
		logging.debug("new window, lines=%d,cols=%d,beginy=%d,beginx=%d", 
				endRow - beginRow, 
				endCol - beginCol, beginRow, beginCol)
		self.screen = self.app.stdscr.subwin(endRow - beginRow,
				endCol - beginCol, 
				beginRow, beginCol)
		self.win = edit(self.app, self.screen, self.app.colorScheme)
		self.win.set_name(self.name)

	def get_win(self):
		return self.win

	def get_screen(self):
		return self.screen

	def get_name(self):
		return self.name

	def is_show(self):
		return self.win.is_show()

	def get_view_region(self):
		global stdscr
		def calValue(val, defVal, maxVal):
			if not val: return defVal
			elif val < 0: return maxVal + val
			elif val > 0 and val < 1: return int(maxVal * val)
			elif val < maxVal: return val
			else: return maxVal
		(maxRow, maxCol) = self.app.stdscr.getmaxyx() 
		logging.debug("maxRow=%d,maxCol=%d", maxRow, maxCol)
		beginRow = calValue(self.beginRow, 0, maxRow)
		endRow = calValue(self.endRow, maxRow, maxRow)
		beginCol = calValue(self.beginCol, 0, maxCol)
		endCol = calValue(self.beginCol, maxCol, maxCol)
		return (beginRow, endRow, beginCol, endCol)

	def get_begin_row(self):
		(beginRow, endRow, beginCol, endCol)  = self.get_view_region()
		return beginRow

	def get_begin_col(self):
		(beginRow, endRow, beginCol, endCol)  = self.get_view_region()
		return beginCol


class app:
	def __init__(self):
		self.views = []
		self.isQuit = False
		self.init_curses()
		colorScheme = color_scheme()

		colorScheme.create_color("TITLE", curses.COLOR_GREEN, -1)
		colorScheme.create_color("ACTIVE_TITLE", curses.COLOR_RED, curses.COLOR_CYAN)
		colorScheme.create_color("TEXT", curses.COLOR_BLUE, -1)
		self.colorScheme = colorScheme
		self.mode = NORMAL_MODE
		self.curActiveView  = None

		# view = screen_view(self, name, beginRow, endRow, beginCol, endCol)
		# view.init_edit()
		view = screen_view(self, "command", -1, -1)
		view.init_edit()
		self.command_edit = view.get_win()

	def set_mode(self, mode):
		modes = dict(zip([NORMAL_MODE, SWITCH_MODE, COMMAND_MODE], ["normal", "switch", "command"]))
		self.mode = mode
		logging.debug("app enter %s mode!", modes[mode])

	def get_color_scheme(self):
		return self.colorScheme

	def __del__(self):
		self.cleanup_curses()

	#init curses
	def init_curses(self):
		self.stdscr = curses.initscr()
		curses.start_color()
		curses.use_default_colors()
		curses.noecho()
		curses.cbreak()
		curses.curs_set(2)
		self.stdscr.keypad(1)
		curses.qiflush(1)
		#pad = curses.newpad(1000, 1000)

	def cleanup_curses(self):
		curses.nocbreak()
		self.stdscr.keypad(0)
		curses.echo()
		curses.endwin()


	def adjust_view(self):
		(row, col) = self.stdscr.getmaxyx() 

		self.maxRow = row
		self.maxCol = col
		def insert_region(br, er, bc, ec):
			self.maxRow = min(br, self.maxRow)
			self.maxCol = min(bc, self.maxCol)

		def adjust_region(br, er, bc, ec):
			return (br, min(self.maxRow, er), bc, min(self.maxCol, ec))

		for i in range(len(self.views), 0, -1):
			view = self.views[i-1]
			if not view.get_win().showed:
				continue
			(beginRow, endRow, beginCol, endCol) = view.get_view_region()
			(br, er, bc, ec) = adjust_region(beginRow, endRow, beginCol, endCol)
			logging.debug("window resize, lines=%d-%d,cols=%d-%d", er, br, ec, bc)
			view.get_win().resize(er - br, ec - bc)
			insert_region(br, er, bc, ec)

	def new_view(self, name, beginRow = None, endRow = None, beginCol = None, endCol = None):
		view = screen_view(self, name, beginRow, endRow, beginCol, endCol)
		self.views.append(view)
		return view

	def get_view(self, name):
		views = [view for view in self.views if view.get_name() == name]
		return len(views) > 0 and views[0] or None

	def new_window(self, name, beginRow = None, endRow = None, beginCol = None, endCol = None):
		view = self.new_view(name, beginRow, endRow, beginCol, endCol)
		view.init_win()
		return view.get_win()

	def new_edit(self, name, beginRow = None, endRow = None, beginCol = None, endCol = None):
		view = self.new_view(name, beginRow, endRow, beginCol, endCol)
		view.init_edit()
		return view.get_win()

	def get_window(self, name):
		view = self.get_view(name)
		if view: return view.get_win()

	def view_notice_active(self, noticeWin, bactive):
		noticeView = self.get_view(noticeWin.get_name())
		activeView = noticeView
		if not bactive: 
			if self.curActiveView == noticeView:
				views = [view for view in self.views if (view != noticeView and view.get_win().is_show()) ]
				activeView = len(views) > 0 and views[0] or None
			else: return
		map(lambda view: view.get_win().active(False, False),  [view for view in self.views if view != activeView])
		self.curActiveView = activeView
		if activeView:
			logging.debug("cur active view:%s", activeView.get_name())
			activeView.get_win().active(True, False)

	def transform_key(self, key):
		keyname = curses.keyname(key)
		if key >= 1 and key <= 26:
			keyname = "Ctrl-%s"%chr(key + ord('A') - 1)
		if key == 10:
			keyname = "KEY_ENTER"
		return keyname

	def is_switch_mode(self):
		return (self.mode == SWITCH_MODE)

	def is_command_mode(self):
		return (self.mode == COMMAND_MODE)

	def on_command(self, key):
		logging.debug("on_command=%s", key)
		activeWin = self.curActiveView.get_win()

		if key == "Ctrl-W":
			self.set_mode(SWITCH_MODE)
			return True
		if key == ":":
			self.set_mode(COMMAND_MODE)
			self.command_edit.edit()
			logging.debug("command : %s", self.command_edit.gather())
			self.set_mode(NORMAL_MODE)
			return True

		if self.is_switch_mode():
			self.set_mode(NORMAL_MODE)
			curActiveView = self.curActiveView
			views = []
			#map(lambda view:logging.debug("name=%s,row=%d,col=%d", view.get_name(), view.get_begin_row(), view.get_begin_col()), [view for view in self.views])
			valfunc = None
			reverse = False
			if key == 'j':
				views = [view for view in self.views if view.is_show() and view.get_begin_row() > curActiveView.get_begin_row()]
				valfunc = lambda v: v.get_begin_row()
			elif key == 'k':
				views = [view for view in self.views if view.is_show() and view.get_begin_row() < curActiveView.get_begin_row()]
				valfunc = lambda v: v.get_begin_row()
				reverse = True
			elif key == 'l':
				views = [view for view in self.views if view.is_show() and view.get_begin_col() > curActiveView.get_begin_col()]
				valfunc = lambda v: v.get_begin_col()
			elif key == 'h':
				views = [view for view in self.views if view.is_show() and view.get_begin_col() < curActiveView.get_begin_col()]
				valfunc = lambda v: v.get_begin_col()
				reverse = True
			if len(views):
				views = sorted(views, key = valfunc, reverse = reverse)
				for view in views:
					logging.debug("view name=%s", view.name)
				views[0].get_win().active(True)
			return True

		logging.debug("dispatch event: %s", key)
		return activeWin.dispatch_event(key)

	def redraw(self):
		if not self.views: return
		for view in self.views:
			view.get_win().draw()

	def is_end(self):
		if self.isQuit:
			return True
		if len(self.views) <= 0:
			return True
		if not self.curActiveView:
			logging.error("not acitive win!")
			return True
		return False

	def loop(self):
		while 1:
			if self.is_end():
				break
			try:
				key = self.stdscr.getch()
			except KeyboardInterrupt:
				logging.error("app quit by force!")
				break

			keyname = self.transform_key(key)

			if self.on_command(keyname):
				self.redraw()
			if self.curActiveView:
				self.curActiveView.get_win().on_active()
	def quit(self):
		self.isQuit = True

if __name__ == "__main__":
	app = app()
