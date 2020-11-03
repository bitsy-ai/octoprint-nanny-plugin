# coding=utf-8
from __future__ import absolute_import
from octoprint.events import eventManager, Events

import logging
import threading

import octoprint.plugin

from PIL import Image as PImage
from tflite_runtime import interpreter  as tflite_interpreter

logger = logging.getLogger('octoprint.plugins.print_nanny')

class ThreadLocalPredictor(threading.local):
    model_path = 'data/tflite-print3d_20201101015829-2020-11-03T06:39:54.239Z/model.tflite'
    label_path = 'data/tflite-print3d_20201101015829-2020-11-03T06:39:54.239Z/dict.txt'
    image_shape = (320, 320)

    def __init__(self, _, **kwargs):
        self.tflite_interpreter = tflite_interpreter.Interpreter(
            model_path=self.model_path
        )
        self.tflite_interpreter.allocate_tensors()
        self.input_details = self.tflite_interpreter.get_input_details()
        self.output_details = self.tflite_interpreter.get_output_details()
        self.__dict__.update(**kwargs)

    def predict(self, image):
        image = np.asarray(image)
        self.tflite_interpreter.set_tensor(self.input_details[0]["index"], image)
        self.tflite_interpreter.invoke()

        box_data = tf.convert_to_tensor(
            self.tflite_interpreter.get_tensor(self.output_details[0]["index"])
        )
        class_data = tf.convert_to_tensor(
            self.tflite_interpreter.get_tensor(self.output_details[1]["index"])
        )
        score_data = tf.convert_to_tensor(
            self.tflite_interpreter.get_tensor(self.output_details[2]["index"])
        )
        num_detections = tf.convert_to_tensor(
            self.tflite_interpreter.get_tensor(self.output_details[3]["index"])
        )
 
        return {
            "detection_boxes": box_data,
            "detection_classes": class_data,
            "detection_scores": score_data,
            "num_detections": len(num_detections),
        }
class OctoPrintNannyPlugin(octoprint.plugin.SettingsPlugin,
                  octoprint.plugin.AssetPlugin,
                  octoprint.plugin.TemplatePlugin,
                  octoprint.plugin.WizardPlugin):

    def __init__(self, *args, **kwargs):

        eventManager().subscribe(Events.PRINT_STARTED, self.on_print_started)
        eventManager().subscribe(Events.PRINT_RESUME, self.on_print_resume)

        eventManager().subscribe(Events.PRINT_PAUSED, self.on_print_paused)
        eventManager().subscribe(Events.PRINT_FAILED, self.on_print_failed)
        eventManager().subscribe(Events.PRINT_DONE, self.on_print_done)

        eventManager().subscribe(Events.CAPTURE_DONE, self.on_capture_done)
        eventManager().subscribe(Events.MOVIE_DONE, self.on_movie_done)

        for (event, callback) in self.event_subscriptions():
            eventManager().subscribe(event, callback)

        self._active = False
        self._queue = queue.Queue()

        self._predictor = ThreadLocalPredictor()

		self._predict_thread = threading.Thread(target=self._predict_worker)
		self._predict_thread.daemon = True

        # self._upload_thread = threading.Thread(target=self._upload_worker)
        # self._upload_thread.daemon = True

    def _start(self):
        self._reset()
        self._predict_thread.start()
        # self._upload_thread.start()
        self._active = True
    
    def _resume(self):
        pass

    def _stop(self):
        pass

    def _reset(self):
        pass

    def _predict_worker(self):
        while self._queue_active:
            image = self._predict_queue.get(block=True)
            prediction = self._predictor.predict(image)
    
    def load_image(self, filename):
        # @todo path prefix?
        return PImage.open(filename)

    def on_capture_done(self, payload):
        '''
        payload:
            file: the name of the image file that was saved
        '''
        image = self.load_image(payload['file'])
        self._predict_queue.put(image)


    def on_print_started(self, payload):
        '''
            payload:
                name: the file’s name
                path: the file’s path within its storage location
                origin: the origin storage location of the file, either local or sdcard
                size: the file’s size in bytes (if available)
                owner: the user who started the print job (if available)
                user: the user who started the print job (if available)
        '''
        self._start()

    def on_print_resume(self):
        self._resume()


    def on_print_failed(self, payload):
        '''
            name: the file’s name
            path: the file’s path within its storage location
            origin: the origin storage location of the file, either local or sdcard
            size: the file’s size in bytes (if available)
            owner: the user who started the print job (if available)
            time: the elapsed time of the print when it failed, in seconds (float)
            reason: the reason the print failed, either cancelled or error
        '''
        self._stop()
        self._reset()
    ## Wizard plugin mixin




    def get_wizard_version(self):
        return 2
    def is_wizard_required(self):
        return not self._settings.get(["auth_token"])

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            remote_uri='https://api.print-nanny.com'
        )

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/nanny.js"],
            css=["css/nanny.css"],
            less=["less/nanny.less"]
        )

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return dict(
            nanny=dict(
                displayName="Bitsy OctoPrint Nanny",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="bitsy-ai",
                repo="octoprint-nanny",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/bitsy-ai/octoprint-nanny/archive/{target_version}.zip"
            )
        )

        

        
        
        
def _register_custom_events(*args, **kwargs):
    return [
        "predict_done", 
        "predict_failed", 
        "upload_done", 
        "upload_failed"
    ]


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Nanny Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = OctoprintNannyPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.timelapse.capture.post": __plugin_implementation__.on_timelapse_capture
    }

