Little script I made that suspends games when their windows aren't in focus to decrease CPU/GPU usage.

# Setup:

1. [Download and install Python 3.](https://www.python.org/downloads/) Make sure add to PATH is selected.

2. Install dependecies by running `pip install psutil, pywinauto` on a powershell/cmd window.

3. [Download PSTools Suite.](https://docs.microsoft.com/en-us/sysinternals/downloads/pstools)

4. Download .zip of the script, extract it.

5. Extract `pssuspend64.exe` from PSTools.zip to the same folder.

6. Make a text file called games.txt in the same folder and write the names of the executables you want the script to work on, one name each line. You can keep adding to this file if you install new games.

7. (Optional) Place a shortcut in %Appdata%\Microsoft\Windows\Start Menu\Programs\Startup to make it auto start at logon.

8. (Optional) Check the github page for future releases (Next major version will work seamlessly without needing to use the return button)

# Usage

Run BGAS.py and minimize the window. When you launch a game a window will open after 60 seconds and your game will be suspended. You can use the return (enter) button to switch back to your game. If you alt+tab from the game the script will automatically minimize and suspend it for you. When you're done with the game just close it normally, the window will close on its own.

It should be compatible with most offline games, online games / games with anticheat might not like it tho. If it doesn't work on a game at all, try running the script as administrator by running administrator.py instead of BGAS.py.

Don't open two instances of the script at once.

Report issues on GitHub if you experience them.

BGAS Copyright (C) 2022  Lojcs

You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.