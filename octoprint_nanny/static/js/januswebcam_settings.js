$(function () {
  function JanusWebcamSettingsViewModel(parameters) {
    var self = this;

    self.loginState = parameters[0];
    self.settings = parameters[1];
    self.janusWebcam = parameters[2];

    self.onBeforeBinding = function () {
      self.webcamEnabled = self.settings.settings.webcam.webcamEnabled;
      self.janusApiUrl = self.settings.settings.plugins.octoprint_nanny.janusApiUrl;
      self.janusApiToken = self.settings.settings.plugins.octoprint_nanny.janusApiToken;
      self.streamWebrtcIceServers = self.settings.settings.plugins.octoprint_nanny.streamWebrtcIceServers;
      self.loading = self.janusWebcam.loading;
      self.active = self.janusWebcam.active;
      self.ready = self.janusWebcam.ready;

      self.updateStreamsList = self.janusWebcam.updateStreamsList;
      self.streams = self.janusWebcam.streams;
      self.startStream = self.janusWebcam.startStream;
      self.stopStream = self.janusWebcam.stopStream;
      self.selectedStreamId = self.janusWebcam.selectedStreamId;
      self.showStartButton = self.janusWebcam.showStartButton;
    };
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: JanusWebcamSettingsViewModel,
    dependencies: ["loginStateViewModel", "settingsViewModel", "janusWebcamViewModel"],
    elements: ["#janus_webcam_settings"]
  });
});
