# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# BUG: Manager Windows closing without countdown (Possibly fatal(?))
# BUG: L252: popen method - some running proccesses are seen as unknown + some suspended processes are seen as running, psutil method - suspended processes are seen as running

# TODO: Option to mute instead of suspend
# TODO: Auto unsuspend when exiting the game.
# TODO: Indication when the game is supposed to be in focus
# TODO: Use grid to put buttons next to each other
# TODO: Correct the button colors when hover/select via keyboard

# TODO: Main window renovation
# TODO: Easier way to add games to games.txt
# TODO: use window title in gui, add gui icon
# TODO: Better layout
# TODO: Script uses too much cpu (kinda solved) (even more so)

# TODO: Seamless mode
# TODO: Use main window for config, option to minimize to tray
# TODO: Set as service to autostart
# TODO: Include dependecies

# BUG: Script crashes after long idle time

# BUG: Returning to game doesn't work reliably for sekiro

version = "2.1.b5.1"
print("Initialising")
try:
	import win32gui, pywinauto, psutil
	import pycaw.pycaw as pycaw
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them by running 'pip install win32gui, pywinauto, psutil, pycaw'")
	time.sleep(10)

import win32process, sys, os, time, subprocess, tkinter, threading, win32api, win32con, pywintypes, collections, ctypes
from tkinter import ttk
from tkinter.messagebox import askokcancel, showerror
try:
	class Interfaces:
		def __init__(self):
			self.debug = 0
			self.iodebug = 0
			self.script = 1
			self.climode = 0
			if ctypes.windll.shell32.IsUserAnAdmin():
				self.clihandle = pywinauto.Application().connect(process=os.getpid()).top_window().handle
			else:
				try:
					self.clihandle = pywinauto.Application().connect(process=psutil.Process(os.getpid()).ppid()).top_window().handle
				except:
					self.climode = -1
			if self.climode != -1:
				win32gui.ShowWindow(self.clihandle, win32con.SW_HIDE)
			threading.Thread(target=self.cli, name="Cli thread", daemon=1).start()

			self.gui = tkinter.Tk()
			self.init_style()
			self.gui.title(f"BGAS V{version} Main Window")
			# self.gui.geometry("260x40+1000+500")
			self.gui.resizable(0,0)
			self.gui_label = ttk.Label(self.gui, text = "BGAS RUNNING", font=("TkDefaultFont", 25))
			self.gui_clibutton = ttk.Button(self.gui, text="Cli Debug Off", command=self.clitoggle)
			if self.climode == -1:
				self.gui_clibutton.config(text="Cli Debug On", state="disabled")
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
				self.gui_clibutton.config(text="Cli Debug On")
			elif self.climode == 1:
				win32gui.ShowWindow(self.clihandle, win32con.SW_HIDE)
				self.climode = 0
				self.gui_clibutton.config(text="Cli Debug Off")

		def cli(self):
			while True:
				i = input("Type d to toggle debug messages, i to toggle loading detection i/o rates, p to toggle entire script (but the cli), r to switch to eval mode:\n")
				if i == "d":
					self.debug = 1 - self.debug
					print(f"debug {self.debug}")
				elif i == "i":
					self.iodebug = 1 - self.iodebug
					print(f"iodebug {self.iodebug}")
				elif i == "p":
					self.script = 1 - self.script # TODO: Make the code respond to this
					print(f"script {self.script}")
				elif i == "r":
					while True:
						i = input("Enter string to eval, r to return back:\n")
						if i == "r":
							break
						else:
							try:
								eval(i) # TODO: Test this
							except Exception as e:
								print(f"Exception in cli eval : {e}")

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
			self.title(f"{self.manager.fname}\nSuspender Initilasing")
			self.geometry("250x350")
			self.label = ttk.Label(self, text = f"{self.manager.fname}", justify="center", font=("TkDefaultFont", 20))
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
			self.title(f"{self.manager.fname}\nSuspender")
			self.returnbutton.config(text="Window not found" if self.manager.windowhandle == None else f"Return to\n{self.manager.fname}", state="disabled" if self.manager.windowhandle == None else "active")
		
		def init_thirdstage(self):
			self.returnbutton.config(text=f"Return to\n{self.manager.fname}", state="active")
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
				if self.manager.script == 0:
					self.scripttoggle()
				self.lsdbutton.config(text="Loading Detection\nActive", style="green.TButton")
				self.manager.detectloading = 1
				if self.manager.state == "background" and self.manager.script == 1:
					threading.Thread(target=self.manager.inbackground, name=f"{self.manager.pname} inbackground", daemon=1).start()
			elif self.manager.detectloading == 1:
				self.lsdbutton.config(text="Loading Detection\nPaused", style="red.TButton")
				self.manager.detectloading = 0
				if self.manager.state == "background" and self.manager.script == 1:
					self.manager.inbackground()
		def scripttoggle(self):
			if self.manager.script == 0:
				self.scriptbutton.config(text="Auto\nActive", style="green.TButton")
				self.manager.script = 1
				if main.debug == 1:
					print(f"{self.manager.pid} {self.manager.pname} : script resumed")
			elif self.manager.script == 1:
				if self.manager.detectloading == 1:
					self.lsdtoggle()
				self.scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				self.manager.script = 0
				if main.debug == 1:
					print(f"{self.manager.pid} {self.manager.pname} : script paused")
		
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
			try:
				self.inittime = time.time()
				self.active = 1
				self.script = 0
				self.pid = pid
				self.pname = psutil.Process(pid).name()
				self.fname = "-".join(list(filter(lambda x: (0 if x.lower() in ["win64","shipping", None] else 1), self.pname[:-4].split("-"))))
				self.windowhandle = None
				self.managevolume = 0
				self.volumecontrol = None
				self.muted = 0
				self.safelyclosed = 0
				self.gui = ManagerGui(self)
				self.graceperiod = 20
				self.detectloading = 1
				self.loadingthreshold = 40000
				self.loadinginterval = 0.2
				self.loadingtimeout = 3
				self.loadingafterchecks = 5
				threading.Thread(target=self.adjustloadingthreashold, name=f"{self.pname} loading threshold adjuster", daemon=1).start()
				self.state = "unknown"
				i = 0
				try:
					self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle # TODO: Option to redo this manually in case it finds the wrong window
				except Exception as e:
					if main.debug == 1:
						print(f"Exception in {self.pid} {self.pname} window handle attempt initial : {e}")
					if "No windows for that process could be found" in str(e):
						pass
					elif "PID" in str(e):
						self.gameclosed()
						raise
				time.sleep(0.2)
				self.gui.init_secondstage()
				if subprocess.Popen(f'tasklist /FI "PID eq {self.pid}" /FI "STATUS eq SUSPENDED"', stdout=subprocess.PIPE).stdout.read() != b"INFO: No tasks are running which match the specified criteria.\r\n": # TODO: Differentiate between suspended and not responding
					self.suspended = 1
					if main.debug == 1:
						print(f"{self.pid} {self.pname} : trying to resume process")
					self.gui.returnbutton.config(text="Unresponsive\ntrying to resume")
					while subprocess.Popen(f'tasklist /FI "PID eq {self.pid}" /FI "STATUS eq SUSPENDED"', stdout=subprocess.PIPE).stdout.read() != b"INFO: No tasks are running which match the specified criteria.\r\n":
						unsuspendpid(pid)
						time.sleep(0.2) # TODO: Test and try to decrease this
					suspendpid(pid)
					self.gui.returnbutton.config(text=f"Return to\n{self.fname}")
				else:
					self.suspended = 0
				if self.windowhandle == None:
					self.gui.returnbutton.config(text="Searching for\ngame window")
					i = 0
					while True:
						try:
							self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle # TODO: Option to redo this manually in case it finds the wrong window
							break
						except Exception as e:
							if main.debug == 1:
								print(f"Exception in {self.pid} {self.pname} window handle attempt {i} : {e}")
							if "PID" in str(e):
								self.gameclosed()
								raise
							if i > 3 and "No windows for that process could be found" in str(e):
								self.gameclosed()
								raise # TODO: This could be better
							i += 1
							time.sleep(0.2)
				# self.script = self.suspended
				self.updatevolumecontrol()
				self.script = 1
				self.gui.init_thirdstage()
			except (psutil.NoSuchProcess, ProcessLookupError): # TODO: Does this actually happen here? If so do something else than passing
				pass
			except Exception as e:
				if main.debug == 1:
					print(f"Exception in {self.pid} {self.pname} init : {e}")
			
		def adjustloadingthreashold(self):
			try:
				iorates = []
				b = 0
				t = time.time()
				ioread = psutil.Process(self.pid).io_counters()[2]
				time.sleep(self.loadinginterval + t - time.time())
				while True and self.active == 1:
					t = time.time()
					ioreadnew = psutil.Process(self.pid).io_counters()[2]
					iorates.append(ioreadnew-ioread)
					if len(iorates) >= 10/self.loadinginterval:
						top4 = collections.Counter(iorates).most_common(4)
						for rate in top4:
							if rate[0] != 0:
								if rate[1] > 10 and rate[0] < 150000:
									if main.debug == 1:
										print(f"{self.pid} {self.pname} : loading threshold set to {rate[0]}")
									self.loadingthreshold = rate[0]
									b = 1
									break
						if b == 1:
							break
					ioread = ioreadnew
					time.sleep(self.loadinginterval + t - time.time())
			except (psutil.NoSuchProcess, ProcessLookupError):
				self.gameclosed()

		def updatevolumecontrol(self):
			audiosessions = pycaw.AudioUtilities.GetAllSessions()
			for session in audiosessions:
				if session.Process and session.Process.pid == self.pid:
					self.volumecontrol = session._ctl.QueryInterface(pycaw.ISimpleAudioVolume)
					if self.volumecontrol.GetMute() == 0:
						self.managevolume = 1 # BUG: This doesn't work

		def suspend(self):
			self.gui.suspendbutton.config(text="Game\nSuspended", style="red.TButton")
			suspendpid(self.pid)
			if main.debug == 1:
				print(f"{self.pid} {self.pname} : suspended")
			self.suspended = 1

		def unsuspend(self):
			self.gui.suspendbutton.config(text="Game\nRunning", style="green.TButton")
			unsuspendpid(self.pid)
			if main.debug == 1:
				print(f"{self.pid} {self.pname} : unsuspended")
			self.suspended = 0

		def mute(self):
			try:
				self.volumecontrol.SetMute(1, None)
				self.muted = 1
				if main.debug == 1:
					print(f"{self.pid} {self.pname} : muted")
			except Exception as e:
				if main.debug == 1:
					print(f"Exception in {self.pid} {self.pname} mute : {e}")
				self.updatevolumecontrol()

		def unmute(self):
			try:
				self.volumecontrol.SetMute(0, None)
				self.muted = 0
				if main.debug == 1:
					print(f"{self.pid} {self.pname} : unmuted")
			except Exception as e:
				if main.debug == 1:
					print(f"Exception in {self.pid} {self.pname} unmute : {e}")
				self.updatevolumecontrol()

		def inforeground(self):
			if self.volumecontrol == None:
				self.updatevolumecontrol()
			if self.muted == 1 and self.managevolume == 1:
				self.unmute()
			if self.suspended != 0:
				print("how did you do this")
				self.unsuspend()

		def inbackground(self):
			if self.volumecontrol == None:
				self.updatevolumecontrol()
			if self.muted == 0 and self.managevolume == 1:
				self.mute()
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
					if main.debug == 1:
						print(f"Exception in {self.pid} {self.pname} inbackground window actions : {e}")
			if self.detectloading == 1:
				i = 0
				def absolutelydectectloadiong():
					return self.state == "background" and self.detectloading == 1 and self.script == 1
				while self.loadingafterchecks >= i:
					ii = 0
					while (ii * self.loadinginterval) / self.loadingtimeout < i**2 and absolutelydectectloadiong(): # Waiting for aftercheck time
						time.sleep(self.loadinginterval)
						if self.state != "background" or self.script == 0:
							break
						ii += 1
					if absolutelydectectloadiong():
						self.unsuspend()
						self.gui.lsdbutton.config(text="Checking for\nloading screen")
						s = 0
						ss = 0
						t = time.time()
						ioread = psutil.Process(self.pid).io_counters()[2]
						time.sleep(self.loadinginterval + t - time.time())
						while s * self.loadinginterval < self.loadingtimeout and absolutelydectectloadiong():
							t = time.time()
							ioreadnew = psutil.Process(self.pid).io_counters()[2]
							if main.iodebug == 1:
								print(ioreadnew - ioread)
							if ioreadnew - ioread <= self.loadingthreshold:
								s += 1
							else:
								self.gui.lsdbutton.config(text="Waiting for\nloading screen")
								s = 0
								ss += 1
								i = 0
							if ss * self.loadinginterval > 60:
								threading.Thread(target=self.adjustloadingthreashold, name=f"{self.pname} loading threshold adjuster", daemon=1).start()
							ioread = ioreadnew
							time.sleep(self.loadinginterval + t - time.time())
					else:
						break
					if absolutelydectectloadiong() and time.time()-self.inittime > self.graceperiod and time.time()-scriptstart > self.graceperiod:
						win32gui.ShowWindow(self.windowhandle, win32con.SW_MINIMIZE)
						self.suspend()
						self.gui.lsdbutton.config(text="Loading Detection\nActive")
					else:
						break
					i += 1
			elif self.suspended != 1:
				self.suspend()

		def returntogame(self):
			self.gui.returnbutton.config(text="Returning")
			s = 0
			if self.script == 1:
				s = 1
				self.script = 0
			else:
				if self.muted == 1 and self.managevolume == 1:
					self.unmute()
			self.unsuspend()
			while True:
				try:
					win32gui.ShowWindow(self.windowhandle, win32con.SW_RESTORE) # TODO: (Maybe) Add alternative method using hide
					win32gui.SetForegroundWindow(self.windowhandle)
					break
				except Exception as e:
					if main.debug == 1:
						print(f"Exception in {self.pid} {self.pname} returntogame window actions : {e}")
					if "not responding" in str(e):
						self.unsuspend()
					elif "no active desktop" in str(e):
						continue
					elif "Invalid window handle" in str(e): # TODO: Why are there two of these?
						self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle as e: # TODO: Maybe show error window if this happens back to back?
					if main.debug == 1:
						print(f"Exception in {self.pid} {self.pname} inbackground window actions : {e} (Handle Invalid)")
					self.windowhandle = pywinauto.Application().connect(process=self.pid).top_window().handle
			if main.debug == 1:
				print(f"{self.pid} {self.pname} : return complete")
			self.gui.returnbutton.config(text=f"Return to\n{self.fname}")
			if s == 1:
				self.script = 1
			# self.gui.returnbutton.config(text=f"{self.pname}\nin focus")

		def kill(self):
			if askokcancel(title=f"Kill {self.pname}?", message=f"Killing {self.pname} ({self.pid}) will result in loss of unsaved data."):
				if self.muted == 1 and self.managevolume == 1:
					self.unmute()
				subprocess.run(["taskkill", "/PID", f"{self.pid}", "/T", "/F"])
				self.gameclosed()

		def gameclosed(self):
			if self.safelyclosed == 0:
				if main.debug == 1:
					print(f"{self.pid} {self.pname} : gameclosed")
				try:
					self.unsuspend()
				except:
					pass
				if main.debug == 1:
					print(f"{self.pid} {self.pname} : gameclosed")
				self.active = 0
				self.script = 0
				for widget in [self.gui.returnbutton, self.gui.suspendbutton, self.gui.lsdbutton, self.gui.scriptbutton]:
					widget.config(state="disabled")
				self.gui.label.config(text="Window closing")
				for i in range(3,0,-1):																							# BUG: Why doesn't this work??
					self.gui.returnbutton.config(text=f"Window closing\nin {i} sec")
					time.sleep(1)
				self.gui.destroy()
				self. safelyclosed = 1

		def safeexit(self):
			self.script = 0
			if self.muted == 1 and self.managevolume == 1:
				self.unmute()
			win32gui.ShowWindow(self.gui.handle, win32con.SW_HIDE)
			time.sleep(0.5)
			self.gui.destroy()
			self.safelyclosed = 1

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
						threading.Thread(target=lambda:managedgames.update({process : GameManager(process)}), name=f"{process} init thread", daemon=1).start()
						time.sleep(1)
				except (psutil.NoSuchProcess, ProcessLookupError):
					pass
				except Exception as e:
					if main.debug == 1:
						print(f"Exception in processscanner : {e}")
			time.sleep(1)

	def foregroundcheck():
		while True:
			currentwindow = win32gui.GetForegroundWindow()
			deletionlist = []
			managedgamescache = managedgames.copy()
			for game in managedgamescache.values():
				if game.script == 1:
					if currentwindow == game.windowhandle:
						if game.state == "background" or game.state == "unknown":
							game.state = "foreground"
							threading.Thread(target=game.inforeground, name=f"{game.pname} {game.pid} inforeground", daemon=1).start()
					else:
						if game.state == "foreground" or game.state == "unknown":
							game.state = "background"
							threading.Thread(target=game.inbackground, name=f"{game.pname} {game.pid} inbackground", daemon=1).start()
				if game.active == 0:
					deletionlist.append(game.pid)
			for pid in deletionlist:
				del managedgames[pid]
			time.sleep(0.2)
		
	def suspendpid(pid):
		psutil.Process(pid).suspend() # Discovered this by complete luck

	def unsuspendpid(pid):
		psutil.Process(pid).resume()

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
		print(f"Exception in entire script : {e}")
		time.sleep(10)