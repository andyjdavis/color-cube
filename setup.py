from cx_Freeze import setup,Executable

includefiles = ['resources/suck.wav','resources/zap.wav','resources/barrier.wav','resources/yeah.wav','resources/music.mp3']

build_exe_options = {"packages": ["os"], "excludes": ["tkinter"], 'include_files':includefiles}

setup(
    name = 'ColorCube',
    version = '1.0',
    description = 'A game about a colorless cube',
    author = 'Andrew Davis',
    options = {"build_exe": build_exe_options}, 
	executables = [Executable(script="main.py", base="Win32GUI", icon = "ColorCube.ico", targetName="ColorCube.exe")]
)
