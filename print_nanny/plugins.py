import logging
import queue
import threading

import octoprint.plugin

from octoprint.events import eventManager, Events


from .predictor import ThreadLocalPredictor

logger = logging.getLogger('octoprint.plugins.print_nanny')

class BitsyNannyPlugin(octoprint.plugin.SettingsPlugin,
                  octoprint.plugin.AssetPlugin,
                  octoprint.plugin.TemplatePlugin,
                  octoprint.plugin.WizardPlugin):
    
    CALIBRATE_EVENT = 'calibrate'
    CALIBRATE_DONE = 'calibrate_done'
    CALIBRATE_FAILED = 'calibrate_failed'
    
    PREDICT_EVENT = 'predict'
    PREDICT_EVENT_DONE = 'predict_done'
    PREDICT_EVENT_FAILED = 'predict_failed'

    UPLOAD_EVENT = 'upload'
    UPLOAD_EVENT_FAILED = 'upload_failed'
    UPLOAD_EVENT_DONE = 'uplaod_done'

    def __init__(self, *args, **kwargs):
        
        # @todo add any required calibration routines
        # eventManager().subscribe(self.CALIBRATE_EVENT, self.on_calibrate)

        eventManager().subscribe(Events.PRINT_STARTED, self.on_print_started)
        eventManager().subscribe(Events.PRINT_RESUMED, self.on_print_resume)

        eventManager().subscribe(Events.PRINT_PAUSED, self.on_print_paused)
        eventManager().subscribe(Events.PRINT_FAILED, self.on_print_failed)
        eventManager().subscribe(Events.PRINT_DONE, self.on_print_done)

        eventManager().subscribe(Events.CAPTURE_DONE, self.on_capture_done)
        #eventManager().subscribe(Events.MOVIE_DONE, self.on_movie_done)

        # for (event, callback) in self.event_subscriptions():
        #     eventManager().subscribe(event, callback)

        self._active = False
        self._queue = queue.Queue()

        # @todo single-threaded perf against multiprocessing.Pool, Queue, Manager
        self._predictor = ThreadLocalPredictor()
        self._predict_thread = threading.Thread(target=self._predict_worker)
        self._predict_thread.daemon = True

        self.queue_event_handlers = {
            self.PREDICT_EVENT: self._handle_predict,
            self.UPLOAD_EVENT: self._handle_upload
        }

    def _start(self):
        self._reset()
        self._predict_thread.start()
        self._active = True
    
    def _resume(self):
        pass
    
    def _pause(self):
        pass

    def _stop(self):
        pass

    def _reset(self):
        pass

    def _handle_predict(self, filename=None, **kwargs):
        if not None:
            return
        
        image = self.load_image(filename)
        prediction = self._predictor.predict(image)
        prediction = self.postprocess(image, prediction)

        eventManager().fire(self.PREDICT_DONE, prediction['viz'])
        msg = {
            'original_image': image,
            'prediction': prediction,
            'type': self.UPLOAD_EVENT
        }
        self._queue.put(msg)
    
    def _handle_upload(self, original_image=None, prediction=None, **kwargs):
        print(f'uploading {original_image}')
        # @ todo install grpc stub
        pass


    def _predict_worker(self):
        while self._queue_active or not self._predict_queue.empty():
            msg = self._predict_queue.get(block=True)
            if not msg.get('type'):
                logger.warning('Ignoring enqueued msg without type declared {msg}'.format(msg=msg))

            handler_fn = self._queue_event_handlers[msg['type']]
            handler_fn(**msg)
    

    def on_capture_done(self, payload):
        '''
        payload:
            file: the name of the image file that was saved
        '''
        filename = self.load_image(payload['file'])
        self._predict_queue.put(dict(
            type=self.PREDICT_EVENT,
            filename=filename
        ))


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
    
    def on_print_paused(self):
        self._pause()

    def on_print_done(self):
        pass

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

    ## TemplatePlugin mixin
    def get_template_configs(self):
        return [
            # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=wizard#octoprint.plugin.types.TemplatePlugin
            # "mandatory wizard steps will come first, sorted alphabetically, then the optional steps will follow, also alphabetically."
            dict(type="wizard", name="Hello from Bitsy.ai!", template="print_nanny_wizard.jinja2"),
            dict(type="wizard", name="Setup Account", template="print_nanny_2_wizard.jinja2"),

        ]

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            auth_token=None,
            api_uri='http://localhost:8000/api/', # 'https://api.print-nanny.com',
            swagger_json='http://localhost:8000/api/swagger.json', # 'https://api.print-nanny.com/swagger.json'
            prometheus_gateway='https://prom.print-nanny.com'
        )

        
    ## Wizard plugin mixin

    def get_wizard_version(self):
        return 0

    def is_wizard_required(self):
        return self._settings.get(["auth_token"]) is None

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(
            js=["js/nanny.js"],
            css=["css/nanny.css"],
            less=["less/nanny.less"],
            img=["img/wizard_example.jpg"],
            vendor=["vendor/swagger-client@3.12.0.browser.min.js"]
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
