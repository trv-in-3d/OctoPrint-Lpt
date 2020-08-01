# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import re


import octoprint.plugin
import octoprint.plugins

class LptPlugin(octoprint.plugin.StartupPlugin,
				octoprint.plugin.SettingsPlugin,
				octoprint.plugin.AssetPlugin,
				octoprint.plugin.TemplatePlugin):

	##~~ SettingsPlugin mixin

	def __init__(self):
		self.lastt = None
		self.deltat = None
		self.temp_data = dict(tools=dict(), bed=None)

	def on_settings_save(self, data):
		old_deltat = self._settings.get_int(["deltat"])
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		new_deltat = self._settings.get_int(["deltat"])
		self._logger.debug("Settings saved.   Old Deltat={old_deltat}, New DeltaT={new_deltat}".format(**locals()))

	def on_after_startup(self):
		self._logger.info("OctoPrint-LPT has been loaded.  Wow.")
		checkdeltat = self._settings.get_int(["deltat"])
		self._logger.debug("Current deltat setting: {checkdeltat}".format(**locals()))
		checklastt = self._settings.get_int(["lastt"])
		self._logger.debug("Last printed temp setting: {checklastt}".format(**locals()))


	def get_settings_defaults(self):
		return dict(
			deltat = "6",
			lastt = "180",
			purgecode = "X"
		)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False),
			dict(type="sidebar" , custom_bindings=True, template="LPT_sidebar.jinja2")
		]
	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/LPT.js"],
			css=["css/LPT.css"],
			less=["less/LPT.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
		# for details.
		return dict(
			LPT=dict(
				displayName="LPT Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="trv-in-3d",
				repo="OctoPrint-Lpt",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/trv-in-3d/OctoPrint-Lpt/archive/{target_version}.zip"
			)
		)

	def get_temps_from_file(self, selected_file):
		path_on_disk = octoprint.server.fileManager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, selected_file)

		temps = dict(tools=dict(), bed=None)
		currentToolNum = 0
		lineNum = 0
		self._logger.debug("Parsing g-code file, Path=%s", path_on_disk)
		with open(path_on_disk, "r") as file:
			for line in file:
				lineNum += 1
				
				gcode = octoprint.util.comm.gcode_command_for_cmd(line)
				extrusionMatch = octoprint.util.comm.regexes_parameters["floatE"].search(line)
				if gcode == "G1" and extrusionMatch:
					self._logger.debug("Line %d: Detected first extrusion. Read complete.", lineNum)
					break

				if gcode and gcode.startswith("T"):
					toolMatch = octoprint.util.comm.regexes_parameters["intT"].search(line)
					if toolMatch:
						self._logger.debug("Line %d: Detected SetTool. Line=%s", lineNum, line)
						currentToolNum = int(toolMatch.group("value"))

				if gcode in ('M104', 'M109', 'M140', 'M190'):
					self._logger.debug("Line %d: Detected SetTemp. Line=%s", lineNum, line)

					toolMatch = octoprint.util.comm.regexes_parameters["intT"].search(line)
					if toolMatch:
						toolNum = int(toolMatch.group("value"))
					else:
						toolNum = currentToolNum

					tempMatch = octoprint.util.comm.regexes_parameters["floatS"].search(line)
					if tempMatch:
						temp = int(tempMatch.group("value"))

						if gcode in ("M104", "M109"):
							self._logger.debug("Line %d: Tool %s = %s", lineNum, toolNum, temp)
							temps["tools"][toolNum] = temp
						elif gcode in ("M140", "M190"):
							self._logger.debug("Line %d: Bed = %s", lineNum, temp)
							temps["bed"] = temp

		self._logger.debug("Temperatures: %r", temps)
		return temps

	def find_print_temps(self, comm_instance, script_type, script_name, *args, **kwargs):
		if not script_type == "gcode":
			return None

		if script_name == 'beforePrintStarted':
			current_data = self._printer.get_current_data()

			if current_data['job']['file']['origin'] == octoprint.filemanager.FileDestinations.LOCAL:
				self.temp_data = self.get_temps_from_file(current_data['job']['file']['path'])
		return (None, None, self.temp_data)

	def logtemps(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode and  (gcode == "M104" or gcode == "M109"):
			self._logger.debug("Printed Temp [{gcode}]: {cmd}".format(**locals()))
			foundtemp = re.match("M10[4|9]\s+S(\d+)",cmd).group(1)			
			if foundtemp:
				self._logger.debug("actual temp: {foundtemp}".format(**locals()))
				if int(foundtemp) > 0 :
					self.lastt == foundtemp
					# TO DO:     SAVE THIS value CHANGE.


__plugin_name__ = "LPT Plugin"

__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LptPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.scripts": __plugin_implementation__.find_print_temps,
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.logtemps
	}

