##TODO 	snap windows earlier, some pixel before mouse hits dead end
##	fix issue in __window_header_clicked()
##	update handling of input commands
##	write some documentation on input arguments
##

from pymouse import PyMouse,PyMouseEvent
from wmctrl import Window, BaseWindow
import sys

LEFT_MOUSE_BUTTON = 1 #PyMouse mapping for left mouse button
COUNTER = 50 #cleaning the dict or window sizes after every x clicks, this has to happen because no events for closing windows are caught, therefor the dict (original_window_sizes) potentially grows forever
global HEADER_CLICKED #meh hacks

class MouseEventHandler(PyMouseEvent):
	def __init__(self,max_width,max_height,wm_width=2,wm_height=44,clickable_offset=23, margin=10):
		PyMouseEvent.__init__(self)
		
		#get these programmatically
		self.WM_WIDTH = int(wm_width) ##WM side of window width in pixels
		self.WM_HEIGHT = int(wm_height) #WM top of window height in pixels
		self.CLICKABLE_OFFSET = int(clickable_offset) #number of pixels on the WM window that are not moving the window when clicked
		self.MARGIN = int(margin) #dictates when snapping occures
		#self.WM_BOTTOM_HEIGHT = 4 #number of pixels at the bottom of each window
		#self.TASKBAR_HEIGHT = 30 #height of the taskbar in pixels, atm only taskbars at the bottom are considered 
		###########################################

		self.MAX_WINDOW_WIDTH = int(max_width)
		self.MAX_WINDOW_HEIGHT = int(max_height)
		

		self.mouse = PyMouse()
		screen_size = self.mouse.screen_size()
		self.screen_width = screen_size[0]
		self.screen_height = screen_size[1]
		self.counter = COUNTER 
		self.original_window_sizes = {} #info used to restore windows when 'unsnapping' them

	def click(self, x, y, button, press):
		if self.counter == 0:
			self.counter = COUNTER
			self.__remove_closed_windows()
		if button is LEFT_MOUSE_BUTTON:
			global HEADER_CLICKED
			if press:
				HEADER_CLICKED = self.__window_header_clicked()
				self.counter -= 1
			elif not press:
				if HEADER_CLICKED:
					window =  self.__get_active_window()
					if window is None:
						return
					restore = self.__window_in_list(window)
					self.__handle_event(window,x,y,restore)
	
	def __handle_event(self,window,x,y,restore):
		if x < self.MARGIN:
			self.__fill_left_half(window)
		elif x > self.screen_width-1-self.MARGIN:
			self.__fill_right_half(window)
		elif y < self.MARGIN:
			self.__maximize(window)
		elif restore:
			self.__restore_size(window)

	def __resize_window(self,window,x_position,y_position,width,height,use_offset=False):
		if use_offset:
			window.resize_and_move(x_position-self.WM_WIDTH,y_position-self.WM_HEIGHT,width,height)
		else:	
			window.resize_and_move(x_position,y_position,width,height)

	def __maximize(self,window):
		if not self.__window_in_list(window):
			self.__update_window(window)
		self.__resize_window(window,0,0,self.MAX_WINDOW_WIDTH,self.MAX_WINDOW_HEIGHT)

	def __fill_right_half(self,window):
		if not self.__window_in_list(window):
			self.__update_window(window)
		self.__resize_window(window,self.MAX_WINDOW_WIDTH/2,0,self.MAX_WINDOW_WIDTH/2,self.MAX_WINDOW_HEIGHT)

	def __fill_left_half(self,window):
		if not self.__window_in_list(window):
			self.__update_window(window)
		self.__resize_window(window,0,0,self.MAX_WINDOW_WIDTH/2,self.MAX_WINDOW_HEIGHT)

	def __restore_size(self,window):
		if window.id in self.original_window_sizes:
			original = self.original_window_sizes[window.id]
			self.__remove_window(window.id)
			self.__resize_window(window,window.x,window.y,original[0],original[1],True)

	def __window_header_clicked(self):
		#still a bug, sometimes false is returned even if the header was clicked 
		#cause seems to be incorrect(too small) Y values for mouse position, timing issue?
		#happens less often when position() before __get_active_window()

		position = self.mouse.position()
		window = self.__get_active_window()
		if window is None:
			return False

		x = position[0]
		y = position[1]
		left_top_x = window.x - self.WM_WIDTH
		right_bottom_x = window.x + window.w
		left_top_y = window.y - self.WM_HEIGHT
		right_bottom_y = window.y - self.CLICKABLE_OFFSET
		inside = (left_top_x <= x <= right_bottom_x and left_top_y <= y <= right_bottom_y) # simple point inside rectangle check
		#if not inside:
		#	print("mouseX",x, "mouseY", y)
		#	print("topleftX",left_top_x, "topleftY", left_top_y)
		#	print("bottomrightX",right_bottom_x, "bottomrightY", right_bottom_y)
		return inside

	#called when a (unsnapped!) window is resized
	def __update_window(self,window):
		self.original_window_sizes.update({window.id:(window.w,window.h)})

	#removes a window from the original sizes dict
	def __remove_window(self,key):
		self.original_window_sizes.pop(key,None)
	
	#removes all windows that have been closed, necessary since we do not intercept any structure events
	def __remove_closed_windows(self):
		try:
			windows = Window.list()
			open_windows = []
			for window in windows:
				open_windows.append(window[0])
			for key in self.original_window_sizes.keys():
				if key not in open_windows:
					self.__remove_window(key)
		except ValueError:
			#catching Error in the wmctrl function list(), still holding already closed windows
			pass
			
	def __window_in_list(self,window):
		return window.id in self.original_window_sizes.keys()
		
	
	#returns None if Window.get_active() fails, this 
	#happens sometimes when windows are closed and the list inside wmctrl.Window 
	#was not yet updated when we called get_active()
	def __get_active_window(self): 
		try:
			window = Window.get_active()
			return window
		except ValueError:
			#catching Error in the wmctrl function list(), still holding already closed windows
			return None



def run_analysis():
	try:
		print("run in maximized window to get values for screen width and height")
		window = Window.get_active()
		return window.w, window.h
	except ValueError:
		#catching Error in the wmctrl function list(), still holding already closed windows
		return None

if __name__ == "__main__":
	args = sys.argv
	if len(args) == 1:
		w,h = run_analysis()
		print("width and height are:", w,h)
		print("use these values to start snap.py")
	elif len(args) == 3:	
		eventhandler = MouseEventHandler(args[1],args[2])
		eventhandler.run()
	elif len(args) == 7:	
		eventhandler = MouseEventHandler(args[1],args[2],args[3],args[4],args[5],args[6])
		eventhandler.run()
	else:
		print("Usage: python snap.py width height [wm_width] [wm_height] [clickable_offset] [margin]")
		print("Example: python snap.py 1920 924 2 44 23 10")

