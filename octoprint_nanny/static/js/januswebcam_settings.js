$(function () {
  function JanusWebcamSettingsViewModel(parameters) {
    var self = this;

    self.loginState = parameters[0];
    self.settings = parameters[1];

    self.onBeforeBinding = function () {
      self.janusApiUrl = self.settings.settings.plugins.octoprint_nanny.janusApiUrl;
      self.janusApiToken = self.settings.settings.plugins.octoprint_nanny.janusApiToken;
      self.streamWebrtcIceServers = self.settings.settings.plugins.octoprint_nanny.streamWebrtcIceServers;
      self.selectedStreamId = self.settings.settings.plugins.octoprint_nanny.selectedStreamId;
      self.janusBitrateInterval = self.settings.settings.plugins.octoprint_nanny.janusBitrateInterval;
    };
  }

  OCTOPRINT_VIEWMODELS.push({
    construct: JanusWebcamSettingsViewModel,
    dependencies: ["loginStateViewModel", "settingsViewModel"],
    elements: [
      "#janus_webcam_settings",
    ]
  });
});
