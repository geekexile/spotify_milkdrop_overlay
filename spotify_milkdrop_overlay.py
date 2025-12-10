import tkinter as tk
from tkinter import ttk
import time
from threading import Thread
from PIL import Image, ImageTk
import requests
from io import BytesIO
import base64
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
import configparser
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Load configuration
config = configparser.ConfigParser()
config_file = 'config.ini'

if not os.path.exists(config_file):
    print(f"ERROR: {config_file} not found!")
    print("Please create config.ini with your Spotify API credentials.")
    sys.exit(1)

config.read(config_file)

# Spotify API Configuration from INI
CLIENT_ID = config.get('spotify', 'client_id')
CLIENT_SECRET = config.get('spotify', 'client_secret')
REDIRECT_URI = config.get('spotify', 'redirect_uri')
SCOPE = config.get('spotify', 'scope')

# Overlay settings from INI
OPACITY = config.getfloat('overlay', 'opacity', fallback=0.85)
UPDATE_INTERVAL = config.getint('overlay', 'update_interval', fallback=2)
WINDOW_WIDTH = config.getint('overlay', 'window_width', fallback=400)
WINDOW_HEIGHT = config.getint('overlay', 'window_height', fallback=140)
POSITION_X = config.getint('overlay', 'position_x', fallback=-1)
POSITION_Y_FROM_BOTTOM = config.getint('overlay', 'position_y_from_bottom', fallback=200)
MAX_TEXT_LENGTH = config.getint('overlay', 'max_text_length', fallback=35)

# Appearance settings from INI
PROGRESS_COLOR = config.get('appearance', 'progress_color', fallback='#1DB954')
TRACK_COLOR = config.get('appearance', 'track_color', fallback='white')
ARTIST_COLOR = config.get('appearance', 'artist_color', fallback='#b3b3b3')
TRACK_FONT_SIZE = config.getint('appearance', 'track_font_size', fallback=14)
ARTIST_FONT_SIZE = config.getint('appearance', 'artist_font_size', fallback=11)
TIME_FONT_SIZE = config.getint('appearance', 'time_font_size', fallback=9)

# Token storage
access_token = None
refresh_token = None
token_expires = 0

