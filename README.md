# Castle Cows
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![trello board](https://img.shields.io/badge/todo%20board-trello-blue.svg)](https://trello.com/b/5BatIDc3/todo)
![modding docs](https://img.shields.io/badge/modding%20docs-COMING%20SOON-blue.svg)

## How to play:
Rulebook still unavailible. Will be put in game when the game is ready.

## Purpose:
Its a fun game
<br>You can beat other people at dairy farming
<br>You can make an overpowered cow farm
<br>You can sign a contract with the devil

## Play from source:
This is for playing Castle Cows without using PyInstaller to turn it into a binary.

You will need python 3.9+ (other versions cause errors)

Install the requirements in requirements.txt using
```
pip3 install -r requirements.txt
```
I would recommend doing the same for optional-requirements.txt if you're on windows (it allows for smooth gameplay)

Run the game with 
```
python3 main.py
```

## Build Instructions:
**NOTE: IF A `pip3` COMMAND DOES NOT WORK, TRY REPLACING IT WITH `py -m pip` OR `python3 -m pip` INSTEAD**

Install the requirements in requirements.txt using
```
pip3 install -r requirements.txt
```
Install pyinstaller with pip using
```
pip3 install PyInstaller
```
Use pyinstaller to build the main.py file
<br>For example, `py -m PyInstaller main.py --clean --F --noconsole`
- `--noconsole` is used to prevent console from appearing when launching
- `--clean` is used to prevent windows defender from falsely detecting it as a virus
- `-F` (shorthand for `--onefile`) makes it one file and removes ".dll" file clutter.

Then, drag images and sound folders into the "dist" folder.<br>
The "build" folder is not essential and can be deleted.

I usually have a batch script do all this for me and will not include it here

## Art disclaimer
In some of the art, I got lazy and started using scaled up emojis.
<br>These emojis are Microsoft emojis so if Microsoft is seeing this than pls dont sue me for using your emojis in my art.
<br>Also I made all the art using Paint 3D (also microsoft's)