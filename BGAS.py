# TODO: Add gui, write suspend() and unsuspend(), 

try:
	import win32gui, pywinauto
except Exception as e:
	print("You don't have all the necessary module dependecies. Please install them.")

import win32process, os, time, psutil
try:
	with open("games.txt","r") as f:
		suspendlist = list(filter(None, f.read().split("\n")))

	runninggames = {} # {pid : [pname, script state, suspension state]}

	def processscanner():
		processes =  win32process.EnumProcesses()
		for process in processes:
			if psutil.Process(process).name() in suspendlist:
				runninggames[psutil.Process(process).pid] = [psutil.Process(process).name(), 1, -1]

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
		
	def unsuspend(pid):
		os.system(".\pssuspend64 -r " + str(latchedpid[1]))


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