# BGAS Copyright (C) 2022  Lojcs
# You should have received a copy of the GNU General Public License along with this program.  If not, see https://www.gnu.org/licenses.

import ctypes, os, sys
ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f"{os.getcwd()}\\BGAS.py", None, 1)