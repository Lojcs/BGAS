# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# BUG: If the game launches two processes with the same name the script doesn't work

# TODO: Detect loading screens
# TODO: Option to mute instead of suspend
# TODO: Indication when the game is supposed to be in focus
# TODO: Use grid to put buttons next to each other
# TODO: Correct the button colors when hover/select via keyboard
# TODO: Main window renovation
# TODO: Easier way to add games to games.txt
# TODO: Auto unsuspend when exiting the game.

# TODO: use window title in gui, add gui icon
# TODO: Better layout
# TODO: Script uses too much cpu (kinda solved) (even more so)

# TODO: Seamless mode
# TODO: Use main window for config, option to minimize to tray
# TODO: Set as service to autostart
# TODO: Include dependecies
# TODO: Remove pssuspend64.exe dependecy requirement

# BUG: Script crashes after long idle time

# BUG: Returning to game doesn't work reliably for sekiro
# BUG: Doesn't work at all for chorus

version = "2.1.b1.2"

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them by running 'pip install win32gui, pywinauto'")
	time.sleep(10)

import win32process, sys, os, time, psutil, subprocess, tkinter, threading, win32api, win32con, pywintypes
from tkinter import ttk
from tkinter.messagebox import askokcancel, showerror
try:
	win32gui.ShowWindow(pywinauto.Application().connect(process=os.getpid()).top_window().handle, win32con.SW_HIDE)
except:
	pass
