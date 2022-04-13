# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

# TODO: use window title in gui, add gui icon
# TODO: functions should aquire a lock before doing actions that might break others.
# TODO: Auto switch back (?)
# TODO: Better layout
# TODO: Use a class instead of lists in runninggames.
# TODO: Script uses too much cpu (kinda solved)
# TODO: Script starting delay to let games start
# BUG: Secondary window has no styling.
# BUG: Auto switching back to gui window stops working work if you alt tab too fast after pressing the return button.
# TODO: To add support for multiple windows, run only the mainloop in seperate thread, consider using mttkinter.

# BUG: Script stalls if restarted while a game is running

# Version 3.a1

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them by running 'pip install win32gui, pywinauto'")

import win32process, sys, os, time, psutil, subprocess, tkinter, threading, win32api, win32con, subprocess, pywintypes
from tkinter import ttk
from tkinter.messagebox import askokcancel
try:
	with open("games.txt","r") as f:
		suspendlist = list(filter(None, f.read().split("\n")))

	runninggames = {} # {pid : [0: pname, 1: script state, 2: suspension state, 3: [gui, reutrnbutton, suspendbutton, window], 4: active, 5: window]}

	refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')
	fgcpause = 0
	def processscanner():
		global fgcpause
		while script == 1:
			for game in runninggames:
				runninggames[game][4] = 0
			processes =  win32process.EnumProcesses() # TODO: Use delta for performance
			try:
				for process in processes:
					if psutil.Process(process).name() in suspendlist:
						if process in runninggames:
							runninggames[process][4] = 1
						else:
							while fgcpause:
								time.sleep(0.2)
							fgcpause = 1
							runninggames[process] = [psutil.Process(process).name(), 1, -1, [], 1, None]
							while subprocess.Popen(f'tasklist /FI "PID eq {process}" /FI "STATUS eq RUNNING"', stdout=subprocess.PIPE).stdout.read() == b"INFO: No tasks are running which match the specified criteria.\r\n":
								subprocess.run([".\pssuspend64", "-r", f"{process}"], capture_output=1)
								print("Trying to resume process") # TODO: Ui, timeout and suggestion to kill 
							threading.Thread(target=guimaker, args=[process], name=f"{psutil.Process(process).name()} window thread", daemon=1).start()
							while runninggames[process][3] == []:
								time.sleep(0.2)
							runninggames[process][3][3] = pywinauto.Application().connect(process=os.getpid()).top_window()
							fgcpause = 0
							print(f"Ui initialised for {runninggames[process][0]}")
							runninggames[process][3][1].config(text=f"Return to\n{runninggames[process][0]}", default="normal") # TODO: Disable all buttons and special text for other window initialising
			except psutil.NoSuchProcess:
				pass
			for game in runninggames:
				if runninggames[game][4] == 0:
					runninggames[game][3][0].destroy()
			time.sleep(5)

	def foregroundcheck():
		global fgcpause
		while script == 1:
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
								win32gui.ShowWindow(runninggames[game][5].handle, win32con.SW_HIDE)
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


	def guimaker(pid):
		def returntogame():
			global fgcpause
			fgcpause = 1
			returnbutton.config(text="Returning")
			unsuspend(pid)
			while True:
				try:
					win32gui.ShowWindow(runninggames[pid][5].handle, win32con.SW_SHOW)
					win32gui.SetForegroundWindow(runninggames[pid][5].handle)
					break
				except RuntimeError as e:
					print(e)
					if "not responding" in str(e):
						unsuspend(pid)
					elif "no active desktop" in str(e):
						continue
				except pywinauto.controls.hwndwrapper.InvalidWindowHandle:
					print("no handle")
					continue
			fgcpause = 0
			returnbutton.config(text=f"Return to\n{runninggames[pid][0]}")
			print(f"Returned to {runninggames[pid][0]}")
		def suspendtoggle():
			if runninggames[pid][2] == 0:
				suspend(pid)
			elif runninggames[pid][2] == 1:
				unsuspend(pid)
		def pausetoggle():
			if runninggames[pid][1] == 0:
				scriptbutton.config(text="Auto\nActive", style="green.TButton")
				runninggames[pid][1] = 1
				print(f"Script resumed for {runninggames[pid][0]}")
			elif runninggames[pid][1] == 1:
				scriptbutton.config(text="Auto\nPaused", style="red.TButton")
				runninggames[pid][1] = 0
				print(f"Script paused for {runninggames[pid][0]}")
		def kill():
			if askokcancel(title=f"Kill {runninggames[pid][0]}?", message=f"Killing {runninggames[pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{pid}"])
				subprocess.run(["taskkill", "/PID", f"{pid}", "/T", "/F"])
				gui.destroy()
		def guiclose():
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				unsuspend(pid)
				runninggames[pid][3] = []
				runninggames[pid][1] = 0
				gui.destroy()

		def returnbuttonpress(event): # TODO: Add visual change
			threading.Thread(target=returntogame).start()
		def suspendbuttonpress(event): # TODO: Add visual change
			suspendtoggle()
		def scriptbuttonpress(event): # TODO: Add visual change
			pausetoggle()
		def killbuttonpress(event): # TODO: Add visual change
			kill()
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

		gui.title(f"{runninggames[pid][0]}\nSuspender")
		gui.geometry("250x350+1000+500")
		gui.resizable(0,0)
		label = ttk.Label(gui, text = f"{runninggames[pid][0]}", justify="center", font=("TkDefaultFont", 20))
		returnbutton = ttk.Button(gui, text="Initialising", style="main.TButton", command=lambda : threading.Thread(target=returntogame, daemon=1).start(), default="disabled") # Do I need lambda here??
		suspendbutton = ttk.Button(gui, text=("Game\nSuspended" if runninggames[pid][2] else "Game\nRunning"), style=("red.TButton" if runninggames[pid][2] else "green.TButton"), command=suspendtoggle)
		scriptbutton = ttk.Button(gui, text=("Auto\nActive" if runninggames[pid][1] else "Auto\nPaused"), style=("green.TButton" if runninggames[pid][1] else "red.TButton"), command=pausetoggle)
		killbutton = ttk.Button(gui, text="Kill game", style="bw.TButton", command=kill)
		returnbutton.bind("<Return>", returnbuttonpress)
		suspendbutton.bind("<Return>", suspendbuttonpress)
		scriptbutton.bind("<Return>", scriptbuttonpress)
		killbutton.bind("<Return>", killbuttonpress)
		label.pack()
		returnbutton.pack()
		suspendbutton.pack()
		scriptbutton.pack()
		killbutton.pack()
		returnbutton.focus_set()

		gui.protocol("WM_DELETE_WINDOW", guiclose)
		runninggames[pid][3] = [gui, returnbutton, suspendbutton, None]
		runninggames[pid][5] = pywinauto.Application().connect(process=pid).top_window()
		gui.mainloop()
		time.sleep(1)

	script = 1
	pss = threading.Thread(target=processscanner, name="processscanner thread", daemon=1).start()
	fgc = threading.Thread(target=foregroundcheck, name="foregroundcheck thread", daemon=1).start()
	while True:
		if input("Enter 'k' to stop BGAS: ") == "k":
			sys.exit(0)
except Exception as e:
	if e != KeyboardInterrupt:
		time.sleep(10)