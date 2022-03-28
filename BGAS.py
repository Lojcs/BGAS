# TODO: Add gui, write suspend() and unsuspend(), use window title in gui, add gui icon

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

	runninggames = {} # {pid : [pname, script state, suspension state, gui, active]}

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
					if psutil.Process(process).pid in runninggames:
						runninggames[psutil.Process(process).pid][4] = 1
					else:
						runninggames[psutil.Process(process).pid] = [psutil.Process(process).name(), 1, -1, threading.Thread(target=guimaker, args=[psutil.Process(process).pid], daemon=1).start(), 1]
			psrunning = 0
			time.sleep(10)

	def foregroundcheck():
		while script == 1:
			currentprocess = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
			for game in runninggames:
				if runninggames[game][1] == 1:
					if currentprocess == game:
						if runninggames[game][2] != 0:
							unsuspend(game)
					else:
						if runninggames[game][2] != 1:
							suspend(game)
			time.sleep(0.5)
		
	def suspend(pid):
		subprocess.run([".\pssuspend64", f"{pid}"])
		runninggames[pid][2] = 1

	def unsuspend(pid):
		subprocess.run([".\pssuspend64", "-r", f"{pid}"])
		runninggames[pid][2] = 0


	def guimaker(pid):
		def suspendtoggle():
			global updatepause
			while updaterunning == 1:
				continue
			updatepause = 1
			if runninggames[pid][2] == 0:
				suspend(pid)
			if runninggames[pid][2] == 1:
				unsuspend(pid)
		def pause():
			global updatepause
			global updaterunning
			print(updaterunning)
			while updaterunning == 1:
				print(3)
				continue
			updatepause = 1
			if runninggames[pid][1] == 0:
				print(7)
				runninggames[pid][1] = 1
			elif runninggames[pid][1] == 1:
				print(8)
				runninggames[pid][1] = 0
		def kill():
			if askokcancel(title=f"Kill {runninggames[pid][0]}?", message=f"Killing {runninggames[pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{pid}"])
				subprocess.run(["taskkill", "/PID", f"{pid}", "/T", "/F"])
				guikill()
		def updater(state):
			while running == 1:
				global updaterunning
				i = 0
				itemlist = [label, scriptbutton, suspendbutton]
				if updatepause == 1:
					continue
				updaterunning = 1
				for present in runninggames[pid]:
					time.sleep(1)
					print(present, state[i])
					if present != state[i]:
						if i == 0:
							itemlist[i].config(text=f"{runninggames[pid][0]}")
						elif i == 1:
							print("Suspended" if runninggames[pid][1] else "Running")
							itemlist[i].config(text=("Working" if runninggames[pid][1] else "Paused"), style=("redback.TButton" if runninggames[pid][1] else "greenback.TButton"))
						elif i == 2:
							itemlist[i].config(text=("Suspended" if runninggames[pid][2] else "Running"), style=("redback.TButton" if runninggames[pid][2] else "greenback.TButton"))
						elif i == 4:
							while psrunning == 1:
								continue
							if present[4] == 0:
								guikill()
					i += 1
				state = runninggames[pid]
				updaterunning = 0
				# time.sleep(1/refresh)
				time.sleep(3)
		def guikill():
			killbutton.config(style="wb.TButton")
			t = 3
			while t > 0:
				t -= 1
				killbutton.config(text=f"Game is closed, closing this window in {t}")
			gui.destroy()
		def guiclose():
			if askokcancel(title="Close Suspender Window?", message="Suspender won't work until you restart the game or the script."):
				runninggames[pid][3] = None
				runninggames[pid][1] = 0
				unsuspend(pid)
		gui = tkinter.Tk()
		style = ttk.Style()
		style.configure("redback.TButton", background="red")
		style.configure("greenback.TButton", background="green")
		style.configure("bw.TButton", background="black", foreground="white")
		style.configure("wb.TButton", background="white", foreground="black")
		gui.title(f"{runninggames[pid][0]}\nSuspender")
		gui.geometry("250x350+1000+500")
		label = ttk.Label(gui, text = f"{runninggames[pid][0]}", justify="center", font=("TkDefaultFont", 24))
		label.pack()
		suspendbutton = ttk.Button(gui, text=("Suspended" if runninggames[pid][2] else "Running"), style=("redback.TButton" if runninggames[pid][2] else "greenback.TButton"), command=suspendtoggle, default="active")
		suspendbutton.pack()
		aslabel = ttk.Label(gui, text = "Auto suspend", justify="center", font=("TkDefaultFont", 24))
		aslabel.pack()
		scriptbutton = ttk.Button(gui, text=("Working" if runninggames[pid][1] else "Paused"), style=("redback.TButton" if runninggames[pid][1] else "greenback.TButton"), command=pause)
		scriptbutton.pack()
		killbutton = ttk.Button(gui, text="Kill game", style="bw.TButton", command=kill)
		killbutton.pack()
		state = runninggames[pid]
		gui.protocol("WM_DELETE_WINDOW", guiclose)
		running = 1
		updaterunning = 0
		updatepause = 0
		updaterdaemon = threading.Thread(target=updater, args=[state], daemon=1).start()
		gui.mainloop()
		running = 0
		time.sleep(1)

	script = 1
	pss = threading.Thread(target=processscanner, daemon=1).start()
	fgc = threading.Thread(target=foregroundcheck, daemon=1).start()
	while True:
		if input("Enter 'k' to stop BGAS: ") == "k":
			sys.exit(0)
except Exception as e:
	if e != KeyboardInterrupt:
		time.sleep(10)