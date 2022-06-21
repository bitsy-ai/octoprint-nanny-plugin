/*
 * View model for OctoPrintNanny
 *
 * Author: Leigh Johnson, Bitsy AI Labs
 * License: AGPLv3
 */

// add more view models as needed 
// $(function() {
//     function AnotherPrintNannyViewModel(parameters) {
//         let self = this;
//         self.apiClient = null;
//     }

//     // assign the injected parameters, e.g.:
//     self.loginStateViewModel = parameters[0];
//     self.settingsViewModel = parameters[1];

//     OCTOPRINT_VIEWMODELS.push({
//         construct: PrintNannyViewModel,
//         // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
//         dependencies: [ "loginStateViewModel", "settingsViewModel"],
//         // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
//         elements: [ '#wizard_plugin_octoprint_nanny_2', '#settings_plugin_octoprint_nanny' ]

//     });
// });

/*
** 
** Helpers
**
*/

$(function () {
    function PrintNannyTabViewModel(parameters) {
        let self = this;

        self.showError = ko.observable(false);
        self.showStart = ko.observable(true);
        self.disableStart = ko.observable(false);
        self.errorMessages = ko.observableArray([])
        self.onAfterBinding = function () {
            initializeJanus(self)
        }

        self.error = function (msg) {
            console.error(msg);
            self.showError(true);
            self.errorMessages.push(msg);
        }

        self.nnstreamerStart = function () {
            self.showStart(false);
            OctoPrint.socket.sendMessage("plugin_octoprint_nanny_nnstreamer_start");
            startStream();
        }

        self.nnstreamerStop = function () {
            self.showStart(true);
            OctoPrint.socket.sendMessage("plugin_octoprint_nanny_nnstreamer_stop");
            stopStream();
        }

        // TODO enable pass messages to vue app
        // OctoPrint.socket.onMessage("*", function (message) {
        //     console.log(message);
        // })
    }

    PrintNannyTabViewModel.prototype.koDescendantsComplete = function (node) {
        $vm.$forceUpdate();
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannyTabViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: ['#tab_plugin_octoprint_nanny', '#navbar_plugin_octoprint_nanny']

    });
});


$(function () {
    function PrintNannySettingsViewModel(parameters) {

        let self = this;

    }



    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannySettingsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: ['#settings_plugin_octoprint_nanny', '#wizard_plugin_octoprint_nanny']

    });
});
