##TODO 	snap windows earlier, some pixel before mouse hits dead end
##	fix issue in __window_header_clicked()
##
##
##

from pymouse import PyMouse,PyMouseEvent
from wmctrl import Window, BaseWindow
from multiprocessing.pool import ThreadPool

LEFT_MOUSE_BUTTON = 1 #PyMouse mapping for left mouse button
COUNTER = 50 #cleaning the dict or window sizes after every x clicks, this has to happen because no events for closing windows are caught, therefor the dict (original_window_sizes) potentially grows forever
global HEADER_CLICKED #meh hacks

class MouseEventHandler(PyMouseEvent):
	def __init__(self):
		PyMouseEvent.__init__(self)
		
		#get these programmatically
		self.WM_WIDTH = 2 #lubuntu standard
		self.WM_HEIGHT = 52 #lubuntu standard
		self.WM_BOTTOM_HEIGHT = 4 #lubuntu standard
		self.TASKBAR_HEIGHT = 24 #lubuntu standard
		###########################################

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
		if y == 0:
			self.__maximize(window)
		elif x == 0:
			self.__fill_left_half(window)
		elif x == self.screen_width-1:
			self.__fill_right_half(window)
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
		self.__resize_window(window,0,0,self.screen_width+(self.WM_WIDTH * 2),self.screen_height - self.TASKBAR_HEIGHT - self.WM_BOTTOM_HEIGHT) #(self.WM_WIDTH * 2) -> compensate for WM borders

	def __fill_right_half(self,window):
		if not self.__window_in_list(window):
			self.__update_window(window)
		self.__resize_window(window,(self.screen_width/2)+(self.WM_WIDTH * 2),0,self.screen_width/2,self.screen_height - self.TASKBAR_HEIGHT - self.WM_BOTTOM_HEIGHT) #(self.WM_WIDTH * 2) -> compensate for WM borders

	def __fill_left_half(self,window):
		if not self.__window_in_list(window):
			self.__update_window(window)
		self.__resize_window(window,0,0,(self.screen_width/2)+(self.WM_WIDTH * 2),self.screen_height - self.TASKBAR_HEIGHT - self.WM_BOTTOM_HEIGHT) #(self.WM_WIDTH * 2) -> compensate for WM borders

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
		right_bottom_y = window.y
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


if __name__ == "__main__":
	eventhandler = MouseEventHandler()
	eventhandler.run()
