/*
* View model for OctoPrint-Lpt
*
* Author: Tom Vogl
* License: AGPLv3
*/
$(function() {
   function LptViewModel(parameters) {
       var self = this;
       self.settings = parameters[0];
       self.loginState = parameters[1];
       self.conectionState = parameters[2];
       self.isActive = function() {
           return self.connectionState.isOperational() && self.loginState.isUser();
       }
       
   
    OCTOPRINT_VIEWMODELS.push({
       construct: LptViewModel,
       // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
       dependencies: [ "settingsViewModel","loginStateViewModel","connectionViewModel"  ],
       // Elements to bind to, e.g. #settings_plugin_LPT, #tab_plugin_LPT, ...
       elements: [ "#sidebar_plugin_LPT"  /* ... */ ]
   });
});
