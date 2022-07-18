# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# BUG: If the game launches two processes with the same name the script doesn't work

# TODO: Detect loading screens better
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

# BUG: Script crashes after long idle time

# BUG: Returning to game doesn't work reliably for sekiro
# BUG: Doesn't work at all for chorus

version = "2.1.b3"

try:
	import win32gui, pywinauto, psutil
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them by running 'pip install win32gui, pywinauto, psutil'")
	time.sleep(10)

import win32process, sys, os, time, subprocess, tkinter, threading, win32api, win32con, pywintypes
from tkinter import ttk
from tkinter.messagebox import askokcancel, showerror
try:
	class Interfaces:
		def __init__(self):
			self.debug = 0
			self.iodebug = 0
			self.script = 1

			try:
				self.clihandle = pywinauto.Application().connect(process=os.getpid()).top_window().handle
				self.climode = 0
				win32gui.ShowWindow(self.clihandle, win32con.SW_HIDE)
			except:
				self.climode = -1
			threading.Thread(target=self.cli, name="Cli thread", daemon=1).start()

			self.gui = tkinter.Tk()
			self.init_style()
			self.gui.title(f"BGAS V{version} Main Window")
			# self.gui.geometry("260x40+1000+500")
			self.gui.resizable(0,0)
			self.gui_label = ttk.Label(self.gui, text = "BGAS RUNNING", font=("TkDefaultFont", 25))
			self.gui_clibutton = ttk.Button(self.gui, text="Cli Off", style="main.TButton", command=self.clitoggle)
			if self.climode == -1:
				self.gui_clibutton.config(text="Cli On", state="disabled")
			self.gui_label.pack()
			self.gui_clibutton.pack()
			self.gui.protocol("WM_DELETE_WINDOW", self.forceclose)

		def init_style(self):
			self.style = ttk.Style()
			self.style.theme_use("default")
			self.style.configure("red.TButton", background="#EB4135", foreground="white", font=("TkDefaultFont", 16), justify="center")
			self.style.map("red.TButton", background=[("active", "#FF4A3C"), ("focus", "#B9372D")])
			self.style.configure("green.TButton", background="#42A531", foreground="white", font=("TkDefaultFont", 16), justify="center")
			self.style.map("green.TButton", background=[("active", "#5AC448"), ("focus", "#327B26")])
			self.style.configure("bw.TButton", background="#2F1319", foreground="white", font=("TkDefaultFont", 16), justify="center")
			self.style.map("bw.TButton", background=[("active", "#BF405F"), ("focus", "#903048")])
			self.style.configure("main.TButton",  font=("TkDefaultFont", 22), justify="center")
			# self.style.configure("wb.TButton", background="white", foreground="black", font=("TkDefaultFont", 16))
			# self.style.map("wb.TButton", background=[("active", "#BF405F"), ("focus", "#BF405F")])
			
		def clitoggle(self):
			if self.climode == 0:
				win32gui.ShowWindow(self.clihandle, win32con.SW_SHOW)
				self.climode = 1
				self.gui_clibutton.config(text="Cli On")
			elif self.climode == 1:
				win32gui.ShowWindow(self.clihandle, win32con.SW_HIDE)
				self.climode = 0
				self.gui_clibutton.config(text="Cli Off")

		def cli(self):
			while self.script == True:
				i = input("Type d to toggle debug messages, i to toggle loading detection i/o rates, p to toggle entire script (but the cli), r to switch to interpreter mode:\n")
				if i == "d":
					self.debug = 1 - self.debug
					print(f"debug {self.debug}")
				elif i == "i":
					self.iodebug = 1 - self.iodebug
					print(f"ioebug {self.iodebug}")
				elif i == "p":
					self.script = 1 - self.script # TODO: Make the code respond to this
					print(f"script {self.script}")
				elif i == "r": # TODO: Implement this
					pass

		def forceclose(self):
			win32gui.ShowWindow(win32gui.GetParent(self.gui.winfo_id()), win32con.SW_HIDE)
			for game in managedgames.values():
				game.safeexit() # BUG: Script completely locks up if this runs in a different thread.
				# threading.Thread(target=game.safeexit, name=f"{game.pname} safeexit").start()
			b = 1
			while b == 1:
				b = 0
				for thread in threading.enumerate():
					if "safeexit" in thread.name:
						b = 1
				time.sleep(0.5)
			os._exit(0)

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
			self.lsdbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.lsdtoggle, state="disabled")
			self.scriptbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.scripttoggle, state="disabled")
			self.killbutton = ttk.Button(self, text="Kill game", style="bw.TButton", command=self.manager.kill)
			# mainwindowitems[f"{self.manager.pid} label"] = ttk.Label(gui, text = f"{self.manager.pname}", justify="center", font=("TkDefaultFont", 20))
			self.returnbutton.bind("<Return>", self.returnbuttonpress)
			self.suspendbutton.bind("<Return>", self.suspendbuttonpress)
			self.lsdbutton.bind("<Return>", self.lsdbuttonpress)
			self.scriptbutton.bind("<Return>", self.scriptbuttonpress)
			self.killbutton.bind("<Return>", self.killbuttonpress)
			self.label.pack()
			self.returnbutton.pack()
			self.suspendbutton.pack() # TODO: Use grid to put button next to each other
			self.lsdbutton.pack()
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
			self.lsdbutton.config(text=("Loading Detection\nActive" if self.manager.detectloading else "Loading Detection\nPaused"), style=("green.TButton" if self.manager.detectloading else "red.TButton"), state="active")
			self.scriptbutton.config(text=("Auto\nActive" if self.manager.script else "Auto\nPaused"), style=("green.TButton" if self.manager.script else "red.TButton"), state="active")

		def suspendtoggle(self):
			if self.manager.script == 1:
				self.scripttoggle()
			if self.manager.suspended == 0:
				self.manager.suspend()
			else:
				self.manager.unsuspend()
		def lsdtoggle(self):
			if self.manager.detectloading == 0:
				self.lsdbutton.config(text="Loading Detection\nActive", style="green.TButton")
				self.manager.detectloading = 1
				if self.manager.state == "background":
					b = 0
					for thread in threading.enumerate():
						if f"{self.manager.pname} inbackground" == thread.name:
							b = 1
					if b == 0:
						threading.Thread(target=self.manager.inbackground, name=f"{self.manager.pname} inbackground", daemon=1).start()
			elif self.manager.detectloading == 1:
				self.lsdbutton.config(text="Loading Detection\nPaused", style="red.TButton")
				self.manager.detectloading = 0
		def scripttoggle(self):
			if self.manager.script == 0:
				self.scriptbutton.config(text="Auto\nActive", style="green.TButton")
				self.manager.script = 1
				if main.debug == 1:
					print(f"Script resumed for {self.manager.pname}")
			elif self.manager.script == 1:
				self.scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				self.manager.script = 0
				if main.debug == 1:
					print(f"Script paused for {self.manager.pname}")
		
		def closebuttonpressed(self):
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				self.manager.safeexit()

		def returnbuttonpress(self, event): # TODO: Add visual change
			threading.Thread(target=self.manager.returntogame, daemon=1).start()
		def suspendbuttonpress(self, event): # TODO: Add visual change
			self.suspendtoggle()
		def lsdbuttonpress(self, event): # TODO: Add visual change
			self.lsdtoggle()
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
			self.detectloading = 1
			self.loadingtimeout = 3
			self.loadingtreshold = 40000
			self.loadingafterchecks = 5
			self.state = "unkown"
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
				if main.debug == 1:
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
					except Exception as e: # TODO: Make the exception more specific
						print(e)
					time.sleep(0.2)
			# self.script = self.suspended
			self.script = 1
			self.gui.init_thirdstage()
			
		def suspend(self):
			self.gui.suspendbutton.config(text="Game\nSuspended", style="red.TButton")
			suspendpid(self.pid)
			self.suspended = 1

		def unsuspend(self):
			self.gui.suspendbutton.config(text="Game\nRunning", style="green.TButton")
			unsuspendpid(self.pid)
			self.suspended = 0

		def inforeground(self):
			if self.suspended != 0:
				print("how did you do this")
				self.unsuspend()

		def inbackground(self):
			# game.gui.returnbutton.config(text=f"Return to\n{game.pname}")
			if self.suspended != 1:
				try:
					try:
						win32gui.ShowWindow(self.windowhandle, win32con.SW_MINIMIZE) # TODO: Do a better job
					except:
						pass
					win32gui.ShowWindow(self.gui.handle, win32con.SW_SHOW)
					win32gui.SetForegroundWindow(self.gui.handle)
				except pywintypes.error as e: # TODO: Do something else here
					print(e)
			if self.detectloading == 1:
				i = 0
				while self.loadingafterchecks >= i and self.script == 1:
					ii = 0
					while (ii * 0.2) / self.loadingtimeout < i**2:
						time.sleep(0.2)
						if self.state != "background" or self.script == 0:
							break
						ii += 1
					if self.state == "background" and self.detectloading == 1 and self.script == 1:
						self.unsuspend()
						i = self.pauseonloading(i)
					else:
						break
					if self.state == "background" and self.script == 1:
						win32gui.ShowWindow(self.windowhandle, win32con.SW_MINIMIZE) # TODO: Do a better job
						self.suspend()
						self.gui.lsdbutton.config(text="Loading Detection\nActive")
					else:
						break
					i += 1
			else:
				self.suspend()

		def pauseonloading(self, i = None): # TODO: Integrate this to inbackground # TODO: Make this better
			self.gui.lsdbutton.config(text="Checking for\nloading screen")
			adjustedthreshold = self.loadingtreshold * 0.5
			ioread = psutil.Process(self.pid).io_counters()[2]
			s = 0
			ii = 0
			while s * 0.5 < self.loadingtimeout and self.script == 1:
				time.sleep(0.1)
				if self.state != "background" or self.script == 0:
					break
				ii += 1
				if ii < 5:
					continue
				ii = 0
				ioreadnew = psutil.Process(self.pid).io_counters()[2]
				if main.iodebug == 1:
					print(ioreadnew - ioread)
				if ioreadnew - ioread < adjustedthreshold:
					s += 1
				else:
					self.gui.lsdbutton.config(text="Waiting for\nloading screen")
					s = 0
					i = 0
				ioread = ioreadnew
			return i

		def kill(self):
			if askokcancel(title=f"Kill {self.pname}?", message=f"Killing {self.pname} will result in loss of unsaved data."):
				self.unsuspend()
				subprocess.run(["taskkill", "/PID", f"{self.pid}", "/T", "/F"])
			
		def returntogame(self):
			self.gui.returnbutton.config(text="Returning")
			self.script = 0
			self.unsuspend()
			while True:
				try:
					win32gui.ShowWindow(self.windowhandle, win32con.SW_RESTORE) # TODO: (Maybe) Add alternative method using hide
					win32gui.SetForegroundWindow(self.windowhandle)
					break
				except RuntimeError as e:
					if main.debug == 1:
						print(e)
					if "not responding" in str(e):
						self.unsuspend()
					elif "no active desktop" in str(e):
						continue
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle: # TODO: Maybe show error window if this happens back to back?
					if main.debug == 1:
						print("Handle invalid")
					self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle
					continue
			if main.debug == 1:
				print(f"Returned to {self.pname}")
			self.gui.returnbutton.config(text=f"Return to\n{self.pname}")
			self.script = 1
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

		def safeexit(self):
			self.script = 0
			win32gui.ShowWindow(self.gui.handle, win32con.SW_HIDE)
			time.sleep(0.5)
			self.gui.destroy()

	def retrievesuspendlist():
		if os.path.exists("games.txt"):
			with open("games.txt","r") as f:
				return list(filter(None, f.read().split("\n")))
		else:
			with open("games.txt", "w") as f:
				f.write("Delete this line and enter the names of the executables you want the script to work on, one name each line") # TODO: Add GUI message

	def processscanner():
		processcache = set([])
		while main.script == True:
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
						game.state = "foreground"
						threading.Thread(target=game.inforeground, name=f"{game.pname} inforeground", daemon=1).start()
					else:
						game.state = "background"
						b = 0
						for thread in threading.enumerate():
							if f"{game.pname} inbackground" == thread.name:
								b = 1
						if b == 0:
							threading.Thread(target=game.inbackground, name=f"{game.pname} inbackground", daemon=1).start()
				if game.active == 0:
					deletionlist.append(game.pid)
			for pid in deletionlist:
				del managedgames[pid]
			time.sleep(0.2)
		
	def suspendpid(pid):
		psutil.Process(pid).suspend() # Discovered this by complete luck
		if main.debug == 1:
			print(f"Suspended {pid}")

	def unsuspendpid(pid):
		psutil.Process(pid).resume()
		if main.debug == 1:
			print(f"Unsuspended {pid}")

	suspendlist = retrievesuspendlist()
	managedgames = {} # {pid : MonitoredGame}
	# refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')

	scriptstart = time.time()
	main = Interfaces()
	threading.Thread(target=processscanner, name="processscanner thread", daemon=1).start()
	threading.Thread(target=foregroundcheck, name="foregroundcheck thread", daemon=1).start()
	main.gui.mainloop()
	
except Exception as e:
	if e != KeyboardInterrupt:
		print(e)
		time.sleep(10)