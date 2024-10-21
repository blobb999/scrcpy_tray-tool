![DALL·E 2024-10-21 01 26 03 - Create a simple, modern icon representing the concept of Android screen mirroring using the scrcpy tool  The icon should include an abstract depiction](https://github.com/user-attachments/assets/d182d404-da4f-4417-b89a-c5bdd55d3fe6)
scrcpy Tray-Tool
Description

The scrcpy Tray-Tool is a simple GUI application that manages the Android screen mirroring process via scrcpy. The program provides a graphical user interface (GUI) to display key information about the connected Android device, such as USB details, renderer, audio configurations, and texture sizes.

The program is controlled via a tray icon, allowing you to minimize it while keeping it running. It also displays essential information, normally seen in the GUI, within the tray icon tooltip.
Features

    Start and stop scrcpy directly from the GUI or the tray icon.
    Real-time display of information about your Android device:
        USB details
        Renderer
        Audio status
        Texture size (screen resolution)
        Mouse position and clicks within the mirrored screen.
    Minimize the application to the system tray instead of closing.
    Exit the application only through the tray icon (by selecting "Quit").

Installation

    Clone the repository:

    bash

git clone https://github.com/blobb999/scrcpy_tray-tool.git

Install the dependencies:

bash

pip install -r requirements.txt

Run the program:

bash

    python scrcpy_tray-tool.py

Usage

    Launch the application.
    Select "Start Scrcpy" from the GUI or tray icon menu to mirror the Android device.
    Device information will be displayed in the GUI and the tray icon tooltip.
    To minimize the application, click the close ("X") button – the app will continue running in the background.
    Exit the application via the tray icon menu ("Quit").

Requirements

    Python 3.x
    scrcpy (automatically downloaded)
    Dependencies from requirements.txt (Pillow, pystray, pygetwindow, pynput)
	
Releases
    I uploaded a compiled release
	https://github.com/blobb999/scrcpy_tray-tool/releases/tag/scrcpy_Tray-Tool_V1.0


License

This project is licensed under the MIT License – see the LICENSE file for details.