from cx_Freeze import setup,Executable

includefiles = ['resources/suck.wav','resources/zap.wav','resources/barrier.wav','resources/yeah.wav','resources/music.mp3']

build_exe_options = {"packages": ["os"], "excludes": ["tkinter"], 'include_files':includefiles}

setup(
    name = 'ColorCube',
    version = '0.1',
    description = 'A game about a colorless cube',
    author = 'Andrew Davis',
    options = {"build_exe": build_exe_options}, 
	executables = [Executable('main.py', targetName="ColorCube.exe")]
)