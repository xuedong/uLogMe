#!/usr/bin/env python
# -*- coding: utf8 -*-
# export_events.py for https://github.com/Naereen/uLogMe/
# MIT Licensed, https://lbesson.mit-license.org/
#
from __future__ import print_function  # Python 2 compatibility

import json
import os
import os.path
import glob


# Import a printc function to use ANSI colors in the stdout output
try:
    try:
        from ansicolortags import printc
    except ImportError:
        print("Optional dependancy (ansicolortags) is not available, using regular print function.")
        print("  You can install it with : 'pip install ansicolortags' (or sudo pip)...")
        from ANSIColors import printc
except ImportError:
    print("Optional dependancy (ANSIColors) is not available, using regular print function.")
    print("  You can install it with : 'pip install ANSIColors-balises' (or sudo pip)...")

    def printc(*a, **kw):
        """ Fake function printc.

        ansicolortags or ANSIColors are not installed...
        Install ansicolortags from pypi (with 'pip install ansicolortags')
        """
        print(*a, **kw)


def loadEvents(fname):
    """
    Reads a file that consists of first column of unix timestamps
    followed by arbitrary string, one per line. Outputs as dictionary.
    Also keeps track of min and max time seen in global mint,maxt
    """
    events = []

    try:
        try:  # We have a bytes, as in Python2
            with open(fname, "r") as f:
                ws = f.read().decode("utf-8").splitlines()
        except AttributeError:  # We have a string, as in Python3
            with open(fname, "r") as f:
                ws = f.read().splitlines()
        events = []
        for w in ws:
            ix = w.find(" ")  # find first space, that's where stamp ends
            stamp = int(w[:ix])
            sstr = w[ix + 1:]
            events.append({"t": stamp, "s": sstr})
    except Exception as e:
        printc("The file '<black>%s<reset>' probably <red>does not exist<reset>, setting empty events list ..." % (fname, ))
        printc("<red>error was:<reset>")
        print(e)
        events = []
    return events


def mtime(f):
    """ Returns time file was last modified, or 0 if it does not exist. """
    if os.path.isfile(f):
        return int(os.path.getmtime(f))
    else:
        return 0


def updateEvents():
    """ Goes down the list of .txt log files and writes all .json files that can be used by the frontend. """
    logFiles = []
    logFiles.extend(glob.glob(os.path.join("..", "logs", "keyfreq_*.txt")))
    logFiles.extend(glob.glob(os.path.join("..", "logs", "window_*.txt")))
    logFiles.extend(glob.glob(os.path.join("..", "logs", "notes_*.txt")))
    logFiles = [f for f in logFiles if not os.path.islink(f)]

    # extract all times. all log files of form {type}_{stamp}.txt
    ts = [int(x[x.find("_") + 1: x.find(".txt")]) for x in logFiles]
    ts = list(set(ts))
    ts.sort()

    mint = min(ts)

    # march from beginning to end, group events for each day and write json
    ROOT = ""
    RENDER_ROOT = os.path.join(ROOT, "..", "render")
    # DONE in a more Pythonic way
    if not os.path.isdir(RENDER_ROOT):
        os.makedirs(RENDER_ROOT)
    t = mint
    out_list = []
    for t in ts:
        t0 = t
        t1 = t0 + 60 * 60 * 24  # 24 hrs later
        fout = os.path.join("json", "events_%d.json" % (t0, ))
        out_list.append({"t0": t0, "t1": t1, "fname": fout})

        fwrite = os.path.join(RENDER_ROOT, fout)
        e1f = os.path.join("..", "logs", "window_%d.txt" % (t0, ))
        e2f = os.path.join("..", "logs", "keyfreq_%d.txt" % (t0, ))
        e3f = os.path.join("..", "logs", "notes_%d.txt" % (t0, ))
        e4f = os.path.join("..", "logs", "blog_%d.txt" % (t0, ))

        dowrite = False

        # output file already exists?
        # if the log files have not changed there is no need to regen
        if os.path.isfile(fwrite):
            tmod = mtime(fwrite)
            e1mod = mtime(e1f)
            e2mod = mtime(e2f)
            e3mod = mtime(e3f)
            e4mod = mtime(e4f)
            if e1mod > tmod or e2mod > tmod or e3mod > tmod or e4mod > tmod:
                dowrite = True  # better update!
                printc("<yellow>A log file has changed<reset>, so will update '<black>%s<reset>' ..." % (fwrite, ))
        else:
            # output file does not exist, so write.
            dowrite = True

        if dowrite:
            # okay lets do work
            e1 = loadEvents(e1f)
            e2 = loadEvents(e2f)
            e3 = loadEvents(e3f)
            for k in e2:
                k["s"] = int(k["s"])  # int convert

            e4 = ""
            if os.path.isfile(e4f):
                e4 = open(e4f, "r").read()

            eout = {
                "window_events": e1,
                "keyfreq_events": e2,
                "notes_events": e3,
                "blog": e4
            }
            # print("eout =", eout)  # DEBUG
            with open(fwrite, "w") as f:
                try:
                    f.write(json.dumps(eout).encode("utf8"))
                except TypeError:
                    f.write(json.dumps(eout))

    render_json_path = os.path.join(RENDER_ROOT, "json")
    if not os.path.isdir(render_json_path):
        if os.path.exists(render_json_path):
            raise ValueError("Error: the file '{}' already exists but it is not a directory, impossible to create it! Remove it or rename it manually please...")
        else:
            print("The path '{}' did not exists but it is needed to export the list of events to a JSON file...\nCreating it...")
            os.mkdir(render_json_path)
    assert os.path.exists(render_json_path), "Error: the path '{}' do not exist but it should. Try again (or fill an issue, https://github.com/Naereen/uLogMe/issues/new)."  # DEBUG
    fwrite = os.path.join(render_json_path, "export_list.json")
    with open(fwrite, "w") as f:
        try:  # We have a bytes, as in Python2
            f.write(json.dumps(out_list).encode("utf8"))
        except TypeError:  # We have a string, as in Python3
            f.write(json.dumps(out_list))


# invoked as script
if __name__ == "__main__":
    updateEvents()
