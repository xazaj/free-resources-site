#!/usr/bin/env python3
"""Uppcoder entrypoint for the free-resources site.

Uppcoder's Python stacks run ``python3 -u app.py`` by default, and the portal
offers no place to set a custom start command. So this file is the entrypoint:
it just hands over to server.main(), which serves public/ on 0.0.0.0:$PORT
(default 8000) with the Python standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import main

if __name__ == "__main__":
    main()
