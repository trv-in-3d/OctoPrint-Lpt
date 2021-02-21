# OctoPrint-Lpt

**Summary:** OctoPrint Last Print Temp plugin will keep track of the last printed temp used by the printer.  Helpful to remind you if you need to purge that ABS filament in the nozzle before trying to print PLA.

Since I use a Prusa MMU, my goal is have the plugin automatically determine that the last print job used a higher-temp filament.
In auto mode, it will heat the hotend to that previous temp, execute a filament load for the first required filament, then perform a filament unload, and return the hotend to the temp required by the current gcode job.

In manual mode, it will simply warn the user that the last job was at a higher temp and offer to cancel the current job before it is started so the user can manually check/purge the hot end.


NOTE:  This is my first GIT repo, and my first attempt at python programming.

I am using Filament Manager for a lot of my inspiration https://github.com/OllisGit/OctoPrint-FilamentManager as well as Smart Preheat https://github.com/kantlivelong/OctoPrint-SmartPreheat/archive/master.zip.

**Warning:** This is not ready for release.  Use at your own risk.  

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/trv-in-3d/OctoPrint-Lpt/archive/master.zip



## Configuration

**Customize** View the plug-in settings to customize the behaviour.
