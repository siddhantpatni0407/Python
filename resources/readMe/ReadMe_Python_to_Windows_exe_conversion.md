# How to Convert `system_internet_usage.py` to an Executable (.exe)

This guide will walk you through the process of converting your Python `.py` file (`system_internet_usage.py`) into an executable `.exe` file using **PyInstaller**. This allows you to distribute your Python application without requiring the user to have Python installed.

## Prerequisites

* **Python** (version 3.5 or higher)
* **PyInstaller** (to bundle your script as an executable)

### 1. Install Python

First, ensure that Python is installed on your system. If you haven't installed it yet:

1. Download and install Python from the [official Python website](https://www.python.org/downloads/).
2. During installation, make sure to check the box that says "Add Python to PATH."

### 2. Install PyInstaller

To create an `.exe` file, you'll need **PyInstaller**. You can install it using `pip`:

```bash
pip install pyinstaller
```

### 3. Navigate to Your Script's Directory

Open a terminal (Command Prompt or PowerShell on Windows) and navigate to the directory where your Python file (`system_internet_usage.py`) is located.

Example:

```bash
cd path\to\your\script
```

### 4. Create the Executable Using PyInstaller

Run the following command to create the `.exe` file:

```bash
pyinstaller --onefile --noconsole --icon=system_internet_usage_icon.ico system_internet_usage.py
```

#### Explanation of the command:

* `pyinstaller`: Runs the PyInstaller tool.
* `--onefile`: Packages everything into a single `.exe` file.
* `--noconsole`: Hides the command prompt window (for GUI applications).
* `--icon=system_internet_usage_icon.ico`: Adds a custom icon to the `.exe` file.
* `system_internet_usage.py`: Replace with the name of your Python script.

### 5. Locate the Executable

After running the command, PyInstaller will create a `dist` folder in the same directory. Inside that folder, you will find the `.exe` file.

Example:

```bash
cd dist
system_internet_usage.exe
```

### 6. Optional Customizations

#### Add an Icon to the Executable

To add a custom icon to your `.exe` file, use the `--icon` flag (already included in the command):

```bash
pyinstaller --onefile --noconsole --icon=system_internet_usage_icon.ico system_internet_usage.py
```

#### Hide the Command Prompt Window (for GUI applications)

If your script is a GUI application and you don't want a command prompt to appear when the executable runs, use the `--noconsole` flag (also included in the command above):

```bash
pyinstaller --onefile --noconsole system_internet_usage.py
```

### 7. Distribute the Executable

Now that you have your `.exe` file, you can distribute it to others. The `.exe` file will run on any Windows machine, even if Python is not installed.

### 8. Troubleshooting

* **Missing Libraries**: If you get errors about missing libraries when running the executable, you may need to include them manually in the packaging process using the `--add-data` option.

* **Large Executable Size**: The `.exe` file can be large because PyInstaller bundles all necessary libraries. To reduce the size, you can explore options like stripping the executable or using UPX (if compatible with your environment).

* **Antivirus Warnings**: Sometimes, antivirus software may flag the generated `.exe` as a false positive. Make sure to test the `.exe` on a clean machine or consider signing your executable with a digital certificate.

---

This README should guide users through the process of creating an executable from the `system_internet_usage.py` script. Let me know if you need anything added or modified!
