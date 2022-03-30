# TODO: use window title in gui, add gui icon, switch to game window, button shortcuts, layout improvements
# TODO: functions should aquire a lock before doing actions that might break others.
# TODO: "Continue" button
# BUG: line 27 pid not found after killing

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them.")

import win32process, sys, time, psutil, subprocess, tkinter, threading, win32api
from tkinter import ttk
from tkinter.messagebox import askokcancel
try:
	with open("games.txt","r") as f:
		suspendlist = list(filter(None, f.read().split("\n")))

	runninggames = {} # {pid : [0: pname, 1: script state, 2: suspension state, 3: gui, 4: active, 5: updatelock]}

	refresh = getattr(win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1), 'DisplayFrequency')

	def processscanner():
		global psrunning
		while script == 1:
			psrunning = 1
			for game in runninggames:
				runninggames[game][4] = 0
			processes =  win32process.EnumProcesses()
			for process in processes:
				if psutil.Process(process).name() in suspendlist:
					if process in runninggames:
						runninggames[process][4] = 1
					else:
						runninggames[process] = [psutil.Process(process).name(), 1, -1, threading.Thread(target=guimaker, args=[process], name=f"{psutil.Process(process).name()} window thread", daemon=1), 1, 0]
						runninggames[process][3].start()
			psrunning = 0
			time.sleep(1)

	def foregroundcheck():
		while script == 1:
			currentprocess = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
			for game in runninggames:
				if runninggames[game][1] == 1:
					if currentprocess == game:
						if runninggames[game][2] != 0:
							print("ff")
							unsuspend(game)
					else:
						if runninggames[game][2] != 1:
							suspend(game)
			time.sleep(0.5)
		
	def suspend(pid):
		while runninggames[pid][5]:
			continue
		subprocess.run([".\pssuspend64", f"{pid}"], capture_output=1)
		print(f"Suspended {runninggames[pid][0]}")
		runninggames[pid][5] = 1
		runninggames[pid][2] = 1
		runninggames[pid][5] = 0

	def unsuspend(pid):
		while runninggames[pid][5]:
			continue
		subprocess.run([".\pssuspend64", "-r", f"{pid}"], capture_output=1)
		print(f"Resumed {runninggames[pid][0]}")
		runninggames[pid][5] = 1
		runninggames[pid][2] = 0
		runninggames[pid][5] = 0


	def guimaker(pid):
		def suspendtoggle():
			if runninggames[pid][2] == 0:
				suspend(pid)
			elif runninggames[pid][2] == 1:
				unsuspend(pid)
		def pause():
			if runninggames[pid][1] == 0:
				while runninggames[pid][5]:
					continue
				runninggames[pid][5] = 1
				runninggames[pid][1] = 1
				runninggames[pid][5] = 0
				print(f"Resumed for {pid}")
			elif runninggames[pid][1] == 1:
				while runninggames[pid][5]:
					continue
				runninggames[pid][5] = 1
				runninggames[pid][1] = 0
				runninggames[pid][5] = 0
				print(f"Paused for {pid}")
		def kill():
			if askokcancel(title=f"Kill {runninggames[pid][0]}?", message=f"Killing {runninggames[pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{pid}"])
				subprocess.run(["taskkill", "/PID", f"{pid}", "/T", "/F"])
				gui.destroy()
		def updater(past):
			while True:
				i = 0
				itemlist = [label, scriptbutton, suspendbutton]
				if past == runninggames[pid][:-1]:
					continue
				for present in runninggames[pid][:-1]:
					while runninggames[pid][5]:
						continue
					if present != past[i]:
						runninggames[pid][5] = 1
						if i == 0:
							itemlist[i].config(text=f"{runninggames[pid][0]}")
						elif i == 1:
							itemlist[i].config(text=("Active" if runninggames[pid][1] else "Paused"), style=("green.TButton" if runninggames[pid][1] else "red.TButton"))
						elif i == 2:
							itemlist[i].config(text=("Suspended" if runninggames[pid][2] else "Running"), style=("red.TButton" if runninggames[pid][2] else "green.TButton"))
						elif i == 4:
							while psrunning == 1:
								continue
							if runninggames[pid][4] == 0:
								gui.destroy()
						runninggames[pid][5] = 0
					i += 1
				past = runninggames[pid][:-1]
				time.sleep(1/refresh)
				# time.sleep(0.5)
		def guiclose():
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				runninggames[pid][3] = None
				runninggames[pid][1] = 0
				unsuspend(pid)
				gui.destroy()
		gui = tkinter.Tk()
		style = ttk.Style()
		style.theme_use("default")
		style.configure("red.TButton", background="#EB4135", foreground="white", font=("TkDefaultFont", 16))
		style.map("red.TButton", background=[("active", "#FF4A3C"), ("focus", "#B9372D")])
		style.configure("green.TButton", background="#42A531", foreground="white", font=("TkDefaultFont", 16))
		style.map("green.TButton", background=[("active", "#5AC448"), ("focus", "#327B26")])
		style.configure("bw.TButton", background="#2F1319", foreground="white", font=("TkDefaultFont", 16))
		style.map("bw.TButton", background=[("active", "#BF405F"), ("focus", "#903048")])
		# style.configure("wb.TButton", background="white", foreground="black", font=("TkDefaultFont", 16))
		# style.map("wb.TButton", background=[("active", "#BF405F"), ("focus", "#BF405F")])
		gui.title(f"{runninggames[pid][0]}\nSuspender")
		gui.geometry("250x350+1000+500")
		label = ttk.Label(gui, text = f"{runninggames[pid][0]}", justify="center", font=("TkDefaultFont", 24))
		label.pack()
		suspendbutton = ttk.Button(gui, text=("Suspended" if runninggames[pid][2] else "Running"), style=("red.TButton" if runninggames[pid][2] else "green.TButton"), command=suspendtoggle, default="active")
		suspendbutton.pack()
		aslabel = ttk.Label(gui, text = "Auto suspend", justify="center", font=("TkDefaultFont", 24))
		aslabel.pack()
		scriptbutton = ttk.Button(gui, text=("Active" if runninggames[pid][1] else "Paused"), style=("green.TButton" if runninggames[pid][1] else "red.TButton"), command=pause)
		scriptbutton.pack()
		killbutton = ttk.Button(gui, text="Kill game", style="bw.TButton", command=kill)
		killbutton.pack()
		state = runninggames[pid]
		gui.protocol("WM_DELETE_WINDOW", guiclose)
		threading.Thread(target=updater, args=[state], name=f"{runninggames[pid][0]} update thread", daemon=1).start()
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