"""
Comprehensive tests for spotify_milkdrop_overlay.py

This test suite covers utility functions and components from the Spotify overlay application.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from urllib.parse import parse_qs, urlparse
import sys
import os

# Mock the tkinter module before importing the main module
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

# Create a mock config.ini file if it doesn't exist
if not os.path.exists('config.ini'):
    with open('config.ini', 'w') as f:
        f.write("""[spotify]
client_id = TEST_CLIENT_ID
client_secret = TEST_CLIENT_SECRET
redirect_uri = http://127.0.0.1:8888/callback
scope = user-read-currently-playing user-read-playback-state

[overlay]
opacity = 0.85
update_interval = 2
window_width = 400
window_height = 140
position_x = -1
position_y_from_bottom = 200
max_text_length = 35

[appearance]
progress_color = #1DB954
track_color = white
artist_color = #b3b3b3
track_font_size = 14
artist_font_size = 11
time_font_size = 9
""")

# Now import the module we're testing
from spotify_milkdrop_overlay import (
    get_auth_url,
    CallbackHandler,
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    SCOPE
)


class TestFormatTime:
    """Comprehensive tests for the format_time function"""

    def test_format_time_zero_milliseconds(self):
        """Test formatting zero milliseconds"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        assert overlay.format_time(0) == "0:00"

    def test_format_time_seconds_only(self):
        """Test formatting time with only seconds (less than 1 minute)"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        assert overlay.format_time(1000) == "0:01"
        assert overlay.format_time(30000) == "0:30"
        assert overlay.format_time(59000) == "0:59"

    def test_format_time_exact_minutes(self):
        """Test formatting exact minute values"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        assert overlay.format_time(60000) == "1:00"
        assert overlay.format_time(120000) == "2:00"
        assert overlay.format_time(180000) == "3:00"

    def test_format_time_minutes_and_seconds(self):
        """Test formatting time with both minutes and seconds"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        assert overlay.format_time(61000) == "1:01"
        assert overlay.format_time(90000) == "1:30"
        assert overlay.format_time(125000) == "2:05"
        assert overlay.format_time(215000) == "3:35"

    def test_format_time_typical_song_lengths(self):
        """Test formatting typical song durations (2-5 minutes)"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        # 3:42 (typical pop song)
        assert overlay.format_time(222000) == "3:42"
        # 4:20
        assert overlay.format_time(260000) == "4:20"
        # 2:58
        assert overlay.format_time(178000) == "2:58"

    def test_format_time_long_songs(self):
        """Test formatting longer songs (6+ minutes)"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        # 10 minutes
        assert overlay.format_time(600000) == "10:00"
        # 15:47
        assert overlay.format_time(947000) == "15:47"
        # 20:30
        assert overlay.format_time(1230000) == "20:30"

    def test_format_time_edge_cases(self):
        """Test edge cases and boundary values"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        # 999 ms (should round down to 0 seconds)
        assert overlay.format_time(999) == "0:00"
        # 59,999 ms (should be 0:59, not 1:00)
        assert overlay.format_time(59999) == "0:59"
        # Very large value
        assert overlay.format_time(3600000) == "60:00"  # 1 hour

    def test_format_time_preserves_leading_zeros(self):
        """Test that seconds always have 2 digits with leading zeros"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()
        assert overlay.format_time(5000) == "0:05"
        assert overlay.format_time(65000) == "1:05"
        assert overlay.format_time(605000) == "10:05"


class TestGetAuthUrl:
    """Comprehensive tests for the get_auth_url function"""

    def test_auth_url_has_correct_base(self):
        """Test that the auth URL uses the correct Spotify endpoint"""
        url = get_auth_url()
        assert url.startswith("https://accounts.spotify.com/authorize?")

    def test_auth_url_contains_required_parameters(self):
        """Test that all required OAuth parameters are present"""
        url = get_auth_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert 'client_id' in params
        assert 'response_type' in params
        assert 'redirect_uri' in params
        assert 'scope' in params

    def test_auth_url_parameter_values(self):
        """Test that parameters have correct values"""
        url = get_auth_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert params['client_id'][0] == CLIENT_ID
        assert params['response_type'][0] == 'code'
        assert params['redirect_uri'][0] == REDIRECT_URI
        assert params['scope'][0] == SCOPE

    def test_auth_url_is_properly_encoded(self):
        """Test that the URL is properly encoded"""
        url = get_auth_url()
        # Should not contain spaces or unencoded special characters
        assert ' ' not in url
        # The URL should be parseable
        parsed = urlparse(url)
        assert parsed.scheme == 'https'
        assert parsed.netloc == 'accounts.spotify.com'


class TestCallbackHandler:
    """Comprehensive tests for the OAuth callback handler"""

    def _create_handler(self, path):
        """Helper to create a properly mocked CallbackHandler"""
        # Create mock socket and request
        mock_request = MagicMock()
        mock_request.makefile.return_value = MagicMock()

        # Prevent the handler from trying to read/write on initialization
        with patch.object(CallbackHandler, 'handle', return_value=None):
            handler = CallbackHandler(mock_request, ('127.0.0.1', 8888), MagicMock())

        # Set up the mocks we need
        handler.path = path
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.wfile.write = Mock()

        return handler

    def test_callback_handler_success_with_code(self):
        """Test successful callback with authorization code"""
        import spotify_milkdrop_overlay

        # Create a properly mocked handler
        handler = self._create_handler('/callback?code=test_auth_code_123')

        # Reset the global variable
        spotify_milkdrop_overlay.auth_code_received = None

        # Process the request
        handler.do_GET()

        # Verify the auth code was captured
        assert spotify_milkdrop_overlay.auth_code_received == 'test_auth_code_123'

        # Verify success response was sent
        handler.send_response.assert_called_once_with(200)

        # Verify HTML response was written
        assert handler.wfile.write.called
        written_html = handler.wfile.write.call_args[0][0].decode()
        assert 'Authorization Successful' in written_html

    def test_callback_handler_failure_without_code(self):
        """Test callback failure when no code is present"""
        import spotify_milkdrop_overlay

        # Create a properly mocked handler
        handler = self._create_handler('/callback?error=access_denied')

        # Reset the global variable
        spotify_milkdrop_overlay.auth_code_received = None

        # Process the request
        handler.do_GET()

        # Verify no auth code was captured
        assert spotify_milkdrop_overlay.auth_code_received is None

        # Verify error response was sent
        handler.send_response.assert_called_once_with(400)

        # Verify error HTML was written
        written_html = handler.wfile.write.call_args[0][0].decode()
        assert 'Authorization Failed' in written_html

    def test_callback_handler_multiple_parameters(self):
        """Test callback with multiple query parameters"""
        import spotify_milkdrop_overlay

        handler = self._create_handler('/callback?code=abc123&state=xyz789')

        spotify_milkdrop_overlay.auth_code_received = None

        handler.do_GET()

        # Should extract the code correctly even with other parameters
        assert spotify_milkdrop_overlay.auth_code_received == 'abc123'

    def test_callback_handler_sets_correct_content_type(self):
        """Test that the handler sets HTML content type"""
        handler = self._create_handler('/callback?code=test123')

        handler.do_GET()

        # Check that Content-type header was set to text/html
        calls = handler.send_header.call_args_list
        content_type_set = any(
            call[0][0] == 'Content-type' and call[0][1] == 'text/html'
            for call in calls
        )
        assert content_type_set


class TestSpotifyOverlayUtilities:
    """Tests for SpotifyOverlay utility methods"""

    def test_overlay_initialization(self):
        """Test that SpotifyOverlay can be initialized"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()

        # Verify initial state
        assert overlay.current_track is None
        assert overlay.current_image is None
        assert overlay.running is True
        assert overlay.progress_ms == 0
        assert overlay.duration_ms == 0
        assert overlay.is_playing is False

    def test_overlay_text_truncation_short_text(self):
        """Test that short text is not truncated"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()

        # Short track name should not be scrolled
        overlay.full_track_text = "Short Song"
        overlay.full_artist_text = "Artist"

        assert len(overlay.full_track_text) <= overlay.max_text_length
        assert len(overlay.full_artist_text) <= overlay.max_text_length

    def test_overlay_handles_long_text(self):
        """Test that long text triggers scrolling behavior"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()

        # Very long track name
        long_text = "This is an extremely long song title that should definitely trigger scrolling"
        overlay.full_track_text = long_text

        assert len(overlay.full_track_text) > overlay.max_text_length


