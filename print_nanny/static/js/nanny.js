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


$(function() {
    function PrintNannyWizardViewModel(parameters) {
        SwaggerClient.http.withCredentials = true;

        let self = this;
        self.swaggerClient = undefined;
        // settings, wizard
        self.authTokenInput = undefined;
        self.octoUser = undefined;
        self.verified = undefined;
        self.error = undefined;

        self.notices = {
            'alertStong': 'Warning!',
            'alertText': 'Test connection before saving.'
        }


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
        testAuthTokenInput = function(){
            if (self.authTokenInput == undefined){
                return
            }
            SwaggerClient({
                url: self.settingsViewModel.settings.plugins.print_nanny.swagger_json(),
                authorizations: { BearerAuth: {value: self.authTokenInput } } 
            })
            .then( client => {
                console.log('Print Nanny swagger-js client initialized', client)
                self.swaggerClient = client;
                client.apis.me.get_me()
                .then(self.saveSettingsData)
                });

        }

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