try:
	if os.path.exists("games.txt"):
		with open("games.txt","r") as f:
			suspendlist = list(filter(None, f.read().split("\n")))
	else:
		with open("games.txt", "w") as f:
			f.write("Delete this line and enter the names of the executables you want the script to work on, one name each line") # TODO: Add GUI message

	class ManagerGui(tkinter.Toplevel):
		def __init__(self, manager): # TODO: Make sure this is not overwriting anything
			self.manager = manager
			super().__init__()
			self.title(f"{self.manager.pname}\nSuspender Initilasing")
			self.geometry("250x350")
			self.label = ttk.Label(self, text = f"{self.manager.pname}", justify="center", font=("TkDefaultFont", 20))
			self.resizable(0,0)
			self.returnbutton = ttk.Button(self, text="Searching for\ngame window", style="main.TButton", command=lambda: threading.Thread(target=self.manager.returntogame, daemon=1).start(), state="disabled")
			self.suspendbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.suspendtoggle, state="disabled")
			self.scriptbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.scripttoggle, state="disabled")
			self.killbutton = ttk.Button(self, text="Kill game", style="bw.TButton", command=self.manager.kill)
			# mainwindowitems[f"{self.manager.pid} label"] = ttk.Label(gui, text = f"{self.manager.pname}", justify="center", font=("TkDefaultFont", 20))
			self.returnbutton.bind("<Return>", self.returnbuttonpress)
			self.suspendbutton.bind("<Return>", self.suspendbuttonpress)
			self.scriptbutton.bind("<Return>", self.scriptbuttonpress)
			self.killbutton.bind("<Return>", self.killbuttonpress)
			self.label.pack()
			self.returnbutton.pack()
			self.suspendbutton.pack() # TODO: Use grid to put button next to each other
			self.scriptbutton.pack()
			self.killbutton.pack()
			self.returnbutton.focus_set()
			self.protocol("WM_DELETE_WINDOW", self.closebuttonpressed)
			self.handle = win32gui.GetParent(self.winfo_id())
			win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)
			try:
				win32gui.SetForegroundWindow(self.handle)
			except:
				pass

		def init_secondstage(self):
			self.title(f"{self.manager.pname}\nSuspender")
			self.returnbutton.config(text="Window not found" if self.manager.windowhandle == None else f"Return to\n{self.manager.pname}", state="disabled" if self.manager.windowhandle == None else "active")
		
		def init_thirdstage(self):
			self.returnbutton.config(text=f"Return to\n{self.manager.pname}", state="active")
			self.suspendbutton.config(text=("Game\nSuspended" if self.manager.suspended else "Game\nRunning"), style=("red.TButton" if self.manager.suspended else "green.TButton"), state="active")
			self.scriptbutton.config(text=("Auto\nActive" if self.manager.script else "Auto\nPaused"), style=("green.TButton" if self.manager.script else "red.TButton"), state="active")

		def suspendtoggle(self):
			if self.manager.script == 1:
				self.scripttoggle()
			if self.manager.suspended == 0:
				self.manager.suspend()
			else:
				self.manager.unsuspend()
		def scripttoggle(self):
			if self.manager.script == 0:
				self.scriptbutton.config(text="Auto\nActive", style="green.TButton")
				self.manager.script = 1
				if debug == 1:
					print(f"Script resumed for {self.manager.pname}")
			elif self.manager.script == 1:
				self.scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				self.manager.script = 0
				if debug == 1:
					print(f"Script paused for {self.manager.pname}")
		
		def closebuttonpressed(self):
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				self.manager.unsuspend()
				self.manager.script = 0
				win32gui.ShowWindow(self.handle, win32con.SW_HIDE)

		def returnbuttonpress(self, event): # TODO: Add visual change
			threading.Thread(target=self.manager.returntogame, daemon=1).start()
		def suspendbuttonpress(self, event): # TODO: Add visual change
			self.suspendtoggle()
		def scriptbuttonpress(self, event): # TODO: Add visual change
			self.scripttoggle()
		def killbuttonpress(self, event): # TODO: Add visual change
			self.manager.kill()

	class GameManager:
		def __init__(self, pid):
			self.active = 1
			self.script = 0
			self.pid = pid
			self.pname = psutil.Process(pid).name()
			self.gui = ManagerGui(self)
			i = 0
			while i < 20:
				try:
					self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle # TODO: Option to redo this manually in case it finds the wrong window
					break
				except Exception as e: # TODO: Make the exception more spesific
					print(e)
				time.sleep(0.2)
				i += 1
			self.gui.init_secondstage()
			if subprocess.Popen(f'tasklist /FI "PID eq {pid}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n": # TODO: Differentiate between suspended and not responding
				self.suspended = 1
				if debug == 1:
					print("Trying to resume process")
				self.gui.returnbutton.config(text="Unresponsive\ntrying to resume")
				while subprocess.Popen(f'tasklist /FI "PID eq {pid}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n":
					unsuspendpid(pid)
					time.sleep(0.2) # TODO: Test and try to decrease this
				suspendpid(pid)
				self.gui.returnbutton.config(text=f"Return to\n{self.pname}")
			else:
				self.suspended = 0
			if self.windowhandle == None:
				self.gui.returnbutton.config(text="Searching for\ngame window")
				while True:
					try:
						self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle # TODO: Option to redo this manually in case it finds the wrong window
						break
					except Exception as e: # TODO: Make the exception more spesific
						print(e)
					time.sleep(0.2)
			self.script = self.suspended
			self.gui.init_thirdstage()
			
		def suspend(self):
			self.gui.suspendbutton.config(text="Game\nSuspended", style="red.TButton")
			suspendpid(self.pid)
			self.suspended = 1

		def unsuspend(self):
			self.gui.suspendbutton.config(text="Game\nRunning", style="green.TButton")
			unsuspendpid(self.pid)
			self.suspended = 0

		def kill(self):
			if askokcancel(title=f"Kill {self.pname}?", message=f"Killing {self.pname} will result in loss of unsaved data."):
				self.unsuspend()
				subprocess.run(["taskkill", "/PID", f"{self.pid}", "/T", "/F"])
			
		def returntogame(self):
			self.gui.returnbutton.config(text="Returning")
			self.unsuspend()
			while True:
				try:
					win32gui.ShowWindow(self.windowhandle, win32con.SW_RESTORE) # TODO: (Maybe) Add alternative method using hide
					win32gui.SetForegroundWindow(self.windowhandle)
					break
				except RuntimeError as e:
					if debug == 1:
						print(e)
					if "not responding" in str(e):
						self.unsuspend()
					elif "no active desktop" in str(e):
						continue
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle: # TODO: Maybe show error window if this happens back to back?
					if debug == 1:
						print("Handle invalid")
					continue
			if debug == 1:
				print(f"Returned to {self.pname}")
			self.gui.returnbutton.config(text=f"Return to\n{self.pname}")
			# self.gui.returnbutton.config(text=f"{self.pname}\nin focus")

		def gameclosed(self):
			self.active = 0
			for widget in [self.gui.returnbutton, self.gui.suspendbutton, self.gui.scriptbutton]:
				widget.config(state="disabled")
			self.gui.label.config(text="Game closed")
			
			for i in range(3,0,-1):
				self.gui.returnbutton.config(text=f"Window closing\nin {i} sec")
				time.sleep(1)
			self.gui.destroy()

	class SafeQueue: # https://stackoverflow.com/questions/45467163/how-to-pause-a-thread-python
		def __init__(self):
			self.queue = {} # {id : function}
			self.nextid = 1
			self.completedid = 0
			self.mainthread = None
		def do(self, action, wait=0):
			id = self.nextid
			self.queue[id] = action
			self.nextid += 1
			if self.mainthread == None or self.mainthread.is_alive == False:
				self.mainthread = threading.Thread(target=self.main, name="SafeQueue main", daemon=1).start()
			if wait == 1:
				while self.completedid < id:
					time.sleep(0.01) # Increase for less CPU usage
		def main(self):
			while len(self.queue) > 0:
				self.queue[self.completedid + 1]()
				self.completedid += 1

	managedgames = {} # {pid : MonitoredGame}

	runninggames = {} # {pid : [0: pname, 1: script state, 2: suspension state, 3: [gui, reutrnbutton, suspendbutton, window], 4: active, 5: window]}

	# refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')
	def processscanner():
		processcache = set([])
		while script == True:
			currentprocesses =  set(win32process.EnumProcesses())
			newprocesses = currentprocesses.difference(processcache)
			processcache = currentprocesses
			managedgamescache = managedgames.copy()
			for game in managedgamescache:
				if game not in currentprocesses:
					managedgamescache[game].gameclosed()
			for process in newprocesses:
				try:
					if psutil.Process(process).name() in suspendlist:
						managedgames[process] = GameManager(process)
				except psutil.NoSuchProcess:
					pass
			time.sleep(1)

	def foregroundcheck():
		while True:
			currentwindow = win32gui.GetForegroundWindow()
			deletionlist = []
			for game in managedgames.values():
				if game.script == 1:
					if currentwindow == game.windowhandle:
						if game.suspended != 0:
							print("how did you do this")
							game.unsuspend()
					else:
						# game.gui.returnbutton.config(text=f"Return to\n{game.pname}")
						if game.suspended != 1:
							try:
								try:
									win32gui.ShowWindow(game.windowhandle, win32con.SW_MINIMIZE) # TODO: Do a better job
								except:
									pass
								win32gui.ShowWindow(game.gui.handle, win32con.SW_SHOW)
								win32gui.SetForegroundWindow(game.gui.handle)
							except pywintypes.error as e: # TODO: Do something else here
								print(e)
							game.suspend()
				if game.active == 0:
					deletionlist.append(game.pid)
			for pid in deletionlist:
				del managedgames[pid]
			time.sleep(0.2)
		

	def suspendpid(pid):
		subprocess.run([".\pssuspend64", f"{pid}"], capture_output=1)
		if debug == 1:
			print(f"Suspended {pid}")

	def unsuspendpid(pid):
		subprocess.run([".\pssuspend64", "-r", f"{pid}"], capture_output=1)
		if debug == 1:
			print(f"Unsuspended {pid}")

	def cli():
		while script == True:
			if input("Type d for debug, else to exit:") == "d":
				global debug
				debug = 1-debug
				print(f"Debug {debug}")
			else:
				os._exit(0)

	# def rundelayed(event):
	# 	time.sleep(1)
	# 	win32gui.ShowWindow(pywinauto.Application().connect(process=os.getpid()).top_window().handle, win32con.SW_HIDE)

	def forceclose():
		os._exit(0)

	gui = tkinter.Tk()
	style = ttk.Style()
	style.theme_use("default")
	style.configure("red.TButton", background="#EB4135", foreground="white", font=("TkDefaultFont", 16), justify="center")
	style.map("red.TButton", background=[("active", "#FF4A3C"), ("focus", "#B9372D")])
	style.configure("green.TButton", background="#42A531", foreground="white", font=("TkDefaultFont", 16), justify="center")
	style.map("green.TButton", background=[("active", "#5AC448"), ("focus", "#327B26")])
	style.configure("bw.TButton", background="#2F1319", foreground="white", font=("TkDefaultFont", 16), justify="center")
	style.map("bw.TButton", background=[("active", "#BF405F"), ("focus", "#903048")])
	style.configure("main.TButton",  font=("TkDefaultFont", 22), justify="center")
	# style.configure("wb.TButton", background="white", foreground="black", font=("TkDefaultFont", 16))
	# style.map("wb.TButton", background=[("active", "#BF405F"), ("focus", "#BF405F")])
	gui.title(f"BGAS V{version} Main Window")
	# gui.geometry("260x40+1000+500")
	gui.resizable(0,0)
	mainwindowitems = {}
	mainwindowitems["Label"] = ttk.Label(gui, text = "BGAS RUNNING", font=("TkDefaultFont", 25))
	# mainwindowitems["Label"].grid(column=0, row=0)
	# gui.bind("<Visibility>", rundelayed)
	mainwindowitems["Label"].pack()
	gui.protocol("WM_DELETE_WINDOW", forceclose)

	scriptstart = time.time()
	script = True
	debug = 0
	threading.Thread(target=processscanner, name="processscanner thread", daemon=1).start()
	threading.Thread(target=foregroundcheck, name="foregroundcheck thread", daemon=1).start()
	threading.Thread(target=cli, name="cli thread", daemon=1).start()

	gui.mainloop()
	
except Exception as e:
	if e != KeyboardInterrupt:
		print(e)
		time.sleep(10)