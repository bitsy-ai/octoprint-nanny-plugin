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
    function PrintNannySettingsViewModel(parameters) {

    let self = this;
    self.swaggerClient = undefined;
    // settings, wizard
    self.authTokenInput = undefined;
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
            text: 'Could not verify token.',
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
    self.authTokenInput = ko.observable();


    self.basicSettings = [];
    self.advancedSettings = [];


    self.onAllBound = async function(allViewModels){
        SwaggerClient.http.withCredentials = true;
        self.swaggerClient = await SwaggerClient({
            url: self.settingsViewModel.settings.plugins.print_nanny.swagger_json(),
            authorizations: { BearerAuth: {value: settingsViewModel.settings.plugins.print_nanny.auth_token()} } 
        })
        // self.basicSettings = {'auth_token' : {display: 'Token', value: self.settingsViewModel.settings.plugins.print_nanny.auth_token}}

        // self.advancedSettings = [
        //     {key: 'api_uri', display: 'API URI', value: self.settingsViewModel.settings.plugins.print_nanny.auth_token},
        //     {key: 'swagger_json', display: 'API URI', value: self.settingsViewModel.settings.plugins.print_nanny.swagger_json},
        // ]
    }
    self.saveSettingsData = function(userData){

        self.notices = {
            'alertStong': 'Nice!',
            'alertText': 'Your token is verfied.'
        }
        const settings = {
            plugins: {
                print_nanny: {
                    auth_token: self.authTokenInput,
                    email: userData.email,
                    lookup: userData.url
                }
            }
        }
        self.settingsViewModel.saveData(settings);
    }

    testAuthTokenInput = function(){
        if (self.authTokenInput == undefined){
            return
        }
        self.swaggerClient.apis.me.get_me()
            .then((res) =>{
                self.alertClass(self.alerts.success.class)
                self.alertHeader(self.alerts.success.header)
                self.alertText(self.alerts.success.text)
                self.saveSettingsData(res.body)
            })
            .catch(e => {
                console.error(e)
                self.alertMode(self.alerts.success.class)
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
        elements: [ '#settings_plugin_print_nanny' ]

    });
});


$(function() {
    function PrintNannyWizardViewModel(parameters) {

        let self = this;
        self.swaggerClient = undefined;
        // settings, wizard
        self.authTokenInput = ko.observable();
        self.octoUser = undefined;
        self.verified = undefined;
        self.error = undefined;

        // self.alertMode = ko.observable('warning')

        // self.alerts = ko.observable({
        //     'warning': {
        //         strong: 'Warning!',
        //         text: 'Test connection before saving.'
        //     },
        //     'error': {
        //         strong: 'Error!',
        //         text: 'Could not verify token.'
        //     },
        //     'success': {
        //         strong: 'Nice!',
        //         text: 'Your token is verified.'
        //     }
        // })

        // self.fieldset = ko.observable({
        //     'auth_token': undefined
        // })


        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];
        // self.apiUri = self.settingsViewModel.settings.plugins.print_nanny.api_uri

        self.onAllBound = function(allViewModels){
            self.octoUser = self.settingsViewModel.currentUser
        }

        isAuthenticated = function(){
            return false
        }

        self.saveSettingsData = function(userData){

            self.notices = {
                'alertStong': 'Nice!',
                'alertText': 'Your token is verfied.'
            }
            const settings = {
                plugins: {
                    print_nanny: {
                        auth_token: self.authTokenInput,
                        email: userData.body.email,
                        lookup: userData.body.url
                    }
                }
            }
            self.settingsViewModel.saveData(settings);
        }


        // TODO: Implement your plugin's view model here.

        // onStartupComplete() = function () {}
        // onEventPredictDone() = function () {}
        // onEventCalibrateDone() = function () {}
        // onEventCalibrateFailed() = function () {}

        
        // onWizardFinish() = function() {}
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannyWizardViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: [ '#wizard_plugin_print_nanny_2' ]

    });
});
