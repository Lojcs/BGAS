# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# TODO: use window title in gui, add gui icon
# TODO: functions should aquire a lock before doing actions that might break others.
# TODO: Better layout
# TODO: Use a class instead of lists in runninggames.
# TODO: Script uses too much cpu (kinda solved)

# TODO: Seamless mode
# TODO: Use main window for config, option to minimize to tray
# TODO: Set as service to autostart
# TODO: Include dependecies
# TODO: Remove pssuspend64.exe dependecy requirement

# Version 2.0.4

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

	class SuspenderWindow(tkinter.Toplevel):
		def __init__(self, pid):
			self.pid = pid
			super().__init__()
			self.title(f"{runninggames[pid][0]}\nSuspender")
			self.geometry("250x350")
			self.resizable(0,0)
			self.label = ttk.Label(self, text = f"{runninggames[pid][0]}", justify="center", font=("TkDefaultFont", 20))
			self.returnbutton = ttk.Button(self, text="Initialising", style="main.TButton", command=lambda : threading.Thread(target=self.returntogame, daemon=1).start())
			self.suspendbutton = ttk.Button(self, text=("Game\nSuspended" if runninggames[pid][2] else "Game\nRunning"), style=("red.TButton" if runninggames[pid][2] else "green.TButton"), command=self.suspendtoggle)
			self.scriptbutton = ttk.Button(self, text=("Auto\nActive" if runninggames[pid][1] else "Auto\nPaused"), style=("green.TButton" if runninggames[pid][1] else "red.TButton"), command=self.pausetoggle)
			self.killbutton = ttk.Button(self, text="Kill game", style="bw.TButton", command=self.kill)
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
			self.protocol("WM_DELETE_WINDOW", self.guiclose)
			runninggames[pid][3] = [self, self.returnbutton, self.suspendbutton, None]

		def returntogame(self):
			global fgcpause
			fgcpause = 1
			if runninggames[self.pid][5] == None:
				self.returnbutton.config(text="Finding window")
				runninggames[self.pid][5] = pywinauto.Application().connect(process=self.pid).top_window()
			self.returnbutton.config(text="Returning")
			unsuspend(self.pid)
			while True:
				try:
					win32gui.ShowWindow(runninggames[self.pid][5].handle, win32con.SW_SHOW)
					win32gui.SetForegroundWindow(runninggames[self.pid][5].handle)
					break
				except RuntimeError as e:
					print(e)
					if "not responding" in str(e):
						unsuspend(self.pid)
					elif "no active desktop" in str(e):
						continue
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle:
					print("no handle")
					continue
			fgcpause = 0
			self.returnbutton.config(text=f"Return to\n{runninggames[self.pid][0]}")
			print(f"Returned to {runninggames[self.pid][0]}")
		def suspendtoggle(self):
			if runninggames[self.pid][2] == 0:
				suspend(self.pid)
			elif runninggames[self.pid][2] == 1:
				unsuspend(self.pid)
		def pausetoggle(self):
			if runninggames[self.pid][1] == 0:
				self.scriptbutton.config(text="Auto\nActive", style="green.TButton")
				runninggames[self.pid][1] = 1
				print(f"Script resumed for {runninggames[self.pid][0]}")
			elif runninggames[self.pid][1] == 1:
				self.scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				runninggames[self.pid][1] = 0
				print(f"Script paused for {runninggames[self.pid][0]}")
		def kill(self):
			if askokcancel(title=f"Kill {runninggames[self.pid][0]}?", message=f"Killing {runninggames[self.pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{self.pid}"])
				subprocess.run(["taskkill", "/PID", f"{self.pid}", "/T", "/F"])
				self.destroy()
		def guiclose(self):
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				unsuspend(self.pid)
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
			self.kill()


	runninggames = {} # {pid : [0: pname, 1: script state, 2: suspension state, 3: [gui, reutrnbutton, suspendbutton, window], 4: active, 5: window]}

	refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')
	fgcpause = 0
	def processscanner():
		global fgcpause
		while script == True:
			for game in runninggames:
				runninggames[game][4] = 0
			processes =  win32process.EnumProcesses() # TODO: Use delta for performance
			try:
				for process in processes:
					if psutil.Process(process).name() in suspendlist:
						if process in runninggames:
							runninggames[process][4] = 1
						else:
							threading.Thread(target=lambda:windowmaker(process), daemon=1).start()
			except psutil.NoSuchProcess:
				pass
			for game in runninggames:
				if runninggames[game][4] == 0:
					runninggames[game][3][0].destroy()
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
							unsuspend(game)
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
							suspend(game)
			fgcpause = 0
			time.sleep(0.3)
		
	def suspend(pid):
		runninggames[pid][3][2].config(text="Game\nSuspended", style="red.TButton")
		subprocess.run([".\pssuspend64", f"{pid}"], capture_output=1)
		runninggames[pid][2] = 1
		print(f"Suspended {runninggames[pid][0]}")

	def unsuspend(pid):
		runninggames[pid][3][2].config(text="Game\nRunning", style="green.TButton")
		subprocess.run([".\pssuspend64", "-r", f"{pid}"], capture_output=1)
		runninggames[pid][2] = 0
		print(f"Resumed {runninggames[pid][0]}")

	def windowmaker(process):
		runninggames[process] = [None, None, None, None, 1, None]
		global fgcpause
		if time.time() - scriptstart > 60:
			if debug == 0:
				print("Letting the game start up")
				time.sleep(60)
		while fgcpause:
			time.sleep(0.2)
		fgcpause = 1
		runninggames[process] = [psutil.Process(process).name(), 1, -1, [], 1, None]
		while subprocess.Popen(f'tasklist /FI "PID eq {process}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n":
			subprocess.run([".\pssuspend64", "-r", f"{process}"], capture_output=1)
			print("Trying to resume process") # TODO: Ui, timeout and suggestion to kill 
		threading.Thread(target=SuspenderWindow, args=[process], name=f"{psutil.Process(process).name()} window thread", daemon=1).start()
		while runninggames[process][3] == []:
			time.sleep(0.2)
		runninggames[process][3][3] = pywinauto.Application().connect(process=os.getpid()).top_window()
		fgcpause = 0
		print(f"Ui initialised for {runninggames[process][0]}")
		runninggames[process][3][1].config(text=f"Return to\n{runninggames[process][0]}", default="normal") # TODO: Disable all buttons and special text for other window initialising
	
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
	gui.title("Main Window")
	# gui.geometry("260x40+1000+500")
	gui.resizable(0,0)
	label = ttk.Label(gui, text = "BGAS RUNNING", justify="center", font=("TkDefaultFont", 25))
	# gui.bind("<Visibility>", rundelayed)
	label.pack()
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