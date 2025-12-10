# Running Without Console Window

There are three methods to run the Spotify overlay without a console window on Windows:

## Method 1: Use the Batch File (Easiest)

1. Double-click `run_overlay.bat`
2. The overlay will start without a console window
3. Click the **X button** on the overlay to close it

## Method 2: Use the VBScript (Cleanest)

1. Double-click `run_overlay.vbs`
2. Completely silent - no console window at all
3. Click the **X button** on the overlay to close it

## Method 3: Create a Windows Shortcut

### Create the Shortcut:
1. Right-click on your desktop or in a folder
2. Select **New → Shortcut**
3. For the location, enter:
   ```
   C:\Path\To\Python\pythonw.exe "C:\Path\To\spotify_milkdrop_overlay.py"
   ```
   Replace the paths with your actual Python and script locations
   
4. Click **Next**
5. Name it "Spotify Overlay" (or whatever you like)
6. Click **Finish**

### Optional - Add an Icon:
1. Right-click the shortcut → **Properties**
2. Click **Change Icon**
3. Browse to find an icon (or use a Spotify icon if you have one)
4. Click **OK**

### Find Your Python Path:
Not sure where `pythonw.exe` is? Open a command prompt and run:
```
where pythonw
```

## Important Notes

- **pythonw.exe vs python.exe**: 
  - `python.exe` shows a console window
  - `pythonw.exe` runs without a console window (perfect for GUI apps)
  
- **Closing the overlay**: 
  - Click the **X button** in the top-right corner of the overlay
  - The overlay now has a visible close button (turns red on hover)
  
- **First run authentication**:
  - If you haven't authenticated yet, use `python.exe` or `run_overlay.bat` for the first time
  - After initial authentication, you can use `pythonw.exe` or the VBScript

## Troubleshooting

**Overlay doesn't start:**
- Make sure all files are in the same directory
- Verify Python is installed and in your PATH
- Check that `config.ini` has your Spotify credentials

**Can't find pythonw.exe:**
- It should be in the same directory as `python.exe`
- Try reinstalling Python and make sure to check "Add Python to PATH"

**Need to see error messages:**
- Run with `python.exe` instead of `pythonw.exe` to see console output
- Or check Windows Event Viewer for Python errors
