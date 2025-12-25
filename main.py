# Vision Robot 2026
# By Tomasz Golaszewski
# 12.2025 -


import os
from sys import path

# check the system and add files to path
if os.name == "posix":
    path.append('./src')
    print("Linux")
elif os.name == "nt":
    path.append('.\\src')
    print("Windows")
else:
    path.append('.\\src')
    print("other")

# from settings import *
# from global_variables import *
# from classes_scenes import TitleScene
# from game_engine.scenes import run_game


if __name__ == "__main__":
    # run_game(TitleScene, WIN_WIDTH, WIN_HEIGHT, FRAMERATE, "Tanks 2025", os.path.join(*ICON_PATH))
    pass