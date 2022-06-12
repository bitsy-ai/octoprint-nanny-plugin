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

        OctoPrint.socket.onMessage("*", function (message) {
            console.log(message);
        })
    }


    function PrintNannyTabViewModelDeprecated(parameters) {
        let self = this;
        self.apiClient = null;

        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];

        self.imageData = ko.observable('plugin/octoprint_nanny/static/img/sleeping.png');
        self.calibratePos = ko.observable();


        self.previewActive = ko.observable(false)

        self.calibrationActive = ko.observable(false);

        self.statusCheckActive = ko.observable();
        self.statusCheckSuccess = ko.observable();
        self.statusCheckFailed = ko.observable();

        self.apiStatusMessage = ko.observable();
        self.apiStatusClass = ko.observable();
        self.mqttPingStatusMessage = ko.observable();
        self.mqttPingStatusClass = ko.observable();
        self.mqttPongStatusMessage = ko.observable();
        self.mqttPongStatusClass = ko.observable();



        testConnectionsAsync = function () {
            if (self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token() == undefined) {
                self.statusCheckActive(false);
                self.statusCheckSuccess(false);
                self.statusCheckFailed(true);
                return
            }
            self.statusCheckActive(true);
            self.apiStatusClass('active')
            self.apiStatusMessage('⏳ Connecting')
            self.mqttPingStatusClass('active')
            self.mqttPingStatusMessage('⏳ Sending Ping')
            self.mqttPongStatusMessage('⏳ Waiting on Pong')

            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'testConnectionsAsync'
            return OctoPrint.postJson(url, {
                'auth_token': self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token(),
                'api_url': self.settingsViewModel.settings.plugins.octoprint_nanny.api_url(),
            })
                .done((res) => {
                    console.log(res)


                })
                .fail(e => {
                    console.error('Print Nanny token verification failed', e)
                    self.statusCheckActive(false);
                    self.statusCheckSuccess(false);
                    self.statusCheckFailed(true);
                });
        }

        showMonitoringFrame = function (payload) {
            if (self.previewActive() == false) {
                self.previewActive(true);
            }
            self.imageData("data:image/jpeg;base64," + payload);
        }

        // OctoPrint.socket.onMessage("*", function (message) {
        //     console.log(message)
        //     if (message && message.data && message.data.type) {
        //         switch (message.data.type) {
        //             case 'plugin_octoprint_nanny_monitoring_frame_b64':
        //                 return showMonitoringFrame(message.data.payload)
        //             case 'plugin_octoprint_nanny_monitoring_reset':
        //                 return self.imageData("plugin/octoprint_nanny/static/img/sleeping.png");
        //             case 'plugin_octoprint_nanny_connect_test_rest_api_failed':
        //                 self.statusCheckActive(false);
        //                 self.statusCheckSuccess(false);
        //                 self.statusCheckFailed(true);
        //                 self.apiStatusMessage(message.data.payload.error + '\n Try restarting OctoPrint and running this test again.');
        //                 self.apiStatusClass('danger');
        //                 break
        //             case 'plugin_octoprint_nanny_connect_test_rest_api_success':
        //                 self.statusCheckActive(false);
        //                 self.statusCheckFailed(false);
        //                 self.apiStatusMessage('✔️ Connected to REST API');
        //                 self.apiStatusClass('success');
        //                 break
        //             case 'plugin_octoprint_nanny_connect_test_mqtt_ping_failed':
        //                 self.statusCheckActive(false);
        //                 self.statusCheckSuccess(false);
        //                 self.statusCheckFailed(true);
        //                 self.mqttPingStatusMessage(message.data.payload.error + '\n Try restarting OctoPrint and running this test again.');
        //                 self.mqttPingStatusClass('danger');
        //                 break
        //             case 'plugin_octoprint_nanny_connect_test_mqtt_ping_success':
        //                 self.statusCheckActive(false);
        //                 self.statusCheckFailed(false);
        //                 self.mqttPingStatusMessage('✔️ Ping Sent');
        //                 self.mqttPingStatusClass('success');
        //                 break
        //             case 'plugin_octoprint_nanny_connect_test_mqtt_pong_success':
        //                 self.statusCheckActive(false);
        //                 self.statusCheckFailed(false);
        //                 self.mqttPongStatusMessage('✔️ Pong Received');
        //                 self.mqttPongStatusClass('success');
        //                 break
        //         }
        //     }
        // });

        calibrate = function () {
            self.calibrationActive(true);
            const calibrateImg = new Image();
            calibrateImg.src = $('#tab_plugin_octoprint_nanny_preview').attr('src')
            $('#tab_plugin_octoprint_nanny_calibrate').empty()
            $('#tab_plugin_octoprint_nanny_calibrate').append(calibrateImg);
            Jcrop.load(calibrateImg).then(img => {
                const stage = Jcrop.attach(img);
                stage.listen('crop.change', function (widget, e) {
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

        saveCalibration = function () {
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

        startMonitoring = function () {
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'startMonitoring'

            OctoPrint.postJson(url, {})
                .done((res) => {
                    console.debug('Starting stream', res)
                    self.previewActive(true);
                })
                .fail(e => {
                    console.error('Failed to start stream', e)
                });

        }

        stopMonitoring = function () {
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'stopMonitoring'
            OctoPrint.postJson(url, {})
                .done((res) => {
                    console.log(res)
                    self.previewActive(false);
                })
                .fail(e => {
                    console.error('Failed to stop stream', e)
                });
        }

        isPreviewActive = function () {
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'previewActive'

            OctoPrint.postJson(url, {})
                .done((res) => {
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
        self.swaggerClient = undefined;
        // settings, wizard
        self.octoUser = undefined;
        self.verified = undefined;
        self.error = undefined;

        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];

        self.authAlertClass = ko.observable();
        self.authAlertText = ko.observable()
        self.authAlertHeader = ko.observable()
        self.authAlerts = {
            'warning': {
                header: 'Link your Print Nanny account',
                text: 'Enter your auth token and click the Test Connection button to get started.',
                class: 'alert'
            },
            'error': {
                header: 'Error!',
                text: 'Could not verify token. Email support@print-nanny.com for assistance.',
                class: 'alert-error'
            },
            'success': {
                header: 'Nice!',
                text: 'Your Print Nanny account is linked. Register this device below to begin monitoring your prints.',
                class: 'alert-success'
            }
        };

        self.imageData = ko.observable();
        self.deviceRegisterProgressPercent = ko.observable();
        self.deviceRegisterProgress = 0;
        self.deviceRegisterProgressCompleted = 6;

        self.onAfterBinding = function () {
            if (!self.settingsViewModel.settings.plugins.octoprint_nanny.auth_valid) {
                self.authAlertHeader = self.authAlerts.warning.header
                self.authAlertText = self.authAlerts.warning.text
                self.authAlertClass = self.authAlerts.warning.class
            }
        }

        self.deviceAlertClass = ko.observable();
        self.deviceAlerts = {
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
        self.deviceAlertHeader = ko.observable();
        self.deviceAlertText = ko.observable();

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

        OctoPrint.socket.onMessage("*", function (message) {
            if (message && message.data && (
                message.data.type == 'plugin_octoprint_nanny_device_register_start' ||
                message.data.type == 'plugin_octoprint_nanny_device_register_done' ||
                message.data.type == 'plugin_octoprint_nanny_device_register_failed' ||
                message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_start' ||
                message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_done' ||
                message.data.type == 'plugin_octoprint_nanny_device_printer_profile_sync_failed'

            )) {
                console.log(message)
            }
        });

        self.backupStatus = ko.observable();

        createBackup = function () {
            self.backupStatus('loading');
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'createBackup'
            OctoPrint.postJson(url, {})
                .done((res) => {
                    self.backupStatus('success');
                    console.info("Succes POST /createBackup", res)
                })
                .fail(e => {
                    console.error(e)
                    self.backupStatus('fail');
                })
        }

        registerDevice = function () {
            self.deviceRegisterProgress = 100 / self.deviceRegisterProgressCompleted;
            self.deviceRegisterProgressPercent(self.deviceRegisterProgress + '%');
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'registerDevice'
            OctoPrint.postJson(url, {
                'device_name': self.settingsViewModel.settings.plugins.octoprint_nanny.device_name()
            })
                .done((res) => {
                    console.info("Succes POST /registerDevice", res)
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

        testAuthTokenInput = function () {
            if (self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token() == undefined) {
                return
            }
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'testAuthToken'
            console.debug('Attempting to verify Print Nanny Auth token...')
            OctoPrint.postJson(url, {
                'auth_token': self.settingsViewModel.settings.plugins.octoprint_nanny.auth_token(),
                'api_url': self.settingsViewModel.settings.plugins.octoprint_nanny.api_url(),
            })
                .done((res) => {
                    console.log(res)
                    self.authAlertClass(self.authAlerts.success.class)
                    self.authAlertHeader(self.authAlerts.success.header)
                    self.authAlertText(self.authAlerts.success.text)
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

        saveAdvancedSettings = function () {
            console.log('Saving settings')
            OctoPrint.settings.savePluginSettings('octoprint_nanny', {
                'webcam_to_octoprint_ws': self.settingsViewModel.settings.plugins.webcam_to_octoprint_ws(),
                'webcam_to_mqtt': self.settingsViewModel.settings.plugins.webcam_to_mqtt(),
                'ws_url': self.settingsViewModel.settings.plugins.octoprint_nanny.ws_url(),
                'api_url': self.settingsViewModel.settings.plugins.octoprint_nanny.api_url(),
                'monitoring_frames_per_minute': self.settingsViewModel.settings.plugins.octoprint_nanny.monitoring_frames_per_minute(),
                'mqtt_bridge_hostname': self.settingsViewModel.settings.plugins.octoprint_nanny.mqtt_bridge_hostname(),
                'mqtt_bridge_port': self.settingsViewModel.settings.plugins.octoprint_nanny.mqtt_bridge_port(),
                'mqtt_bridge_certificate_url': self.settingsViewModel.settings.plugins.octoprint_nanny.mqtt_bridge_certificate_url()
            })
                .done((res) => {
                    console.log(res)
                    testAuthTokenInput()
                })
                .fail(e => {
                    console.error(e)

                });

        }

        testSnapshotUrl = function () {
            const url = OctoPrint.getBlueprintUrl('octoprint_nanny') + 'testSnapshotUrl'
            OctoPrint.postJson(url, {
                'snapshot_url': self.settingsViewModel.settings.plugins.octoprint_nanny.snapshot_url(),
            })
                .done((res) => {
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
        dependencies: ["loginStateViewModel", "settingsViewModel"],
        // Elements to bind to, e.g. #settings_plugin_nanny, #tab_plugin_nanny, ...
        elements: ['#settings_plugin_octoprint_nanny', '#wizard_plugin_octoprint_nanny']

    });
});
