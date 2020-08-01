/*
 * View model for OctoPrint-Lpt
 *
 * Author: Tom Vogl
 * License: AGPLv3
 */
$(function() {
    function LptViewModel(parameters) {
        var self = this;


        // assign the injected parameters, e.g.:
        self.settingsViewModel = parameters[0];
        self.printerStateViewModel = parameters[1];
       
        // TODO: Implement your plugin's view model here.
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */

    
     OCTOPRINT_VIEWMODELS.push({
        construct: LptViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "settingsViewModel","printerStateViewModel"  ],
        // Elements to bind to, e.g. #settings_plugin_LPT, #tab_plugin_LPT, ...
        elements: [ "#settings_plugin_LPT"  /* ... */ ]
    });
});
