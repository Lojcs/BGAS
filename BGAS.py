# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# TODO: Don't start suspending until game window appearsZ

# TODO: use window title in gui, add gui icon
# TODO: functions should aquire a lock before doing actions that might break others.
# TODO: Better layout
# TODO: Use a class instead of lists in runninggames.
# TODO: Use an orderer to lift fgcpause for individual functions
# TODO: Script uses too much cpu (kinda solved)

# TODO: Auto unsuspend when exiting the game.
# TODO: Seamless mode
# TODO: Use main window for config, option to minimize to tray
# TODO: Set as service to autostart
# TODO: Include dependecies
# TODO: Remove pssuspend64.exe dependecy requirement

# BUG: Script crashes after long idle time

# BUG: Returning to game doesn't work reliably for sekiro
# BUG: Doesn't work at all for chorus

version = "2.1.a3"

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them by running 'pip install win32gui, pywinauto'")

import win32process, sys, os, time, psutil, subprocess, tkinter, threading, win32api, win32con, pywintypes
from tkinter import ttk
from tkinter.messagebox import askokcancel
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
		def __init__(self, manager):
			self.manager = manager
			super().__init__()
			self.title("Suspender initialising")
			self.geometry("250x350")
			self.label = ttk.Label(self, text = f"Initialising", justify="center", font=("TkDefaultFont", 20))
			self.resizable(0,0)
			self.returnbutton = ttk.Button(self, text="Initialising", style="main.TButton", command=lambda: threading.Thread(target=self.returntogame, daemon=1).start(), state="disabled")
			self.suspendbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.suspendtoggle, state="disabled")
			self.scriptbutton = ttk.Button(self, text="Initialising", style="red.TButton", command=self.pausetoggle, state="disabled")
			self.killbutton = ttk.Button(self, text="Kill game", style="bw.TButton", command=self.killgame)
			self.returnbutton.bind("<Return>", self.returnbuttonpress)
			self.suspendbutton.bind("<Return>", self.suspendbuttonpress)
			self.scriptbutton.bind("<Return>", self.scriptbuttonpress)
			self.killbutton.bind("<Return>", self.killbuttonpress)
			self.label.pack()
			self.returnbutton.pack()
			self.suspendbutton.pack()
			self.scriptbutton.pack()
			self.killbutton.pack()
			self.returnbutton.focus_set()
			self.protocol("WM_DELETE_WINDOW", self.closebuttonpressed)
			self.hwnd = win32gui.GetParent(self.winfo_id())

		def finalise_init(self):
			self.title(f"{self.manager.pname}\nSuspender")
			self.label.config(self, text = f"{self.manager.pname}", justify="center", font=("TkDefaultFont", 20))
			self.returnbutton.config(text=f"Return to\n{self.manager.pname}", default="normal")
			self.suspendbutton.config(text=("Game\nSuspended" if self.manager.suspended else "Game\nRunning"), style=("red.TButton" if self.manager.suspended else "green.TButton"))
			self.scriptbutton.config(text=("Auto\nActive" if self.manager.script else "Auto\nPaused"), style=("green.TButton" if self.manager.script else "red.TButton"))
		
		def suspendtoggle(self):
			if runninggames[self.pid][1] == 1:
				self.pausetoggle()
			if runninggames[self.pid][2] == 0:
				suspend_old(self.pid)
			elif runninggames[self.pid][2] == 1:
				unsuspend_old(self.pid)
		def pausetoggle(self):
			if runninggames[self.pid][1] == 0:
				self.scriptbutton.config(text="Auto\nActive", style="green.TButton")
				runninggames[self.pid][1] = 1
				print(f"Script resumed for {runninggames[self.pid][0]}")
			elif runninggames[self.pid][1] == 1:
				self.scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				runninggames[self.pid][1] = 0
				print(f"Script paused for {runninggames[self.pid][0]}")
		def killgame(self):
			if askokcancel(title=f"Kill {runninggames[self.pid][0]}?", message=f"Killing {runninggames[self.pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{self.pid}"])
				subprocess.run(["taskkill", "/PID", f"{self.pid}", "/T", "/F"])
				self.destroy()
		
		def closebuttonpressed(self):
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				unsuspend_old(self.pid)
				runninggames[self.pid][3] = []
				runninggames[self.pid][1] = 0
				self.destroy()

		def returnbuttonpress(self, event): # TODO: Add visual change
			threading.Thread(target=self.returntogame, daemon=1).start()
		def suspendbuttonpress(self, event): # TODO: Add visual change
			self.suspendtoggle()
		def scriptbuttonpress(self, event): # TODO: Add visual change
			self.pausetoggle()
		def killbuttonpress(self, event): # TODO: Add visual change
			self.killgame()

	class GameManager:
		def __init__(self, pid):
			self.script = 0
			self.gui = ManagerGui(self)
			self.pid = pid
			self.pname = psutil.Process(pid).name()
			if subprocess.Popen(f'tasklist /FI "PID eq {pid}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n":
				self.suspended = 1
				print("Trying to resume process")
				self.gui.label.config(text="Trying to resume process")
				while subprocess.Popen(f'tasklist /FI "PID eq {pid}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n":
					unsuspend(pid)
					time.sleep(0.2) # TODO: Test and try to decrease this
				suspend(pid)
			else:
				self.suspended = 0
			self.focus = 0
			self.gui.finalise_init()
			self.script = 1
			# self.window = window # Unused

		def returntogame(self):
			global fgcpause
			fgcpause = 1
			if runninggames[self.pid][5] == None:
				self.returnbutton.config(text="Finding window")
				runninggames[self.pid][5] = pywinauto.Application().connect(process=self.pid).top_window()
			self.returnbutton.config(text="Returning")
			unsuspend_old(self.pid)
			while True:
				try:
					win32gui.ShowWindow(runninggames[self.pid][5].handle, win32con.SW_RESTORE) # TODO: (Maybe) Add alternative method using hide
					win32gui.SetForegroundWindow(runninggames[self.pid][5].handle)
					break
				except RuntimeError as e:
					print(e)
					if "not responding" in str(e):
						unsuspend_old(self.pid)
					elif "no active desktop" in str(e):
						continue
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle:
					print("no handle")
					continue
			fgcpause = 0
			self.returnbutton.config(text=f"Return to\n{runninggames[self.pid][0]}")
			print(f"Returned to {runninggames[self.pid][0]}")

		def gameclosed(self): # TODO: GUI Indication
			threading.Thread(target=safedeller, args=[self.pid], name="safedeller thread", daemon=1).start()
			self.destroy()

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
	managedgamesqueue = SafeQueue()

	runninggames = {} # {pid : [0: pname, 1: script state, 2: suspension state, 3: [gui, reutrnbutton, suspendbutton, window], 4: active, 5: window]}

	refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')
	fgcpause = 0
	safetodel = 1 # This is the lamest solution
	def processscanner():
		global fgcpause, safetodel
		processcache = set([])
		while script == True:
			currentprocesses =  set(win32process.EnumProcesses()) # TODO: Use delta for performance
			newprocesses = currentprocesses.difference(processcache)
			processcache = currentprocesses
			for game in managedgames:
				if game not in currentprocesses:
					managedgames[game].gameclosed()
			for process in newprocesses:
				try:
					if psutil.Process(process).name() in suspendlist:
						if process in managedgames:
							managedgames[process].focus = 1
						else:
							threading.Thread(target=lambda: managedgames.update({process: GameManager(process)}), name="Game Manager init", daemon=1).start()
				except psutil.NoSuchProcess:
					pass
			while fgcpause:
				time.sleep(0.2)
			time.sleep(5)

	def foregroundcheck():
		global fgcpause
		while script == True:
			while fgcpause:
				time.sleep(0.2)
			fgcpause = 1
			currentprocess = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
			for game in runninggames:
				if runninggames[game][1] == 1:
					if currentprocess == game:
						if runninggames[game][2] != 0:
							print("how did you do this")
							unsuspend_old(game)
					else:
						if runninggames[game][2] != 1:
							try:
								try:
									win32gui.ShowWindow(runninggames[game][5].handle, win32con.SW_MINIMIZE) # TODO: Do a better job
								except:
									pass
								win32gui.ShowWindow(runninggames[game][3][3].handle, win32con.SW_SHOW)
								win32gui.SetForegroundWindow(runninggames[game][3][3].handle)
							except pywintypes.error as e: # TODO: Do something else here
								print(e)
							suspend_old(game)
			fgcpause = 0
			time.sleep(0.3)
		

	def suspend(pid, log = 1):
		subprocess.run([".\pssuspend64", f"{pid}"], capture_output=1)
		if log == 1:
			print(f"Suspended {pid}")

	def unsuspend(pid, log = 1):
		subprocess.run([".\pssuspend64", "-r", f"{pid}"], capture_output=1)
		if log == 1:
			print(f"Unsuspended {pid}")

	def suspend_old(pid):
		runninggames[pid][3][2].config(text="Game\nSuspended", style="red.TButton")
		subprocess.run([".\pssuspend64", f"{pid}"], capture_output=1)
		runninggames[pid][2] = 1
		print(f"Suspended {runninggames[pid][0]}")

	def unsuspend_old(pid):
		runninggames[pid][3][2].config(text="Game\nRunning", style="green.TButton")
		subprocess.run([".\pssuspend64", "-r", f"{pid}"], capture_output=1)
		runninggames[pid][2] = 0
		print(f"Resumed {runninggames[pid][0]}")

	def safedeller(pid):
		global fgcpause
		while fgcpause: # TODO: Make this better
			time.sleep(0.2)
		fgcpause = 1
		del runninggames[pid]
		fgcpause = 0

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
	mainwindowitems = []
	mainwindowitems.append(ttk.Label(gui, text = "BGAS RUNNING", justify="center", font=("TkDefaultFont", 25)))
	# gui.bind("<Visibility>", rundelayed)
	mainwindowitems[0].pack()
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