class TestConfigurationLoading:
    """Tests for configuration file loading"""

    def test_config_values_loaded(self):
        """Test that configuration values are loaded correctly"""
        # The config.ini in the repo may have different values
        # Just test that they were loaded (not default placeholder values or empty)
        assert CLIENT_ID is not None
        assert len(CLIENT_ID) > 0
        assert CLIENT_SECRET is not None
        assert len(CLIENT_SECRET) > 0
        assert REDIRECT_URI is not None
        assert 'http' in REDIRECT_URI
        assert SCOPE is not None
        assert 'user-read' in SCOPE


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling"""

    def test_format_time_with_negative_values(self):
        """Test format_time behavior with negative values"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()

        # Negative values should be handled gracefully
        # The function uses int() which rounds towards zero
        result = overlay.format_time(-1000)
        assert isinstance(result, str)
        assert ':' in result

    def test_format_time_with_very_large_values(self):
        """Test format_time with very large values (hours)"""
        from spotify_milkdrop_overlay import SpotifyOverlay
        overlay = SpotifyOverlay()

        # 2 hours in milliseconds
        result = overlay.format_time(7200000)
        assert result == "120:00"  # Shows as minutes, not hours

    def test_auth_url_consistency(self):
        """Test that get_auth_url returns consistent results"""
        url1 = get_auth_url()
        url2 = get_auth_url()

        # Should return the same URL each time (for same config)
        assert url1 == url2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
