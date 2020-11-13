import asyncio
from datetime import datetime
import logging
import queue
import glob
import threading
import os
import io
from urllib.parse import urlparse
import base64
import json

import flask
import octoprint.plugin
import pytz

from octoprint.events import eventManager, Events
import octoprint.util
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
import requests
from PIL import Image

import bravado.exception

import print_nanny_client
from print_nanny_client.api import events_api, users_api


from .predictor import ThreadLocalPredictor
from .errors import WebcamSettingsHTTPException, SnapshotHTTPException
from .utils.encoder import NumpyEncoder



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
    
    CALIBRATE_START = 'calibrate_start'
    CALIBRATE_DONE = 'calibrate_done'
    CALIBRATE_FAILED = 'calibrate_failed'
    
    PREDICT_START = 'predict_start'
    PREDICT_DONE = 'predict_done'
    PREDICT_FAILED = 'predict_failed'

    UPLOAD_START = 'upload_start'
    UPLOAD_FAILED = 'upload_failed'
    UPLOAD_DONE = 'upload_done'

    def __init__(self, *args, **kwargs):

        # swagger api
        self.swagger_client = None

        # Octolapse plugin
        self._octolapse_data = None
        self._octolapse_snapshot_path = None

        # Threads
        self._active = False
        self._predict_queue = queue.Queue()

        # @todo compare single-threaded perf against multiprocessing.Pool, Queue, Manager
        self._predictor = ThreadLocalPredictor()
        self._predict_thread = threading.Thread(target=self._predict_worker)
        self._predict_thread.daemon = True
        self._predict_thread.start()
        self._queue_event_handlers = {
            self.PREDICT_START: self._handle_predict,
            self.PREDICT_DONE: self._handle_predict_upload,
        }


    

        self._api_thread = threading.Thread(target=self._start_api_loop)
        self._api_thread.daemon = True
        self._api_thread.start() 


    def _start_api_loop(self):
        self._event_loop = asyncio.new_event_loop()
        self._upload_queue = asyncio.Queue(loop=self._event_loop)
        #consumer = asyncio.ensure_future(self._upload_worker())
        self._event_loop.run_until_complete(self._upload_worker())

    def _get_metadata(self):
        return {
            'printer': self._printer.get_current_data(),
            'temperature':  self._printer.get_current_temperatures(),
            'dt': datetime.now(pytz.timezone('America/Los_Angeles')),
            'plugin_version': self.version,
            'octoprint_version': octoprint.util.version.get_octoprint_version_string()
        }

    def _start(self):

        self._reset()
        self._active = True
        self._queue_predict()

    
    def _queue_predict(self):

        return self._predict_queue.put({
            'event_type': self.PREDICT_START, 
            'url': self._settings.global_get(['webcam', 'snapshot'])
        })

    def _queue_upload(self, data):
        metadata = self._get_metadata()
        data['event_data'].update(metadata)
        event_type = data['event_type']
        logger.info(f'Submitting {event_type} to upload_queue')

        self._event_loop.call_soon_threadsafe(self._upload_queue.put_nowait, data)

    
    def _resume(self):
        pass
    
    def _pause(self):
        pass

    def _drain(self):
        while self._predict_queue.qsize() > 0 or self._upload_queue.qsize() > 0:
            logger.warning(f'Waiting for predict_queue: {self._predict_queue.qsize()} upload_queue {self._upload_queue.qsize()} to drain from queue')
            continue

    def _stop(self):
        self._active = False


    def _reset(self):
        pass

    def _handle_predict(self, url=None, **kwargs):
        if url is None:
            raise ValueError('Snapshot url is required')

        image = self._predictor.load_url(url)
        prediction = self._predictor.predict(image)
        viz_np = self._predictor.postprocess(image, prediction)

        ## octoprint event
        viz_image = Image.fromarray(viz_np, 'RGB')
        buffer = io.BytesIO()
        viz_image.save(buffer,format="JPEG")
        viz_bytes = buffer.getvalue()                     

        self._event_bus.fire(Events.PLUGIN_PRINT_NANNY_PREDICT_DONE, payload={
            'image':  base64.b64encode(viz_bytes)
        })

        self._queue_upload({
                'event_type': self.PREDICT_DONE,
                'original_image': image,
                'annotated_image': viz_bytes,
                'event_data': {
                    'pediction': prediction
                }
        })
        if self._active:
            self._queue_predict()
        ## internal queue

    async def _test_api_auth(self, loop=None):
        with print_nanny_client.ApiClient(self._api_config) as api_client:
            api_instance = users_api.UsersApi(api_client=api_client)
            return await api_instance.users_me_retrieve()
        #     user = await future
        # return user

    async def _handle_predict_upload(self, event_type, event_data, annotated_image, original_image):
        with print_nanny_client.ApiClient(self._api_config) as api_client:
            api_instance = events_api.EventsApi(api_client=api_client)
            res = await api_instance.events_predict_create(
                dt=event_data.get('dt'),
                plugin_version=event_data.get('plugin_version'),
                octoprint_version=event_data.get('octoprint_version'),
                original_image=original_image,
                annotated_image=annotated_image,
                event_data=json.dumps(event_data, cls=NumpyEncoder)
            )
            res = await asyncio.run_coroutine_threadsafe(res, self._event_loop)
            logger.info(f'Uploaded predict event {res}')

    async def _upload_worker(self):
        '''
            async
        '''
        logger.info('Started _upload_worker thread')
        while True:
            logger.info(f'awaiting _upload_worker ')

            msg = await self._upload_queue.get()
            logger.info(f'Read _upload_worker msg')
            if not msg.get('event_type'):
                logger.warning('Ignoring enqueued msg without type declared {msg}'.format(msg=msg))
                continue
            handler_fn = self._queue_event_handlers[msg['event_type']]
            logger.info(f'Calling handler_fn {handler_fn}')
            await handler_fn(**msg)
            self._upload_queue.task_done()


    def _predict_worker(self):
        '''
            sync
        '''
        logger.info('Started _predict_worker thread')
        while True:
            msg = self._predict_queue.get(block=True)
            if not msg.get('event_type'):
                logger.warning('Ignoring enqueued msg without type declared {msg}'.format(msg=msg))
                continue
            handler_fn = self._queue_event_handlers[msg['event_type']]
            handler_fn(**msg)
            self._predict_queue.task_done()


    def _predict(self, filename):
        prediction = self._predictor.predict(image)
        prediction['image'] = self._predictor.postprocess(image, prediction)
        return prediction

    ##
    ## Octoprint api routes + handlers
    ##
    # def register_custom_routes(self):
    @octoprint.plugin.BlueprintPlugin.route("/startPredict", methods=["POST"])
    def start_predict(self):

        # settings test#
        if self._settings.global_get(['webcam', 'snapshot']) is None:
            raise WebcamSettingsHTTPException()
        
        # url test
        #try:
        url = self._settings.global_get(['webcam', 'snapshot'])
        res = requests.get(url)
        res.raise_for_status()
        # except:
        #     raise SnapshotHTTPException()

        self._start()
        return flask.json.jsonify({'ok': 1})

    @octoprint.plugin.BlueprintPlugin.route("/stopPredict", methods=["POST"])
    def stop_predict(self):
        self._drain()
        self._stop()
        return flask.json.jsonify({'ok': 1})


    @octoprint.plugin.BlueprintPlugin.route("/testAuthToken", methods=["POST"])
    def test_auth_token(self):
        auth_token = flask.request.json.get('auth_token')
        api_uri = flask.request.json.get('api_uri')
        
        self._api_config = print_nanny_client.Configuration(
            host = self._settings.get(['api_host']),
        )
        self._api_config.access_token = self._settings.get(['auth_token'])

        user = asyncio.run_coroutine_threadsafe(self._test_api_auth(), self._event_loop).result()
        logger.info(f'Authenticated as {user}')
        return flask.json.jsonify(user.to_dict())


    def register_custom_events(self):
        return [
            "predict_done", 
            "predict_failed", 
            "upload_done", 
            "upload_failed"
        ]
    
    
    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)


        self._api_config = print_nanny_client.Configuration(
            host = self._settings.get(['api_host']),
            access_token = self._settings.get(['auth_token'])
        )

        user = asyncio.run_coroutine_threadsafe(self._test_api_auth(), self._event_loop).result()
        logger.info(f'Authenticated as {user}')

    def on_settings_initialized(self):
        '''
            Called after plugin initialization
        '''
        if self._settings.get(['auth_token']) is not None:

            self._api_config = print_nanny_client.Configuration(
                host = self._settings.get(['api_host']),
            )
            self._api_config.access_token = self._settings.get(['auth_token'])

            user = asyncio.run_coroutine_threadsafe(self._test_api_auth(), self._event_loop).result()
            logger.info(f'Authenticated as {user}')


        # Octoprint events
        self._event_bus.subscribe(Events.PRINT_STARTED, self.on_print_started)
        self._event_bus.subscribe(Events.PRINT_RESUMED, self.on_print_resume)
        self._event_bus.subscribe(Events.PRINT_PAUSED, self.on_print_paused)
        self._event_bus.subscribe(Events.PRINT_FAILED, self.on_print_failed)
        self._event_bus.subscribe(Events.PRINT_DONE, self.on_print_done)
        self._event_bus.subscribe(Events.PRINT_CANCELLED, self.on_print_cancelled)
        
        self._event_bus.subscribe(Events.MOVIE_DONE, self.on_movie_done)
        self._event_bus.subscribe(Events.PLUGIN_OCTOLAPSE_MOVIE_DONE, self.on_movie_done)
        # Octolapse events

    def on_movie_done(self, payload):
        data = { 'event_type': Events.MOVIE_DONE, 'event_data': payload }
        self._event_data[Events.MOVIE_DONE] = data
        self._queue_upload(data)

    def on_print_cancelled(self, payload):

        data = {'event_type': Events.PRINT_CANCELLED, 'event_data': payload }
        self._event_data[Events.PRINT_CANCELLED] = data
        self._queue_upload(data)
        
        self._drain()
        self._stop()
        self._reset()

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
        data = {'event_type': Events.PRINT_STARTED, 'event_data': payload}
        self._event_data[Events.PRINT_STARTED] = data
        self._queue_upload(data)
        
        self._start()

    def on_print_resume(self, payload):
        '''
            payload

                name: the file’s name
                path: the file’s path within its storage location
                origin: the origin storage location of the file, either local or sdcard
                size: the file’s size in bytes (if available)
                owner: the user who started the print job (if available)
                user: the user who resumed the print job (if available)
        '''
        data = {'event_type': Events.PRINT_RESUMED, 'event_data': payload }
        self._event_data[Events.PRINT_RESUMED ] = data
        self._queue_upload(data)
        
        self._resume()
    
    def on_print_paused(self, payload):
        '''
            payload
                name: the file’s name
                path: the file’s path within its storage location
                origin: the origin storage location of the file, either local or sdcard
                size: the file’s size in bytes (if available)
                owner: the user who started the print job (if available)
                user: the user who paused the print job (if available)
                position: the print head position at the time of pausing (if available, not available if the recording of the position on pause is disabled or the pause is completely handled by the printer’s firmware)
                position.x: x coordinate, as reported back from the firmware through M114
                position.y: y coordinate, as reported back from the firmware through M114
                position.z: z coordinate, as reported back from the firmware through M114
                position.e: e coordinate (of currently selected extruder), as reported back from the firmware through M114
                position.t: last tool selected through OctoPrint (note that if you did change the printer’s selected tool outside of OctoPrint, e.g. through the printer controller, or if you are printing from SD, this will NOT be accurate)
                position.f: last feedrate for move commands sent through OctoPrint (note that if you modified the feedrate outside of OctoPrint, e.g. through the printer controller, or if you are printing from SD, this will NOT be accurate)
        '''

        data = {'event_type': Events.PRINT_PAUSED, 'event_data': payload }
        self._event_data[Events.PRINT_PAUSED ] = data
        self._queue_upload(data)

        self._pause()

    def on_print_done(self, payload):
        '''
            payload
                name: the file’s name
                path: the file’s path within its storage location
                origin: the origin storage location of the file, either local or sdcard
                size: the file’s size in bytes (if available)
                owner: the user who started the print job (if available)
                time: the time needed for the print, in seconds (float)
        '''
        data = {'event_type': Events.PRINT_DONE, 'event_data': payload }
        self._event_data[Events.PRINT_DONE ] = data
        self._queue_upload(data)
  

        self._drain()
        self._stop()
        self._reset()

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
        data = {'event_type': Events.PRINT_FAILED, 'event_data': payload  }
        self._event_data[Events.PRINT_FAILED ] = data
        self._queue_upload(data)

        self._drain()
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
            api_host='http://localhost:8000',
            api_uri='http://localhost:8000/api/', # 'https://api.print-nanny.com',
            swagger_json='http://localhost:8000/api/swagger.json', # 'https://api.print-nanny.com/swagger.json'
            prometheus_gateway='https://prom.print-nanny.com',
            # ./mjpg_streamer -i "./input_raspicam.so" -o "./output_file.so -f /tmp/ -s 20 -l mjpg-streamer-latest.jpg"
            # snapshot='file:///tmp/mjpg-streamer-latest.jpg'
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
