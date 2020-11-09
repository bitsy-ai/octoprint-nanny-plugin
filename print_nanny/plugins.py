import logging
import queue
import glob
import threading
import os
from urllib.parse import urlparse

import flask
import octoprint.plugin

from octoprint.events import eventManager, Events
import octoprint_octolapse.utility as octolapse_util
from octoprint_octolapse import OctolapsePlugin
from octoprint_octolapse.messenger_worker import MessengerWorker
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient

import bravado.exception

from .predictor import ThreadLocalPredictor

logger = logging.getLogger('octoprint.plugins.print_nanny')

#Events.PLUGIN_OCTOLAPSE_SNAPSHOT_DONE = 'plugin_octolapse_snapshot_done'

class BitsyNannyPlugin(
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.WizardPlugin,
        octoprint.plugin.BlueprintPlugin,
        octoprint.plugin.StartupPlugin,                  
    ):
    
    CALIBRATE_START = 'calibrate'
    CALIBRATE_DONE = 'calibrate_done'
    CALIBRATE_FAILED = 'calibrate_failed'
    
    OCTOPRINT_PREDICT_START = 'octoprint_predict'
    OCTOLAPSE_PREDICT_START = 'octolapse_predict'

    PREDICT_DONE = 'predict_done'
    PREDICT_FAILED = 'predict_failed'

    UPLOAD_START = 'upload'
    UPLOAD_FAILED = 'upload_failed'
    UPLOAD_DONE = 'uplaod_done'

    def __init__(self, *args, **kwargs):

        # swagger api
        self.swagger_client = None

        # Octolapse plugin
        self._octolapse_data = None
        self._octolapse_snapshot_path = None

        # Threads
        self._active = False
        self._queue = queue.Queue()

        # @todo compare single-threaded perf against multiprocessing.Pool, Queue, Manager
        self._predictor = ThreadLocalPredictor()
        self._predict_thread = threading.Thread(target=self._predict_worker)
        self._predict_thread.daemon = True
        self.queue_event_handlers = {
            self.OCTOPRINT_PREDICT_START: self._handle_predict,
            self.OCTOLAPSE_PREDICT_START: self._handle_predict,
            self.UPLOAD_START: self._handle_upload
        }
    
    ## Internals
    def _start(self):

        self._reset()
        self._active = True
    
    def _resume(self):
        pass
    
    def _pause(self):
        pass

    def _drain(self):
        while self._queue.qsize() > 0:
            logger.debug(f'Waiting for {self._queue.qsize()} to drain from queue')
            continue
        self.active = False

    def _stop(self):
        pass

    def _reset(self):
        pass

    def _handle_predict(self, data, event_type=None, filename=None, **kwargs):
        if event_type is None:
            return
        
        if event_type is self.OCTOPRINT_PREDICT_START:
            image = self.load_image(filename)

        elif event_type is self.OCTOLAPSE_PREDICT_START:
            # data = {
            #     "type": "snapshot-complete",
            #     "msg": "Octolapse has completed the current snapshot.",
            #     "status": status_dict,
            #     "state": OctolapsePlugin._timelapse.to_state_dict(),
            #     "main_settings": OctolapsePlugin._octolapse_settings.main_settings.to_dict(),
            #     'success': success,
            #     'error': error,
            #     "snapshot_success": snapshot_success,
            #     "snapshot_error": snapshot_error
            # }
            image = self.load_image(self._octolapse_snapshot_path)
        else:
            raise ValueError('Received unrecognized event_type={event_type}'.format(event_type=event_type))
        prediction = self._predictor.predict(image)
        prediction['image'] = self.postprocess(image, prediction)

        eventManager().fire(self.PREDICT_DONE, prediction)
        msg = {
            'original_image': image,
            'prediction': prediction,
            'type': self.UPLOAD_START
        }
        self._queue.put(msg)

    def _handle_upload(self, original_image=None, prediction=None, **kwargs):
        print(f'uploading {original_image}')
        pass


    def _predict_worker(self):
        while self._active:
            msg = self._predict_queue.get(block=True)
            if not msg.get('type'):
                logger.warning('Ignoring enqueued msg without type declared {msg}'.format(msg=msg))

            handler_fn = self._queue_event_handlers[msg['type']]
            handler_fn(**msg)
    
    def _api_auth(self, uri=None, raw_token=None):
        '''
            Bravado http_client helper
            Returns
                Tuple(api_host, auth_token) 
        '''
        # @todo does bravado provide securityDefinitions parser?
        # securityDefinitions": {"Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}}, 
        # "token": {"title": "Token", "type": "string", "readOnly": true, "minLength": 1}}},


        uri = uri or self._settings.get(['api_host'])
        api_host = urlparse(uri).netloc
        auth_token = 'Token ' + raw_token or 'Token '+ str(self._settings.get(['auth_token']))
        return api_host, auth_token

    ##
    ## Octoprint api routes + handlers
    ##
    # def register_custom_routes(self):
    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def testAuthToken(self):
        auth_token = flask.request.json.get('auth_token')
        api_uri = flask.request.json.get('api_uri')

        swagger_json = flask.request.json.get('swagger_json', self._settings.get(['swagger_json']))


        self.http_client = RequestsClient()

        # _api_auth() extracts domain name from uri, and prefixes bearer token
        _api_host, _auth_token = self._api_auth(uri=api_uri, raw_token=auth_token)
        logger.info(f'Creating http_client from api_host {_api_host} auth_token {_auth_token}')
        self.http_client.set_api_key(
            _api_host,
            _auth_token, 
            param_name='Authorization', 
            param_in='header'
            )

        logger.info(f'Loading api spec from {swagger_json}')
        self.swagger_client = SwaggerClient.from_url(swagger_json, http_client=self.http_client)

        try:
            user = self.swagger_client.users.getMe().response().result[0]
            self._settings.set(['auth_token'], auth_token)
            self._settings.set(['api_uri'], api_uri)
            self._settings.set(['swagger_json'], swagger_json)
            self._settings.set(['user_email'], user.email)
            self._settings.set(['user_url'], user.url)

            return flask.json.jsonify(user)

        except bravado.exception.HTTPClientError as e:
            return e.message, e.status_code
        
    ##
    ## Octoprint events (register + callbacks)
    ##
    def register_custom_events(self):
        return [
            "predict_done", 
            "predict_failed", 
            "upload_done", 
            "upload_failed"
        ]
    
    
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        api_host, auth_token = self._api_auth(uri=data.get('api_uri'), token=data.get('auth_token'))

        self.http_client = RequestsClient()
        self.http_client.set_api_key(
            api_host,
            auth_token,
            param_name='Authorization', 
            param_in='header'
        )

        self.swagger_client = SwaggerClient.from_url(self._settings.get(['swagger_json']), http_client=self.http_client)

    def on_settings_initialized(self):
        '''
            Called after plugin initialization
        '''

        # Settings available, load api spec
        if self._settings.get(['auth_token']) is not None:
            self.http_client = RequestsClient()
            api_host, auth_token = self._api_auth()
            self.http_client.set_api_key(
                api_host,
                auth_token, 
                param_name='Authorization', 
                param_in='header'
                )
            self.swagger_client = SwaggerClient.from_url(self._settings.get(['swagger_json']), http_client=self.http_client)

        # Octoprint events
        self._event_bus.subscribe(Events.PRINT_STARTED, self.on_print_started)
        self._event_bus.subscribe(Events.PRINT_RESUMED, self.on_print_resume)

        self._event_bus.subscribe(Events.PRINT_PAUSED, self.on_print_paused)
        self._event_bus.subscribe(Events.PRINT_FAILED, self.on_print_failed)
        self._event_bus.subscribe(Events.PRINT_DONE, self.on_print_done)

        # Octoprint built-in timelapse
        self._event_bus.subscribe(Events.CAPTURE_DONE, self.on_octoprint_capture_done)
        self._event_bus.subscribe(Events.MOVIE_DONE, self.on_octoprint_movie_done)

        # Octolapse 
        self._event_bus.subscribe(Events.PLUGIN_OCTOLAPSE_SNAPSHOT_DONE, self.on_octolapse_capture_done)
        self._event_bus.subscribe(Events.PLUGIN_OCTOLAPSE_MOVIE_DONE, self.on_octolapse_movie_done)
        self._octolapse_data = os.path.join(
            os.path.split(self.get_plugin_data_folder())[0],
            'octolapse',
            'tmp',
            'octolapse_snapshots_tmp'
        )
        # @todo is this readable from Octoprint settings?
        self._octolapse_snapshot_path = glob.glob(
            self._octolapse_data + '/latest_*.jpeg'
        )
    def on_octoprint_capture_done(self, payload):
        '''
        payload:
            file: the name of the image file that was saved
        '''
        filename = self.load_image(payload['file'])
        self._predict_queue.put(dict(
            event_type=self.OCTOPRINT_PREDICT_START,
            data=dict(filename=filename)
        ))
    def on_octoprint_movie_done(self, payload):
        pass
    def on_octolapse_capture_done(self, payload):
        self._predict_queue.put(dict(
            event_type=self.OCTOLAPSE_PREDICT_START,
            data=payload
        ))
    def on_octolapse_movie_done(self, payload):
        pass

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
    # def get_template_configs(self):
    #     return [
    #         # https://docs.octoprint.org/en/master/modules/plugin.html?highlight=wizard#octoprint.plugin.types.TemplatePlugin
    #         # "mandatory wizard steps will come first, sorted alphabetically, then the optional steps will follow, also alphabetically."
    #         dict(type="wizard", name="Print Nanny Setup", template="print_nanny_wizard.jinja2"),
    #         #dict(type="generic", template="print_nanny_generic_settings.jinja2"),
    #         #dict(type="wizard", name="Setup Account", template="print_nanny_2_wizard.jinja2"),

    #     ]

    ## SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            auth_token=None,
            user_email=None,
            user_url=None,
            api_host='localhost:8000',
            api_uri='http://localhost:8000/api/', # 'https://api.print-nanny.com',
            swagger_json='http://localhost:8000/api/swagger.json', # 'https://api.print-nanny.com/swagger.json'
            prometheus_gateway='https://prom.print-nanny.com'
        )

        
    ## Wizard plugin mixin

    def get_wizard_version(self):
        return 0

    def is_wizard_required(self):

        return any([
            self._settings.get(["auth_token"]) is None,
            self._settings.get(["api_uri"]) is None,
            self._settings.get(["user_email"]) is None,
            self._settings.get(["user_url"]) is None
        ])

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
