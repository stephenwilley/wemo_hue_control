# WeMo Hue Control

### Description

Use a WeMo Light Switch to turn on or off Hue lights.
If you turn your Hue lights on or off by some other means, it will set the appropriate state of the WeMo switch.

The Hue lights must be wired always on (check your local regulations as to whether this is allowed).
You can either have the WeMo switch simply have no load on it, or you can use this to combo up simple and Hue lights.

### Status

Work in progress.  Currently just printing debug info.

### Prerequisites

WeMo bits requires ouimeaux from https://github.com/iancmcc/ouimeaux
Hue bits require PyPHue from https://github.com/rdespoiu/PyPHue
Also relies on Python polling module

Use `pip install ouimeaux pyphue polling`
