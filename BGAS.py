# TODO: Add gui, write suspend() and unsuspend(), use window title in gui, add gui icon

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them.")

import win32process, os, time, psutil, subprocess, tkinter, threading
from tkinter import ttk
from tkinter.messagebox import askokcancel
try:
	with open("games.txt","r") as f:
		suspendlist = list(filter(None, f.read().split("\n")))

	runninggames = {} # {pid : [pname, script state, suspension state, gui]}

	def processscanner():
		processes =  win32process.EnumProcesses()
		for process in processes:
			if psutil.Process(process).name() in suspendlist:
				runninggames[psutil.Process(process).pid] = [psutil.Process(process).name(), 1, -1, threading.Thread(target=guimaker, args=pid)]

	def foregroundcheck():
		currentprocess = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
		for game in runninggames:
			if runninggames[game][1] == 1:
				if currentprocess == game:
					if runninggames[game][2] != 0:
						unsuspend(game)
				else:
					if runninggames[game][2] != 1:
						suspend(game)
		
	def suspend(pid):
		subprocess.run([".\pssuspend64", f"{pid}"])
		runninggames[pid][2] = 1

	def unsuspend(pid):
		subprocess.run([".\pssuspend64", "-r", f"{pid}"])


	def guimaker(pid):
		def unsuspend():
			suspendbutton
			unsuspend(pid)
		def pause():
			runninggames[pid][1] = 0
		def kill():
			if askokcancel(title=f"Kill {runninggames[pid][0]}?", message=f"Killing {runninggames[pid][0]} will result in loss of unsaved data."):
				subprocess.run([".\pssuspend64", "-r", f"{pid}"])
				subprocess.run(["taskkill", "/PID", f"{pid}", "/T", "/F"])
		def updater():
			while running == 1:
				
				
		gui = tkinter.Tk()
		gui.title(f"{runninggames[pid][0]}\nSuspender")
		gui.geometry("250x350+1000+500")
		label = ttk.Label(gui, text = f"{runninggames[pid][0]}", justify="center", font=("TkDefaultFont", 24)).pack()
		suspendbutton = ttk.Button(gui, text=("Suspended" if runninggames[pid][2] else "Running"), bg=("red" if runninggames[pid][2] else "green"), command=unsuspend)
		scriptbutton = ttk.Button(gui, text=("Working" if runninggames[pid][1] else "Paused"), bg=("red" if runninggames[pid][1] else "green"), command=pause, justify="center")
		killbutton = ttk.Button(gui, text="Kill game", bg="black", fg="white", command=kill)
		running = 1
		updaterdaemon = threading.Thread(target=updater,daemon=1)
		gui.mainloop()
		running = 0
		time.sleep(1)

	def old():
		while True:
			currentprocess = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[1]
			if currentprocess != latchedpid[1]:
				try:
					pywinauto.Application().connect(process=os.getpid()).top_window().set_focus()
				except:
					print("You pressed the start button, you need to manually change the virtual desktop")
				os.system(".\pssuspend64 " + str(latchedpid[1]))
				print("Suspended " + latchedpid[0])
				inp = input("\nPress enter to switch to " + latchedpid[0] + ". 'q' stop the script with the game running. 'p' to pause the script with the game running. 'k' to kill the script and the game: ").lower()
				if inp == "q":
					os.system(".\pssuspend64 -r " + str(latchedpid[1]))
					break
				elif inp == "k":
					os.system(".\pssuspend64 -r " + str(latchedpid[1]))
					os.system("taskkill /PID " + str(latchedpid[1]) + " /T /F")
					break
				elif inp == "p":
					os.system(".\pssuspend64 -r " + str(latchedpid[1]))
					input("Press enter to resume the script.")
				else:
					os.system(".\pssuspend64 -r " + str(latchedpid[1]))
					try:
						pywinauto.Application().connect(handle=latchedpid[2]).top_window().set_focus()
					except Exception as e:
						print()
			time.sleep(0.5)

	latchedpid = processscanner()
	foregroundscanner()
except Exception as e:
	print(e)
	time.sleep(100)