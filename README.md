# Spotify Milkdrop Overlay

A transparent overlay that displays currently playing Spotify track information with album art, progress bar, and smooth fade animations - perfect for use with Milkdrop visualizations!

## Features

- 🎵 **Real-time track info** - Song title, artist, and album art
- 📊 **Progress bar** - Live playback progress with time display
- ✨ **Smooth animations** - Fade in/out transitions on track changes
- 🎨 **Transparent overlay** - Sits on top of Milkdrop without blocking the view
- 🖱️ **Draggable** - Left-click and drag to reposition
- 🎯 **Always on top** - Stays visible over fullscreen applications

## Installation

### 1. Install Python Packages

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests Pillow
```

### 2. Set Up Spotify API Credentials

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in:
   - **App Name:** Milkdrop Overlay (or whatever you like)
   - **App Description:** Display current track info
   - **Redirect URI:** `http://127.0.0.1:8888/callback` (NOT localhost!)
5. Click "Save"
6. Copy your **Client ID** and **Client Secret**

### 3. Configure the Application

Open `config.ini` in a text editor and update the Spotify credentials:

```ini
[spotify]
client_id = YOUR_CLIENT_ID_HERE        # Replace with your Client ID
client_secret = YOUR_CLIENT_SECRET_HERE  # Replace with your Client Secret
```

You can also customize other settings in the config file:
- `opacity` - Window transparency (0.0 to 1.0)
- `update_interval` - How often to check Spotify (in seconds)
- `progress_color` - Progress bar color (hex format)
- `track_color`, `artist_color` - Text colors
- Font sizes and window dimensions

## Usage

### First Run - Authentication

1. Run the script:
```bash
python spotify_milkdrop_overlay.py
```

2. A browser window will open asking you to authorize the app
3. Click "Agree" to grant permissions
4. **The script will automatically capture the authorization!**
5. You'll see a success page in your browser - you can close it
6. The overlay will start automatically

### Using the Overlay

Once authenticated:

- The overlay will appear at the bottom center of your screen
- **Left-click and drag** to reposition it anywhere
- **Click the X button** (top-right corner) to close it
- Start playing music on Spotify and watch it update in real-time!

### Running Without Console Window

See `RUNNING_WITHOUT_CONSOLE.md` for detailed instructions on:
- Using the included batch file (`run_overlay.bat`)
- Using the VBScript launcher (`run_overlay.vbs`)
- Creating a Windows shortcut with `pythonw.exe`

**Quick start (no console):**
```bash
# Use pythonw.exe instead of python.exe
pythonw spotify_milkdrop_overlay.py

# Or simply double-click: run_overlay.bat
```

### Running with Milkdrop

1. Start Milkdrop (standalone version 3.31 or compatible)
2. Run the overlay script
3. Position the overlay where you want it on screen
4. Enjoy your visualizations with live track info!

## Customization

All customization options are now in `config.ini`. Edit the file and restart the overlay to apply changes.

### Change Position

```ini
[overlay]
# -1 for auto-center, or specify exact X coordinate
position_x = -1
# Distance from bottom of screen
position_y_from_bottom = 200

# For top center:
position_y_from_bottom = 950  # Adjust based on your screen height

# For top right:
position_x = 1470  # Adjust based on your screen width
position_y_from_bottom = 950
```

### Change Opacity

```ini
[overlay]
opacity = 0.85  # 0.0 = invisible, 1.0 = fully opaque
```

### Change Colors

```ini
[appearance]
progress_color = #1DB954  # Spotify green (default)
# progress_color = #FF0000  # Red
# progress_color = #00FFFF  # Cyan

track_color = white       # Track name
artist_color = #b3b3b3    # Artist name (gray)
```

### Change Font Sizes

```ini
[appearance]
track_font_size = 14   # Track name
artist_font_size = 11  # Artist name  
time_font_size = 9     # Time stamps
```

### Change Update Speed

```ini
[overlay]
update_interval = 2  # Check Spotify every 2 seconds (default)
# update_interval = 1  # More frequent updates (more API calls)
# update_interval = 5  # Less frequent updates (fewer API calls)
```

## Troubleshooting

### "Authentication failed"
- Double-check your Client ID and Client Secret
- Make sure you copied the ENTIRE callback URL including `?code=...`
- Verify the Redirect URI in Spotify Dashboard is exactly: `http://localhost:8888/callback`

### "No track playing" constantly
- Make sure Spotify is actually playing music
- Check that you granted the required permissions during authentication
- Try re-authenticating by running the script again

### Overlay not visible
- Check if it's behind other windows
- Try adjusting the opacity (make it more opaque)
- Verify Spotify is playing - overlay fades out when no track is playing

### Album art not loading
- Check your internet connection
- Some tracks may not have album art available
- Try a different song

## Requirements

- Python 3.7+
- Active Spotify account (Free or Premium)
- Internet connection
- Windows, macOS, or Linux

## Notes

- The overlay uses Spotify's API which has rate limits, so don't set the update interval too low
- Token expires after 1 hour but automatically refreshes in the background
- Works with Spotify Desktop, Web Player, or Mobile (as long as you're playing on the same account)

## License

Feel free to modify and use as you wish!