# Callback capture
auth_code_received = None


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to capture OAuth callback"""
    
    def do_GET(self):
        """Handle the OAuth callback"""
        global auth_code_received
        
        # Parse the URL to get the code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        if 'code' in params:
            auth_code_received = params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Spotify Authorization</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #191414; color: white;">
                <h1 style="color: #1DB954;">&#x2713; Authorization Successful!</h1>
                <p style="font-size: 18px;">You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            # Error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head><title>Spotify Authorization</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #191414; color: white;">
                <h1 style="color: #ff0000;">&#x2717; Authorization Failed</h1>
                <p style="font-size: 18px;">No authorization code received.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def wait_for_callback(port=8888, timeout=120):
    """Start a local server and wait for the OAuth callback"""
    global auth_code_received
    auth_code_received = None
    
    server = HTTPServer(('127.0.0.1', port), CallbackHandler)
    server.timeout = 1  # Check every second
    
    print(f"Waiting for authorization (timeout: {timeout} seconds)...")
    print("Complete the authorization in your browser.\n")
    
    start_time = time.time()
    while auth_code_received is None and (time.time() - start_time) < timeout:
        server.handle_request()
    
    if auth_code_received:
        return auth_code_received
    else:
        print("Timeout waiting for authorization.")
        return None


def get_auth_url():
    """Generate Spotify authorization URL"""
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    return f"https://accounts.spotify.com/authorize?{urlencode(params)}"


def get_token_from_code(auth_code):
    """Exchange authorization code for access token"""
    global access_token, refresh_token, token_expires
    
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        json_result = response.json()
        access_token = json_result['access_token']
        refresh_token = json_result.get('refresh_token')
        token_expires = time.time() + json_result['expires_in']
        return True
    return False


def refresh_access_token():
    """Refresh the access token using refresh token"""
    global access_token, token_expires
    
    if not refresh_token:
        return False
    
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        json_result = response.json()
        access_token = json_result['access_token']
        token_expires = time.time() + json_result['expires_in']
        return True
    return False


def get_auth_header():
    """Get authorization header, refreshing token if needed"""
    global access_token, token_expires
    
    # Check if token needs refresh
    if time.time() >= token_expires - 60:  # Refresh 1 minute before expiry
        if not refresh_access_token():
            raise Exception("Failed to refresh token")
    
    return {'Authorization': f'Bearer {access_token}'}


def get_current_track():
    """Get currently playing track with album art and progress"""
    headers = get_auth_header()
    url = "https://api.spotify.com/v1/me/player/currently-playing"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200 and response.text:
        data = response.json()
        
        if data and data.get('item'):
            track = data['item']
            
            # Get album art (largest image)
            album_art_url = None
            if track.get('album') and track['album'].get('images'):
                album_art_url = track['album']['images'][0]['url']
            
            return {
                'track': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'album_art_url': album_art_url,
                'progress_ms': data.get('progress_ms', 0),
                'duration_ms': track.get('duration_ms', 0),
                'is_playing': data.get('is_playing', False)
            }
    
    return None


class SpotifyOverlay:
    def __init__(self):
        self.root = tk.Tk()
        
        # Make window transparent and always on top
        self.root.attributes('-alpha', 0.0)  # Start invisible for fade-in
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        # Additional flags to stay on top of fullscreen apps
        try:
            # Windows-specific: Set as a tool window to stay on top
            self.root.attributes('-toolwindow', True)
        except:
            pass
        
        try:
            # Try to set window to be always on top even for fullscreen
            self.root.wm_attributes('-topmost', 1)
        except:
            pass
        
        # Set window size and position from config
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Calculate position
        if POSITION_X == -1:
            # Auto-center horizontally
            x = (screen_width - WINDOW_WIDTH) // 2
        else:
            x = POSITION_X
        
        y = screen_height - POSITION_Y_FROM_BOTTOM
        
        self.root.geometry(f'{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}')
        self.root.configure(bg='black')
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Album art on the left
        self.album_art_label = tk.Label(
            self.main_frame,
            bg='black',
            width=100,
            height=100
        )
        self.album_art_label.pack(side='left', padx=(0, 15))
        
        # Text and progress on the right
        self.info_frame = tk.Frame(self.main_frame, bg='black')
        self.info_frame.pack(side='left', fill='both', expand=True)
        
        self.track_label = tk.Label(
            self.info_frame,
            text="Waiting for Spotify...",
            font=('Arial', TRACK_FONT_SIZE, 'bold'),
            fg=TRACK_COLOR,
            bg='black',
            justify='left',
            anchor='w'
        )
        self.track_label.pack(anchor='w', pady=(5, 2), fill='x')
        
        self.artist_label = tk.Label(
            self.info_frame,
            text="",
            font=('Arial', ARTIST_FONT_SIZE),
            fg=ARTIST_COLOR,
            bg='black',
            justify='left',
            anchor='w'
        )
        self.artist_label.pack(anchor='w', pady=(0, 8), fill='x')
        
        # Progress bar frame
        self.progress_frame = tk.Frame(self.info_frame, bg='black')
        self.progress_frame.pack(fill='x', pady=(0, 2))
        
        # Custom progress bar using Canvas
        self.progress_canvas = tk.Canvas(
            self.progress_frame,
            height=4,
            bg='#404040',
            highlightthickness=0
        )
        self.progress_canvas.pack(fill='x')
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 4,
            fill=PROGRESS_COLOR,
            outline=''
        )
        
        # Time labels
        self.time_frame = tk.Frame(self.info_frame, bg='black')
        self.time_frame.pack(fill='x')
        
        self.current_time_label = tk.Label(
            self.time_frame,
            text="0:00",
            font=('Arial', TIME_FONT_SIZE),
            fg=ARTIST_COLOR,
            bg='black'
        )
        self.current_time_label.pack(side='left')
        
        self.total_time_label = tk.Label(
            self.time_frame,
            text="0:00",
            font=('Arial', TIME_FONT_SIZE),
            fg=ARTIST_COLOR,
            bg='black'
        )
        self.total_time_label.pack(side='right')
        
        # Close button
        self.close_button = tk.Label(
            self.main_frame,
            text="✕",
            font=('Arial', 16, 'bold'),
            fg='#666666',
            bg='black',
            cursor='hand2',
            padx=5
        )
        self.close_button.pack(side='right', anchor='ne')
        self.close_button.bind('<Button-1>', lambda e: self.close())
        self.close_button.bind('<Enter>', lambda e: self.close_button.config(fg='#ff0000'))
        self.close_button.bind('<Leave>', lambda e: self.close_button.config(fg='#666666'))
        
        # Track current song and state
        self.current_track = None
        self.current_image = None
        self.target_alpha = OPACITY
        self.current_alpha = 0.0
        self.is_fading = False
        
        # Text scrolling state
        self.full_track_text = ""
        self.full_artist_text = ""
        self.track_scroll_pos = 0
        self.artist_scroll_pos = 0
        self.max_text_length = MAX_TEXT_LENGTH  # Characters before scrolling kicks in
        self.scroll_paused = False
        self.scroll_pause_counter = 0
        
        # Progress tracking
        self.progress_ms = 0
        self.duration_ms = 0
        self.last_update = time.time()
        self.is_playing = False
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_spotify, daemon=True)
        self.monitor_thread.start()
        
        # Start progress update thread
        self.progress_thread = Thread(target=self.update_progress_loop, daemon=True)
        self.progress_thread.start()
        
        # Start text scrolling thread
        self.scroll_thread = Thread(target=self.scroll_text_loop, daemon=True)
        self.scroll_thread.start()
        
        # Allow dragging the window
        for widget in [self.main_frame, self.album_art_label, self.track_label, 
                       self.artist_label, self.info_frame]:
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)
        
    def start_drag(self, event):
        self.drag_x = event.x_root - self.root.winfo_x()
        self.drag_y = event.y_root - self.root.winfo_y()
        
    def on_drag(self, event):
        x = event.x_root - self.drag_x
        y = event.y_root - self.drag_y
        self.root.geometry(f'+{x}+{y}')
    
    def fade_in(self):
        """Smooth fade in animation"""
        if self.current_alpha < self.target_alpha and not self.is_fading:
            self.is_fading = True
            self.animate_fade(self.target_alpha, step=0.05)
    
    def fade_out(self, callback=None):
        """Smooth fade out animation"""
        if self.current_alpha > 0 and not self.is_fading:
            self.is_fading = True
            self.animate_fade(0, step=-0.05, callback=callback)
    
    def animate_fade(self, target, step=0.05, callback=None):
        """Animate opacity change"""
        if (step > 0 and self.current_alpha < target) or \
           (step < 0 and self.current_alpha > target):
            self.current_alpha = max(0, min(1.0, self.current_alpha + step))
            self.root.attributes('-alpha', self.current_alpha)
            self.root.after(20, lambda: self.animate_fade(target, step, callback))
        else:
            self.current_alpha = target
            self.root.attributes('-alpha', self.current_alpha)
            self.is_fading = False
            if callback:
                callback()
    
    def load_album_art(self, url):
        """Download and resize album art"""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"Error loading album art: {e}")
            return None
    
    def format_time(self, ms):
        """Convert milliseconds to MM:SS format"""
        seconds = int(ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def update_progress_bar(self):
        """Update the progress bar visual"""
        if self.duration_ms > 0:
            # Calculate progress with local time tracking for smoothness
            current_progress = self.progress_ms
            if self.is_playing:
                elapsed = (time.time() - self.last_update) * 1000
                current_progress = min(self.duration_ms, self.progress_ms + elapsed)
            
            progress_ratio = current_progress / self.duration_ms
            canvas_width = self.progress_canvas.winfo_width()
            bar_width = canvas_width * progress_ratio
            
            self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 4)
            self.current_time_label.config(text=self.format_time(current_progress))
    
    def update_progress_loop(self):
        """Background thread for smooth progress updates"""
        while self.running:
            if self.is_playing and self.duration_ms > 0:
                self.root.after(0, self.update_progress_bar)
            time.sleep(0.1)  # Update 10 times per second for smoothness
    
    def scroll_text_loop(self):
        """Background thread for scrolling long text"""
        while self.running:
            if not self.scroll_paused:
                # Scroll track name if needed
                if len(self.full_track_text) > self.max_text_length:
                    self.track_scroll_pos = (self.track_scroll_pos + 1) % (len(self.full_track_text) + 5)
                    self.update_scrolling_track()
                
                # Scroll artist name if needed
                if len(self.full_artist_text) > self.max_text_length:
                    self.artist_scroll_pos = (self.artist_scroll_pos + 1) % (len(self.full_artist_text) + 5)
                    self.update_scrolling_artist()
            
            time.sleep(0.15)  # Scroll speed (lower = faster)
    
    def update_scrolling_track(self):
        """Update scrolling track text display"""
        if len(self.full_track_text) > self.max_text_length:
            # Add padding for smooth loop
            padded_text = self.full_track_text + "     "
            
            # Get visible portion
            visible = padded_text[self.track_scroll_pos:self.track_scroll_pos + self.max_text_length]
            
            # Wrap around if needed
            if len(visible) < self.max_text_length:
                visible += padded_text[:self.max_text_length - len(visible)]
            
            self.root.after(0, lambda: self.track_label.config(text=f"♪ {visible}"))
    
    def update_scrolling_artist(self):
        """Update scrolling artist text display"""
        if len(self.full_artist_text) > self.max_text_length:
            # Add padding for smooth loop
            padded_text = self.full_artist_text + "     "
            
            # Get visible portion
            visible = padded_text[self.artist_scroll_pos:self.artist_scroll_pos + self.max_text_length]
            
            # Wrap around if needed
            if len(visible) < self.max_text_length:
                visible += padded_text[:self.max_text_length - len(visible)]
            
            self.root.after(0, lambda: self.artist_label.config(text=visible))
    
    def monitor_spotify(self):
        """Background thread to monitor Spotify"""
        while self.running:
            try:
                track_info = get_current_track()
                
                if track_info:
                    track_id = f"{track_info['track']}|{track_info['artist']}"
                    
                    # Check if track changed
                    if track_id != self.current_track:
                        # Fade out before changing
                        if self.current_track is not None:
                            self.fade_out(callback=lambda: self.change_track(track_info))
                        else:
                            self.change_track(track_info)
                    else:
                        # Just update progress info
                        self.progress_ms = track_info['progress_ms']
                        self.duration_ms = track_info['duration_ms']
                        self.is_playing = track_info['is_playing']
                        self.last_update = time.time()
                        
                        # Update total time if needed
                        self.root.after(0, lambda: self.total_time_label.config(
                            text=self.format_time(self.duration_ms)
                        ))
                else:
                    if self.current_track is not None:
                        self.fade_out(callback=self.clear_track)
                        
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(UPDATE_INTERVAL)
    
    def change_track(self, track_info):
        """Change to a new track with fade-in"""
        self.current_track = f"{track_info['track']}|{track_info['artist']}"
        
        # Store full text for scrolling
        self.full_track_text = track_info['track']
        self.full_artist_text = track_info['artist']
        
        # Reset scroll positions
        self.track_scroll_pos = 0
        self.artist_scroll_pos = 0
        
        # Load album art if available
        if track_info.get('album_art_url'):
            album_art = self.load_album_art(track_info['album_art_url'])
            if album_art:
                self.current_image = album_art
                self.update_album_art(album_art)
        
        # Update text (will be truncated or scrolled as needed)
        self.update_display(track_info['track'], track_info['artist'])
        
        # Update progress info
        self.progress_ms = track_info['progress_ms']
        self.duration_ms = track_info['duration_ms']
        self.is_playing = track_info['is_playing']
        self.last_update = time.time()
        
        # Update time labels
        self.root.after(0, lambda: self.total_time_label.config(
            text=self.format_time(self.duration_ms)
        ))
        
        # Fade in
        self.fade_in()
    
    def clear_track(self):
        """Clear track info"""
        self.current_track = None
        self.current_image = None
        self.progress_ms = 0
        self.duration_ms = 0
        self.is_playing = False
        self.full_track_text = ""
        self.full_artist_text = ""
        self.track_scroll_pos = 0
        self.artist_scroll_pos = 0
        self.update_display("No track playing", "")
        self.clear_album_art()
        self.root.after(0, lambda: self.progress_canvas.coords(self.progress_bar, 0, 0, 0, 4))
        self.root.after(0, lambda: self.current_time_label.config(text="0:00"))
        self.root.after(0, lambda: self.total_time_label.config(text="0:00"))
    
    def update_display(self, track, artist):
        """Update the text labels"""
        def update():
            # Truncate or prepare for scrolling
            if len(track) <= self.max_text_length:
                self.track_label.config(text=f"♪ {track}")
            else:
                # Will be handled by scroll thread
                self.track_label.config(text=f"♪ {track[:self.max_text_length]}...")
            
            if len(artist) <= self.max_text_length:
                self.artist_label.config(text=artist)
            else:
                # Will be handled by scroll thread
                self.artist_label.config(text=f"{artist[:self.max_text_length]}...")
        
        self.root.after(0, update)
    
    def update_album_art(self, photo):
        """Update the album art image"""
        def update():
            self.album_art_label.config(image=photo)
        self.root.after(0, update)
    
    def clear_album_art(self):
        """Clear the album art"""
        def update():
            self.album_art_label.config(image='')
        self.root.after(0, update)
    
    def close(self):
        """Clean shutdown"""
        self.running = False
        self.root.quit()
    
    def run(self):
        """Start the overlay"""
        print("Spotify Overlay with Album Art, Progress & Animations started!")
        print("- Left-click and drag to move")
        print("- Click the X button to close")
        print("- Smooth fade animations on track changes")
        print("- Real-time progress bar")
        self.root.mainloop()


def main():
    """Main entry point with authentication"""
    global access_token, refresh_token
    
    print("=== Spotify Milkdrop Overlay ===\n")
    
    # Check if credentials are configured
    if CLIENT_ID == "YOUR_CLIENT_ID_HERE" or CLIENT_SECRET == "YOUR_CLIENT_SECRET_HERE":
        print("ERROR: Please configure your Spotify API credentials in config.ini!")
        print("\nSteps:")
        print("1. Open config.ini in a text editor")
        print("2. Replace YOUR_CLIENT_ID_HERE with your actual Client ID")
        print("3. Replace YOUR_CLIENT_SECRET_HERE with your actual Client Secret")
        print("\nGet credentials at: https://developer.spotify.com/dashboard")
        return
    
    print(f"Configuration loaded from {config_file}")
    print(f"- Update interval: {UPDATE_INTERVAL} seconds")
    print(f"- Opacity: {OPACITY}")
    print(f"- Window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}\n")
    
    # Get authorization
    print("Opening browser for Spotify authentication...")
    auth_url = get_auth_url()
    webbrowser.open(auth_url)
    
    # Wait for callback automatically
    auth_code = wait_for_callback()
    
    if auth_code:
        print("\n✓ Authorization code received!")
        print("Authenticating...")
        
        if get_token_from_code(auth_code):
            print("✓ Authentication successful!\n")
            
            # Start the overlay
            overlay = SpotifyOverlay()
            overlay.run()
        else:
            print("✗ Authentication failed!")
    else:
        print("\n✗ No authorization code received.")
        print("Please try again and complete the authorization in your browser.")


if __name__ == "__main__":
    main()
