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

        self.imageData = ko.observable();
        self.calibratePos = ko.observable();


        self.previewActive = ko.observable(false)

        self.calibrationActive = ko.observable(false)

        self.active = ko.observable(false)


        OctoPrint.socket.onMessage("*", function(message) {
            console.log(message)
            if (message && message.data && message.data.type == 'plugin_print_nanny_predict_done'){

                if (self.previewActive() == false) {
                    self.previewActive(true);
                }
                self.imageData("data:image/jpeg;base64,"+message.data.payload.image);
            }
        });

        toggleAutoStart = function(){
            const newValue = !self.settingsViewModel.settings.plugins.print_nanny.auto_start()
            self.settingsViewModel.settings.plugins.print_nanny.auto_start(newValue)
            OctoPrint.settings.savePluginSettings('print_nanny', {
                auto_start: newValue
            })
        }

        calibrate = function(){
            self.calibrationActive(true);
            const calibrateImg = new Image();
            calibrateImg.src = $('#tab_plugin_print_nanny_preview').attr('src')
            document.getElementById('tab_plugin_print_nanny_calibrate').appendChild(calibrateImg);
            Jcrop.load(calibrateImg).then(img => {
                const stage = Jcrop.attach(img);
                stage.listen('crop.change',function(widget,e){
                    console.log(widget.pos)
                    const normalized = widget.pos.normalize()
                    self.calibratePos({
                        coords: widget.pos,
                        h: img.height,
                        w: img.width
                    });
                });
            });
        }

        saveCalibration = function(){
            self.settingsViewModel.settings.plugins.print_nanny.calibrated(true)
            const calibration = self.calibratePos()
            const s = {
                calibrated: true,
                calibrate_x0: calibration.coords.x / calibration.w,
                calibrate_y0: calibration.coords.y / calibration.h,
                calibrate_x1: calibration.coords.x2 / calibration.w,
                calibrate_y1: calibration.coords.y2 / calibration.h,
                calibrate_h: calibration.h,
                calibrate_w: calibration.w
            }
            OctoPrint.settings.savePluginSettings('print_nanny', s);
            self.calibrationActive(false);

        }
    
        startPredict = function(){
            const url = OctoPrint.getBlueprintUrl('print_nanny') + 'startPredict'

            OctoPrint.postJson(url, {})
            .done((res) =>{
                    console.debug('Starting stream', res)
                    self.previewActive(true);
                    // self.alertClass(self.alerts.success.class)
                    // self.alertHeader(self.alerts.success.header)
                    // self.alertText(self.alerts.success.text)
                })
            .fail(e => {
                    console.error('Failed to start stream', e)
                    // self.alertClass(self.alerts.error.class)
                    // self.alertHeader(self.alerts.error.header)
                    // self.alertText(self.alerts.error.text)
            });
            
        }

        stopPredict = function(){
            const url = OctoPrint.getBlueprintUrl('print_nanny') + 'stopPredict'

            OctoPrint.postJson(url, {})
            .done((res) =>{
                self.previewActive(false);
                console.debug('Starting stream', res)
                    // self.alertClass(self.alerts.success.class)
                    // self.alertHeader(self.alerts.success.header)
                    // self.alertText(self.alerts.success.text)
                })
            .fail(e => {
                    console.error('Failed to start stream', e)
                    // self.alertClass(self.alerts.error.class)
                    // self.alertHeader(self.alerts.error.header)
                    // self.alertText(self.alerts.error.text)
            });        
        }

        isPreviewActive = function(){
            const url = OctoPrint.getBlueprintUrl('print_nanny') + 'previewActive'

            OctoPrint.postJson(url, {})
            .done((res) =>{
                self.previewActive(res.active);

                })
            .fail(e => {
                    console.error('Failed to start stream', e)
                    // self.alertClass(self.alerts.error.class)
                    // self.alertHeader(self.alerts.error.header)
                    // self.alertText(self.alerts.error.text)
            }); 
        }

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
            header: 'Hey!',
            text: 'Test your connection before saving.',
            class: 'alert'
        },
        'error': {
            header: 'Error!',
            text: 'Could not verify token. Email support@print-nanny.com for assistance.',
            class: 'alert-error'
        },
        'success': {
            header: 'Nice!',
            text: 'Your token is verified.',
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
            'api_url': self.settingsViewModel.settings.plugins.print_nanny.api_url(),
        })
        .done((res) =>{
                console.log(res)
                self.alertClass(self.alerts.success.class)
                self.alertHeader(self.alerts.success.header)
                self.alertText(self.alerts.success.text)
            })
        .fail(e => {
                console.error(e)

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
