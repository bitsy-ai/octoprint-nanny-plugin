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
//         elements: [ '#wizard_plugin_octoprint_nanny_2', '#settings_plugin_octoprint_nanny' ]

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

        self.imageData = ko.observable('plugin/octoprint_nanny/static/img/sleeping.png');
        self.calibratePos = ko.observable();


        self.previewActive = ko.observable(false)

        self.calibrationActive = ko.observable(false)

        self.active = ko.observable(false)


        OctoPrint.socket.onMessage("*", function(message) {
            if (message && message.data && message.data.type == 'plugin_octoprint_nanny_predict_done'){

                if (self.previewActive() == false) {
                    self.previewActive(true);
                }
                self.imageData("data:image/jpeg;base64,"+message.data.payload.image);
            }
            if (message && message.data && message.data.type == 'plugin_octoprint_nanny_predict_offline'){
                console.log(message)
                self.imageData("plugin/octoprint_nanny/static/img/sleeping.png");
            }
        });

        toggleAutoStart = function(){
            const newValue = !self.settingsViewModel.settings.plugins.octoprint_nanny.auto_start()
            self.settingsViewModel.settings.plugins.octoprint_nanny.auto_start(newValue)
            OctoPrint.settings.savePluginSettings('octoprint_nanny', {
                auto_start: newValue
            })
        }

        calibrate = function(){
            self.calibrationActive(true);
            const calibrateImg = new Image();
            calibrateImg.src = $('#tab_plugin_octoprint_nanny_preview').attr('src')
            $('#tab_plugin_octoprint_nanny_calibrate').empty()
            $('#tab_plugin_octoprint_nanny_calibrate').append(calibrateImg);
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
            self.settingsViewModel.settings.plugins.octoprint_nanny.calibrated(true)
            const calibration = self.calibratePos()
            const s = {
                calibrated: true,
                calibrate_x0: calibration.coords.x / calibration.w,
                calibrate_y0: calibration.coords.y / calibration.h,
                calibrate_x1: calibration.coords.x2 / calibration.w,
                calibrate_y1: calibration.coords.y2 / calibration.h,
            }
            OctoPrint.settings.savePluginSettings('octoprint_nanny', s);
            self.calibrationActive(false);

        }
    
        startPredict = function(){
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'startPredict'

            OctoPrint.postJson(url, {})
            .done((res) =>{
                    console.debug('Starting stream', res)
                    self.previewActive(true);
                })
            .fail(e => {
                    console.error('Failed to start stream', e)
            });
            
        }

        stopPredict = function(){
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'stopPredict'
            self.imageData("plugin/octoprint_nanny/static/img/sleeping.png");

            OctoPrint.postJson(url, {})
            .done((res) =>{
                console.log(res)
                self.previewActive(false);
                })
            .fail(e => {
                console.error('Failed to stop stream', e)
            });        
        }

        isPreviewActive = function(){
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'previewActive'

            OctoPrint.postJson(url, {})
            .done((res) =>{
                self.previewActive(res.active);

                })
            .fail(e => {
                    console.error('Failed to start stream', e)
                    // self.authAlertClass(self.authAlerts.error.class)
                    // self.authAlertHeader(self.authAlerts.error.header)
                    // self.authAlertText(self.authAlerts.error.text)
            }); 
        }

    }

    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannyTabViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: [ '#tab_plugin_octoprint_nanny' ]

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

    self.authAlertClass = ko.observable();
    self.authAlerts = {
        'warning': {
            header: 'Hey!',
            text: 'Test your connection 👇',
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

    self.imageData = ko.observable();
    self.deviceRegisterProgressPercent = ko.observable();
    self.deviceRegisterProgress = 0;
    self.deviceRegisterProgressCompleted = 6;

    self.authAlertHeader = ko.observable(self.authAlerts.warning.header)
    self.authAlertText = ko.observable(self.authAlerts.warning.text)

    self.deviceAlertClass = ko.observable();
    self.deviceAlerts = {
        'warning1': {
            header: 'Wait!',
            text: 'You need to test your auth token before this device can be provisioned. 👆',
            class: 'alert'
        },
        'warning2': {
            header: 'Wait!',
            text: 'Your device is not registered yet! \n Choose a name for your device and then click the Start Registration button.',
            class: 'alert'
        },
        'nameError': {
            header: 'Hey, choose a name!',
            text: 'Pick a nickname for this device and enter it above.',
            class: 'alert-error'
        },
        'error': {
            header: 'Error!',
            text: 'Something went wrong while provisioning this device.',
            class: 'alert-error'
        },
        'success': {
            header: 'Nice!',
            text: 'Device provisioning suceeded!',
            class: 'alert-success'
        }
    };
    self.deviceAlertHeader = ko.observable(self.deviceAlerts.warning1.header);
    self.deviceAlertText = ko.observable(self.deviceAlerts.warning1.text);

    self.existingDeviceAlertClass = ko.observable();
    self.existingDeviceAlerts = {
        'warning': {
            header: 'Just FYI',
            text: 'Print Nanny will provision a new key pair when you re-register your device.',
            class: 'alert'
        },
        'error': {
            header: 'Error!',
            text: 'Something went wrong while re-provisioning this device.',
            class: 'alert-error'
        },
        'success': {
            header: 'Nice!',
            text: 'Device re-provisioning suceeded!',
            class: 'alert-success'
        }
    };
    self.existingDeviceAlertHeader = ko.observable(self.existingDeviceAlerts.warning.header);
    self.existingDeviceAlertText = ko.observable(self.existingDeviceAlerts.warning.text);

    OctoPrint.socket.onMessage("*", function(message) {
        if (message && message.data && (
            message.data.type == 'plugin_octoprint_nanny_device_register_start' ||
            message.data.type == 'plugin_octoprint_nanny_device_register_done' ||
            message.data.type == 'plugin_octoprint_nanny_device_register_failed' ||
            message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_start' ||
            message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_done' ||
            message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_failed'

            )){
            console.log(message)
        } 
    });
    registerDevice = function(){
        self.deviceRegisterProgress = 100 / self.deviceRegisterProgressCompleted;
        self.deviceRegisterProgressPercent(self.deviceRegisterProgress +'%');
        const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'registerDevice'
        OctoPrint.postJson(url, {
            'device_name': self.settingsViewModel.settings.plugins.octoprint_nanny.device_name()
        })
        .done((res) =>{
                console.log(res)
                self.deviceAlertClass(self.deviceAlerts.success.class);
                self.deviceAlertHeader(self.deviceAlerts.success.header);
                self.deviceAlertText(self.deviceAlerts.success.text);

                self.existingDeviceAlertClass(self.existingDeviceAlerts.success.class);
                self.existingDeviceAlertHeader(self.existingDeviceAlerts.success.header);
                self.existingDeviceAlertText(self.existingDeviceAlerts.success.text);

                self.deviceRegisterProgressPercent('100%');
            })
        .fail(e => {
                console.error(e)

                console.error('Print Nanny device provisioning failed', e)
                self.deviceAlertClass(self.deviceAlerts.error.class);
                self.deviceAlertHeader(self.deviceAlerts.error.header);
                self.deviceAlertText(self.deviceAlerts.error.text);

                self.existingDeviceAlertClass(self.existingDeviceAlerts.error.class);
                self.existingDeviceAlertHeader(self.existingDeviceAlerts.error.header);
                self.existingDeviceAlertText(self.existingDeviceAlerts.error.text);
            });
    }
    
    testAuthTokenInput = function(){
        if (self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token() == undefined){
            return
        }
        const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'testAuthToken'
        console.debug('Attempting to verify Print Nanny Auth token...')
        OctoPrint.postJson(url, {
            'auth_token': self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token(),
            'api_url': self.settingsViewModel.settings.plugins.octoprint_nanny.api_url(),
        })
        .done((res) =>{
                console.log(res)
                self.authAlertClass(self.authAlerts.success.class)
                self.authAlertHeader(self.authAlerts.success.header)
                self.authAlertText(self.authAlerts.success.text)
                self.deviceAlertText(self.deviceAlerts.warning2.text);
                self.settingsViewModel.settings.plugins.octoprint_nanny.auth_valid(true);


        })
        .fail(e => {
                console.error(e)

                console.error('Print Nanny token verification failed', e)
                self.authAlertClass(self.authAlerts.error.class)
                self.authAlertHeader(self.authAlerts.error.header)
                self.authAlertText(self.authAlerts.error.text)
        });
        }

    saveAdvancedSettings = function(){
        console.log('Saving settings')
        OctoPrint.settings.savePluginSettings('octoprint_nanny', {
            'ws_url': self.settingsViewModel.settings.plugins.octoprint_nanny.ws_url(),
            'api_url': self.settingsViewModel.settings.plugins.octoprint_nanny.api_url(),
            })
            .done((res) =>{
                console.log(res)
                testAuthTokenInput()
            })
            .fail(e => {
                console.error(e)

            }); 

        }
    
    testSnapshotUrl = function(){
        const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'testSnapshotUrl'
        OctoPrint.postJson(url, {
            'snapshot_url': self.settingsViewModel.settings.plugins.octoprint_nanny.snapshot_url(),
        })
        .done((res) =>{
            console.log(res);
            self.imageData("data:image/jpeg;base64," + res.image);

            OctoPrint.settings.savePluginSettings('octoprint_nanny', {
                'snapshot_url': self.settingsViewModel.settings.plugins.octoprint_nanny.snapshot_url(),
                });

            })
            .fail(e => {
                console.error(e);
            });
        }
    }



    OCTOPRINT_VIEWMODELS.push({
        construct: PrintNannySettingsViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ "loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: [ '#settings_plugin_octoprint_nanny', '#wizard_plugin_octoprint_nanny']

    });
});
