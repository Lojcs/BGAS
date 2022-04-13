Little script I made that suspends games when their windows aren't in focus to decrease CPU/GPU usage.

# Setup:

1. [Download and install Python 3.](https://www.python.org/downloads/) Make sure add to PATH is selected.

2. Install dependecies by running `pip install psutil, pywinauto` on a powershell/cmd window.

3. [Download PSTools Suite.](https://docs.microsoft.com/en-us/sysinternals/downloads/pstools)

4. Download .zip of the script, extract it.

5. Extract `pssuspend64.exe` from PSTools.zip to the same folder.

6. Make a text file called games.txt in the same folder and write the names of the executables you want the script to work on, one name each line.

# Usage

Run BGAS.py or elevator.py (BGAS w/administrator privilages) after you start a game. I recommend using elevator.py since the script randomly doesn't work for me if I run it as user. You should try putting the game in a seperate virtual desktop if it appears behind windowed applications.

[Reddit Comment Explaining More](https://www.reddit.com/r/pcgaming/comments/3cr573/comment/htx7pd5/?context=3)

BGAS Copyright (C) 2022  Lojcs
You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.