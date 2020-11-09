/*
 * View model for Bitsy Octoprint Nanny
 *
 * Author: Leigh Johnson
 * License: MIT
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
//         elements: [ '#wizard_plugin_print_nanny_2', '#settings_plugin_print_nanny' ]

//     });
// });

/*
** 
** Helpers
**
*/

$(function() {
    function PrintNannyTabViewModel(parameters) {
        let self = this;
        self.apiClient = null;

        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];
    }

    function getLatestPrediction(){
        const url = OctoPrint.getBlueprintUrl('print_nanny') + 'calibrate'

        OctoPrint.postJson(url, {})
        .done((res) =>{
                console.debug('Print Nanny verification success')
                self.alertClass(self.alerts.success.class)
                self.alertHeader(self.alerts.success.header)
                self.alertText(self.alerts.success.text)
            })
        .fail(e => {
                console.error('Print Nanny token verification failed', e)
                self.alertClass(self.alerts.error.class)
                self.alertHeader(self.alerts.error.header)
                self.alertText(self.alerts.error.text)
        });
        
    }



    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannyTabViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: [ '#tab_plugin_print_nanny' ]

    });
});


$(function() {
    function PrintNannySettingsViewModel(parameters) {

    let self = this;
    self.swaggerClient = undefined;
    // settings, wizard
    self.octoUser = undefined;
    self.verified = undefined;
    self.error = undefined;

    // assign the injected parameters, e.g.:
    self.loginStateViewModel = parameters[0];
    self.settingsViewModel = parameters[1];

    self.alertClass = ko.observable();
    self.alerts = {
        'warning': {
            header: 'Warning!',
            text: 'Test connection before saving.',
            class: 'alert'
        },
        'error': {
            header: 'Error!',
            text: 'Could not verify token. Email support@print-nanny.com for assistance.',
            class: 'alert-error'
        },
        'success': {
            header: 'Nice!',
            text: 'Your token is verified',
            class: 'alert-success'
        }
    };
    self.alertHeader = ko.observable(self.alerts.warning.header)
    self.alertText = ko.observable(self.alerts.warning.text)

    testAuthTokenInput = function(){
        if (self.settingsViewModel.settings.plugins.print_nanny.auth_token() == undefined){
            return
        }
        const url = OctoPrint.getBlueprintUrl('print_nanny') + 'testAuthToken'
        console.debug('Attempting to verify Print Nanny Auth token...')
        OctoPrint.postJson(url, {
            'auth_token': self.settingsViewModel.settings.plugins.print_nanny.auth_token(),
            'api_uri': self.settingsViewModel.settings.plugins.print_nanny.api_uri(),
            'swagger_json': self.settingsViewModel.settings.plugins.print_nanny.swagger_json()
        })
        .done((res) =>{
                console.debug('Print Nanny verification success')
                self.alertClass(self.alerts.success.class)
                self.alertHeader(self.alerts.success.header)
                self.alertText(self.alerts.success.text)
            })
        .fail(e => {
                console.error('Print Nanny token verification failed', e)
                self.alertClass(self.alerts.error.class)
                self.alertHeader(self.alerts.error.header)
                self.alertText(self.alerts.error.text)
            });
        }
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannySettingsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: [ '#settings_plugin_print_nanny', '#wizard_plugin_print_nanny']

    });
});
