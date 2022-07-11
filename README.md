Little script I made that suspends games when their windows aren't in focus to decrease CPU/GPU usage. Windows only

# Setup:

1. [Download and install Python 3.](https://www.python.org/downloads/) Make sure add to PATH is selected.

2. Install dependecies by running `pip install win32gui, pywinauto, psutil` on a powershell/cmd window.

3. Make a text file called games.txt in the BGAS folder and write the names of the executables you want the script to work on, one name each line. You can keep adding to this file if you install new games, but you need to restart the script for it to take effect.

4. (Optional) Place a shortcut in %Appdata%\Microsoft\Windows\Start Menu\Programs\Startup to make it auto start at logon.

5. (Optional) Check the github page for future releases (Next major version will work seamlessly with some games without needing to use the return button)

# Usage

Run BGAS.py and minimize the main window. You can close that if you have to force quit out of BGAS. A managing window will appear when you launch a game. It will wait for the game to finish loading, then suspend it if it's in background. You can use the Return To Game button to switch back to your game. If you alt+tab from the game the script will automatically minimize and suspend it for you. If Loading Detection is active, the script will wait for the game to stop using the disk before suspending it, and resume it a couple times in background to make sure it's not loading anything. You can use the Suspension Toggle to manually suspend/unsuspend the game. When you're done with the game just close it normally, the window should close on its own. If it doesn't, try resuming the game by clicking the Suspension Toggle.

It should be compatible with most offline games, online games / games with anticheat might not like it tho. If it doesn't work on a game at all, try running the script as administrator by running administrator.py instead of BGAS.py. Compatibility is still in progress.

The script works with multiple games at once and consecutively, so I recommend leaving the main window minimized instead of closing and relaunching it every time you want to use it.

Report issues on GitHub if you experience them.

BGAS Copyright (C) 2022  Lojcs

You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.