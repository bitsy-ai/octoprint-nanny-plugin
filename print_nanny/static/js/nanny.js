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

SwaggerClient.http.withCredentials = true;


$(function() {
    function PrintNannyWizardViewModel(parameters) {
        let self = this;
        self.swaggerClient = undefined;
        // settings, wizard
        self.authTokenInput = undefined;


        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];
        // self.apiUri = self.settingsViewModel.settings.plugins.print_nanny.api_uri

        authStatusCSS = function(){
            return 
        }

        self.onAllBound = function(allViewModels){
            // SwaggerClient(self.settingsViewModel.settings.plugins.print_nanny.swagger_json())
            // .then( client => {
            //     console.log('Print Nanny swagger-js client initialized', client)
            //     self.swaggerClient = client;
            // });
        }

        isAuthenticated = function(){
            return false
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
                .then(res => console.log(res))
            });
            // self.swaggerClient.apis.api.api_users_me({}, {securities: { authorized: { Token: self.authTokenInput } }})
            // .then(response => console.log(response))

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
