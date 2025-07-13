#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import tkinter
import urllib.parse
import webbrowser


def get_clipboard_text():
    tk = tkinter.Tk()
    tk.withdraw() # test
    return tk.clipboard_get()

def search_by_google(text):
    url = "http://www.google.com/#q=" + urllib.parse.quote(text)
    webbrowser.open_new_tab(url)

def main():
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = get_clipboard_text()

    search_by_google(text)

