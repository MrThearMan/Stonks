"""Testserver for functional testing."""

import socket
import errno
from django.core.servers.basehttp import ThreadedWSGIServer
from django.test.testcases import LiveServerThread, QuietWSGIRequestHandler
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium.webdriver.chrome.webdriver import WebDriver, Options


__all__ = [
    "StaticLiveServerTestCase_Chrome"
]


class WSGIRequestHandler_IgnoreWSAECONNRESET(QuietWSGIRequestHandler):
    """Modify request handling to ignore/not log a certain error."""

    def handle_one_request(self):
        """Copy of WSGIRequestHandler.handle() but with different ServerHandler"""
        try:
            super().handle_one_request()
        except socket.error as e:
            if e.errno != errno.WSAECONNRESET:
                raise e


class LiveServerThread_IgnoreWSAECONNRESET(LiveServerThread):
    """Add modified request handler to the live server thread."""

    def _create_server(self):
        return ThreadedWSGIServer((self.host, self.port),
                                  WSGIRequestHandler_IgnoreWSAECONNRESET,
                                  allow_reuse_address=False)


class StaticLiveServerTestCase_Chrome(StaticLiveServerTestCase):
    """Test site functionality with a headless browser."""

    server_thread_class = LiveServerThread_IgnoreWSAECONNRESET
    headless = True

    @classmethod
    def setUpClass(cls):
        """Build browser instance for testing."""
        super().setUpClass()

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " \
                     "AppleWebKit/537.36 (KHTML, like Gecko) " \
                     "Chrome/88.0.4324.150 Safari/537.36"

        options = Options()
        if cls.headless:
            options.add_argument(f'--headless')
        options.add_argument(f'--user-agent={user_agent}')

        cls.browser = WebDriver(executable_path="chromedriver.exe", options=options)
        cls.browser.set_page_load_timeout(15)
        cls.browser.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        """Close browser after testing."""
        cls.browser.quit()  # noqa
        super().tearDownClass()

    def setUp(self):
        """Setup test by going to site index."""
        self.browser.get(self.live_server_url)