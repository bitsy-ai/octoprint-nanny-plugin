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

var startPrintNannyWebRTC = function (videoElement, streamUrl, iceServers) {
    console.warning("PrintNanny startWebRTC called with videoElement, streamUrl, iceServers", videoElement, streamUrl, iceServers)
}

$(function () {
    function CameraSettingsViewModel(parameters) {
        self.testWebcamStreamUrl = function () {
            var url = self.webcam_streamUrlEscaped();
            if (!url) {
                return;
            }

            if (self.testWebcamStreamUrlBusy()) {
                return;
            }

            var text = gettext(
                "If you see your webcam stream below, the entered stream URL is ok."
            );

            var streamType;
            try {
                streamType = self.webcam_streamType();
            } catch (e) {
                streamType = "";
            }

            var webcam_element;
            var webrtc_peer_connection;
            if (streamType === "mjpg") {
                webcam_element = $('<img src="' + url + '">');
            } else if (streamType === "hls") {
                webcam_element = $(
                    '<video id="webcam_hls" muted autoplay style="width: 100%"/>'
                );
                video_element = webcam_element[0];
                if (video_element.canPlayType("application/vnd.apple.mpegurl")) {
                    video_element.src = url;
                } else if (Hls.isSupported()) {
                    var hls = new Hls();
                    hls.loadSource(url);
                    hls.attachMedia(video_element);
                }
            } else if (isWebRTCAvailable() && streamType === "webrtc") {
                webcam_element = $(
                    '<video id="webcam_webrtc" muted autoplay playsinline controls style="width: 100%"/>'
                );
                video_element = webcam_element[0];

                webrtc_peer_connection = startPrintNannyWebRTC(
                    video_element,
                    url,
                    self.webcam_streamWebrtcIceServers()
                );
            } else {
                throw "Unknown stream type " + streamType;
            }

            var message = $("<div id='webcamTestContainer'></div>")
                .append($("<p></p>"))
                .append(text)
                .append(webcam_element);

            self.testWebcamStreamUrlBusy(true);
            showMessageDialog({
                title: gettext("Stream test"),
                message: message,
                onclose: function () {
                    self.testWebcamStreamUrlBusy(false);
                    if (webrtc_peer_connection != null) {
                        webrtc_peer_connection.close();
                        webrtc_peer_connection = null;
                    }
                }
            });
        };

    }

    OCTOPRINT_VIEWMODELS.push({
        construct: CameraSettingsViewModel,
        dependencies: [
            "loginStateViewModel",
            "accessViewModel",
            "printerProfilesViewModel",
            "aboutViewModel",
            "usersViewModel"
        ],
        elements: ["#settings_dialog"]
    });
});

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
