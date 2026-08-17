import sys
import os

# cPanel Phusion Passenger WSGI Entry Point
INTERP = os.path.expanduser("~/virtualenv/app/3.11/bin/python")
if os.path.exists(INTERP):
    if sys.executable != INTERP:
        os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from app import app as application
