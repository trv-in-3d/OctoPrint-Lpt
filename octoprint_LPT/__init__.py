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
import flask
import octoprint.plugin
import octoprint.plugins
import textwrap

from octoprint.events import Events


class LptPlugin(octoprint.plugin.StartupPlugin,
				octoprint.plugin.SettingsPlugin,
				octoprint.plugin.AssetPlugin,
				octoprint.plugin.TemplatePlugin,
				octoprint.plugin.EventHandlerPlugin):

	##~~ SettingsPlugin mixin

	def __init__(self):
		self.lastt = None
		self.deltat = None
		self.temp_data = dict(tools=dict(), bed=None, firsttool=None)
		self.lptactive = None
		self.purgeenabled = None
		self.default_purge_script = textwrap.dedent(
		"""
		M109 T{{ plugins.LPT.firsttool }} S{{ plugins.LPT.lastt }} 
		T{{ plugins.LPT.firsttool }} ;select tool - performs load
		M702 ; unload filament
		M109 T{{ plugins.LPT.firsttool }} R{{ plugins.LPT.firstt }} ;go back to first temp
	
		""") 		
		# M109 S{{ plugins.LPT.lastt }} ; Wait for hotend to reach last (higher) print temp
		
		# ;set tools to last (higher) print temp
		# {% for tool, temp in plugins.LPT.tools.items %}
		# M104 T{{ tool }} S{{ temp }} 
		# {% endfor %}
		
		# ; wait for tools
		# {% for tool, temp in plugins.LPT.tools.items %}
		# M109 T{{ tool }} S{{ temp }} 
		# {% endfor %}
		
		
		# T{{ plugins.LPT.currenttool }} ; select tool - performs load
		# M702 ; unload filament

		# {% for tool in plugins.LPT.tools.items %}
		# M104 T{{ tool }} S{{plugins.LPT.firstt }} 
		# {% endfor %}

		# {% for tool in plugins.LPT.tools.items %}
		# M10R T{{ tool }} R{{plugins.LPT.firstt }} 
		# {% endfor %}

		# """)

	def on_settings_initalized(self):
		self._logger.debug('Initalizing settings')
		scripts = self._settings.listScripts("gcode")
		if not "snippets/doLPTPurge" in scripts:
			self._logger.debug('Saving doLPTPurge snippet')
			script = self.default_purge_script
			self._settings.saveScript("gcode","snippets/doLPTPurge", u'' + script.replace("\r\n","\n").replace("\r","\n"))


	def on_settings_save(self, data):
		old_lptactive = self._settings.get(["lptactive"])
		old_purgeenabled = self._settings.get(["purgeenabled"])
		old_deltat = self._settings.get_int(["deltat"])
		old_lastt = self._settings.get_int(["lastt"])
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
		new_purgeenabled = self._settings.get(["purgeenabled"])
		new_lptactive = self._settings.get(["lptactive"])
		new_deltat = self._settings.get_int(["deltat"])
		new_lastt = self._settings.get_int(["lastt"])
		if not old_deltat==new_deltat:
			self._logger.debug("Settings saved.   Old deltaT={old_deltat}, New deltaT={new_deltat}".format(**locals()))
		if not old_lptactive==new_lptactive:
			self._logger.debug("Settings saved.  Active stauts changed from={old_lptactive}, to={new_lptactive}".format(**locals()))
		if not old_purgeenabled==new_purgeenabled:
			self._logger.debug("Settings Saved.  Purge status changed from {old_purgeenabled}, to={new_purgeenabled}".format(**locals()))
		if not old_lastt==new_lastt:
			self._logger.debug("Settings Saved.  Last temp value changed from {old_lastt}, to={new_lastt}".format(**locals()))


	def on_after_startup(self):
		self._logger.info("OctoPrint-LPT has been loaded.  Wow.")
		
		checkactive = self._settings.get(["lptactive"])
		self._logger.debug("LPT active: {checkactive}".format(**locals()))
		
		checkpurge = self._settings.get(["purgeenabled"])
		self._logger.debug("Purge enabled: {checkpurge}".format(**locals()))
		
		checkdeltat = self._settings.get_int(["deltat"])
		self._logger.debug("Current deltaT setting: {checkdeltat}".format(**locals()))
		
		checklastt = self._settings.get_int(["lastt"])
		self._logger.debug("Last printed temp setting: {checklastt}".format(**locals()))


	def get_settings_defaults(self):
		return dict(
			deltat = "6",
			lastt = "180",
			purgeenabled = False,
			purgecode = "M109 S@lastt ; Wait for hotend to reach last (higher) print temp \r\nT@tool ; select tool\r\nM702 ; unload filament\r\nM109 R@firstt ; wait for hotend to cool to first temp",
			lptactive = True
		)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=False),
			dict(type="sidebar" , icon="thermometer-half", custom_bindings=True, template="LPT_sidebar.jinja2")
		]

	def get_template_vars(self):
		return 	dict(
			lptactive=self._settings.get(["lptactive"]),
			lastt=self._settings.get(["lastt"]),
			purgeenabled=self._settings.get(["purgeenabled"])
		)

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


	def on_event(self, event, payload):
		if event == Events.PRINTER_STATE_CHANGED:
			self.on_printer_state_changed(payload)

	def on_printer_state_changed(self, payload):
		if payload['state_id'] == "FINISHING":
			if self.lastPrintState == "PRINTING":
				self._logger.debug("State changed to finishing - saving lastt")
				# save the settings
				# TO DO - save settings

		# update last print state
		self.lastPrintState = payload['state_id']


	def get_temps_from_file(self, selected_file):
		path_on_disk = octoprint.server.fileManager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, selected_file)

		temps = dict(tools=dict(), bed=None, firsttool=None)
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

					tempMatchs = octoprint.util.comm.regexes_parameters["floatS"].search(line)
					tempMatchr = octoprint.util.comm.regexes_parameters["floatR"].search(line)
					if tempMatchs:
						temp = int(tempMatchs.group("value"))
					if tempMatchr:
						temp = int(tempMatchr.group("value"))
					if (tempMatchs or tempMatchr):
						if gcode in ("M104", "M109"):
							self._logger.debug("Line %d: Tool %s = %s", lineNum, toolNum, temp)
							temps["tools"][toolNum] = temp
						elif gcode in ("M140", "M190"):
							self._logger.debug("Line %d: Bed = %s", lineNum, temp)
							temps["bed"] = temp
		
		temps["firsttool"] = currentToolNum
		self._logger.debug("Temperature data: %r", temps)
		return temps

	def run_purge(self,purgefirsttemp, purgelasttemp, purgetool):
		# get our code block from settings.
		purgecode = self._settings.get(["purgecode"])
		
		#replace firsttemp


		#replace lasttemp


		#replace tool


		#inject final code into script


	def find_print_temps(self, comm_instance, script_type, script_name, *args, **kwargs):
		if not script_type == "gcode":
			return None
		
		self.temp_data = None

		if script_name == 'beforePrintStarted':
			if not self._settings.get(["lptactive"]):
				self._logger.debug("LPT disabled.  Skipping checks.")
			else:
				self._logger.debug("LPT enabled.  Checking...")
				current_data = self._printer.get_current_data()

				if current_data['job']['file']['origin'] == octoprint.filemanager.FileDestinations.LOCAL:
					self.temp_data = self.get_temps_from_file(current_data['job']['file']['path'])

				deltat = self._settings.get_int(["deltat"])
				lastt = self._settings.get_int(["lastt"])
				tool = self.temp_data["firsttool"]
				firsttemp = int(self.temp_data["tools"][tool])
				if (firsttemp < (lastt - deltat)):
					self._logger.debug("**** LPT PURGE NEEDED ****")
					if self.purgeenabled == True:
						self._logger.debug("Starting purge")
						# Run the Purge process
						result = self.run_purge(firsttemp,lastt,tool)
						# TO DO
					else:
						self._logger.debug("Purge disbled.  Start manual prompt")
						# Purge inactive - use dialog to warn and optionally stop the print
						result = -1 # 
						# TO DO

		return (None, None, self.temp_data)

	def monitorprint(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		# watch printed gcode and if there is a non-zero temp change store the new value as last printed temp.
		if gcode and  (gcode == "M104" or gcode == "M109"):
			self._logger.debug("Printed Temp [{gcode}]: {cmd}".format(**locals()))
			foundtemp = re.match("M10[4|9]\s+[S|R](\d+)",cmd).group(1)			
			if foundtemp:
				if (int(foundtemp) > 0 ):
					self._logger.debug("Saving actual temp string: {foundtemp} ....".format(**locals()))
					#self.lastt == foundtemp
					self._settings.set(["lastt"],foundtemp)
					self._settings.save()
					self._logger.debug("...saved")

__plugin_name__ = "LPT Plugin"

__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LptPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.scripts": __plugin_implementation__.find_print_temps,
		"octoprint.comm.protocol.gcode.sent": __plugin_implementation__.monitorprint
	}

