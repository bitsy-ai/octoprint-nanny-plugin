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
import hashlib

import flask
import octoprint.plugin
import pytz

from octoprint.events import eventManager, Events
import octoprint.util
from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
import requests
from PIL import Image
import aiohttp.client_exceptions
import bravado.exception

import print_nanny_client

from print_nanny_client import ApiClient
from print_nanny_client.api.predict_events_api import PredictEventsApi
from print_nanny_client.api.predict_event_files_api import PredictEventFilesApi

from print_nanny_client.api.octoprint_events_api import OctoprintEventsApi
from print_nanny_client.api.print_jobs_api import PrintJobsApi
from print_nanny_client.api.printer_profiles_api import PrinterProfilesApi
from print_nanny_client.api.users_api import UsersApi
from print_nanny_client.api.gcode_files_api import GcodeFilesApi
from print_nanny_client.model.printer_profile_request import PrinterProfileRequest
from print_nanny_client.model.print_job_request import PrintJobRequest
from print_nanny_client.model.octo_print_event_request import OctoPrintEventRequest
from print_nanny_client.model.predict_event_request import PredictEventRequest

from .predictor import ThreadLocalPredictor
from .errors import WebcamSettingsHTTPException, SnapshotHTTPException
from .utils.encoder import NumpyEncoder

logger = logging.getLogger('octoprint.plugins.print_nanny')


CLIENT_EXCEPTIONS = (print_nanny_client.exceptions.ApiException, aiohttp.client_exceptions.ClientError)
class AsyncApiClient(ApiClient):

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def close(self):
        await self.rest_client.close()

class BitsyNannyPlugin(
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.WizardPlugin,
        octoprint.plugin.BlueprintPlugin,
        octoprint.plugin.StartupPlugin,  
        octoprint.plugin.EventHandlerPlugin                
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
            Events.PRINT_STARTED: self._handle_print_start,
            Events.PRINT_FAILED: self._handle_print_job_status,
            Events.PRINT_DONE: self._handle_print_job_status,
            Events.PRINT_CANCELLING: self._handle_print_job_status,
            Events.PRINT_CANCELLED: self._handle_print_job_status,
            Events.PRINT_PAUSED: self._handle_print_job_status,
            Events.UPLOAD: self._handle_file_upload,

        # self._event_bus.subscribe(Events.MOVIE_DONE, self.on_movie_done)
        # self._event_bus.subscribe(Events.PLUGIN_OCTOLAPSE_MOVIE_DONE, self.on_movie_done)
        }

        self._api_objects = {}
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
            'printer_data': self._printer.get_current_data(),
            'printer_profile': self._printer_profile_manager.get_current_or_default(),
            'temperature':  self._printer.get_current_temperatures(),
            'dt': datetime.now(pytz.timezone('America/Los_Angeles')),
            'plugin_version': self._plugin_version,
            'octoprint_version': octoprint.util.version.get_octoprint_version_string()
        }

    def _start(self):
        self._reset()
        self._active = True
        self._queue_predict()

    
    def _queue_predict(self):
        self._predict_queue.put({
            'event_type': self.PREDICT_START, 
            'url': self._settings.global_get(['webcam', 'snapshot'])
        })

    def _queue_upload(self, data):
        self._event_loop.call_soon_threadsafe(self._upload_queue.put_nowait, data)

    
    def _resume(self):
        self._active = True
    
    def _pause(self):
        self._active = False

    async def _drain(self, tries=3):
        if self._predict_queue.qsize() > 0 or self._upload_queue.qsize() > 0 and tries > 0:
            logger.warning(f'Waiting 30s for predict_queue: {self._predict_queue.qsize()} upload_queue {self._upload_queue.qsize()} to drain from queue')
            await asyncio.sleep(30)
            return await self._drain(tries=tries-1)


    def _stop(self):
        self._active = False

    def _reset(self):
        self._api_objects = {}

    def _handle_predict(self, url=None, **kwargs):
        if url is None:
            raise ValueError('Snapshot url is required')

        image_buffer = self._predictor.load_url_buffer(url)
        image_buffer.name = 'original_image.jpg'
        image = self._predictor.load_image(image_buffer)
        prediction = self._predictor.predict(image)
        viz_np = self._predictor.postprocess(image, prediction)

        ## octoprint event
        viz_image = Image.fromarray(viz_np, 'RGB')
        viz_buffer = io.BytesIO()
        viz_buffer.name = 'annotated_image.jpg'
        viz_image.save(viz_buffer,format="JPEG")
        viz_bytes = viz_buffer.getvalue()                     

        self._event_bus.fire(Events.PLUGIN_PRINT_NANNY_PREDICT_DONE, payload={
            'image':  base64.b64encode(viz_bytes)
        })

        self._queue_upload({
                'event_type': self.PREDICT_DONE,
                'original_image': image_buffer,
                'annotated_image':viz_buffer,
                'prediction': prediction,
                'event_data': {}
        })
        if self._active:
            self._queue_predict()

    async def _test_api_auth(self, auth_token, api_url):
        parsed_uri = urlparse(api_url)
        host = f'{parsed_uri.scheme}://{parsed_uri.netloc}'
        api_config = print_nanny_client.Configuration(
            host = host        
            )
        api_config.access_token = auth_token
        async with AsyncApiClient(api_config) as api_client:
            api_instance = UsersApi(api_client=api_client)
            try:
                user = await api_instance.users_me_retrieve()
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_test_api_auth API call failed {e}')
                return
        return user

    async def _handle_file_upload(self, event_type, event_data):

        gcode_file_path = self._file_manager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, event_data['path'])
        gcode_f = open(gcode_file_path, 'rb')
        file_hash = hashlib.md5(gcode_f.read()).hexdigest()
        gcode_f.seek(0)
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = GcodeFilesApi(api_client=api_client)

            try:
                gcode_file = await api_instance.gcode_files_update_or_create(                
                    name=event_data['name'],
                    file_hash=file_hash,
                    file=gcode_f,
                    _check_return_type=False
                )
                logging.info(f'Upserted gcode_file {gcode_file}')
                return gcode_file
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_file_upload API call failed {e}')

    

    async def _handle_print_job_status(self, event_type, event_data):

        print_job = self._api_objects.get('print_job')
        logger.info(f'_handle_print_job_status called for {event_type} in job {print_job}')
        status = event_type.replace('Print', '').upper()

        async with AsyncApiClient(self._api_config) as api_client:
            # printer profile

            if print_job is not None:
                status_enum = print_nanny_client.model.last_status_enum.LastStatusEnum(status)
                api_instance = PrintJobsApi(api_client=api_client)
                try:
                    request = print_nanny_client.model.patched_print_job_request.PatchedPrintJobRequest(
                        last_status=status_enum
                    )
                    print_job = await api_instance.print_jobs_partial_update(
                        print_job.id,
                        patched_print_job_request=request
                    )
                    logger.info(f'Updated print_job.status {print_job.last_status}')
                    self._api_objects['print_job'] = print_job
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f'_handle_print_job_status API called failed {e}')
        
        if status == 'CANCELLING' or status == 'CANCELLED':
            return
        elif status == 'FAILED' or status == 'DONE' or status == 'CANCELLED':
            self._stop()
            self._reset()
        elif status == 'PAUSED':
            self._pause()
        elif status == 'RESUMED':
            self._resume()

    async def _handle_print_start(self, event_type, event_data):

        self._start()
        event_data.update(self._get_metadata())
        async with AsyncApiClient(self._api_config) as api_client:
            # printer profile
            if self._api_objects.get('printer_profile') is None:
                api_instance = PrinterProfilesApi(api_client=api_client)
                request = PrinterProfileRequest(
                    axes_e_inverted=event_data['printer_profile']['axes']['e']['inverted'],
                    axes_x_inverted=event_data['printer_profile']['axes']['x']['inverted'],
                    axes_y_inverted=event_data['printer_profile']['axes']['y']['inverted'],
                    axes_z_inverted=event_data['printer_profile']['axes']['z']['inverted'],
                    axes_e_speed=event_data['printer_profile']['axes']['e']['speed'],
                    axes_x_speed=event_data['printer_profile']['axes']['x']['speed'],
                    axes_y_speed=event_data['printer_profile']['axes']['y']['speed'],
                    axes_z_speed=event_data['printer_profile']['axes']['z']['speed'], 
                    extruder_count=event_data['printer_profile']['extruder']['count'],
                    extruder_nozzle_diameter=event_data['printer_profile']['extruder']['nozzleDiameter'],
                    extruder_shared_nozzle=event_data['printer_profile']['extruder']['sharedNozzle'],
                    name=event_data['printer_profile']['name'],
                    model=event_data['printer_profile']['model'],
                    heated_bed=event_data['printer_profile']['heatedBed'],
                    heated_chamber=event_data['printer_profile']['heatedChamber'],
                    volume_custom_box=event_data['printer_profile']['volume']['custom_box'],
                    volume_depth=event_data['printer_profile']['volume']['depth'],
                    volume_formfactor=event_data['printer_profile']['volume']['formFactor'],
                    volume_height=event_data['printer_profile']['volume']['height'],
                    volume_origin=event_data['printer_profile']['volume']['origin'],
                    volume_width=event_data['printer_profile']['volume']['width'],
                )
                try:
                    printer_profile = await api_instance.printer_profiles_update_or_create(request)
                    logger.info(f'Synced printer_profile {printer_profile.id}')
                    printer_profile_id = printer_profile.id
                    self._api_objects['printer_profile'] = printer_profile
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f'_handle_print_start API called failed {e}')
                    return
            else:
                printer_profile = self._api_objects.get('printer_profile')
        
            # gcode file
            gcode_file_path = self._file_manager.path_on_disk(octoprint.filemanager.FileDestinations.LOCAL, event_data['path'])
            logging.info(f'Hashing contents of gcode file {gcode_file_path}')
            gcode_f = open(gcode_file_path, 'rb')
            file_hash = hashlib.md5(gcode_f.read()).hexdigest()
            gcode_f.seek(0)
            logging.info(f'Retrieving GcodeFile object with file_hash={gcode_file_path}')



            api_instance = GcodeFilesApi(api_client=api_client)
            try:
                gcode_file = await api_instance.gcode_files_update_or_create(
                    name=event_data['name'],
                    file_hash=file_hash,
                    file=gcode_f
                )
                self._api_objects['gcode_file'] = gcode_file
                logger.info(f'Synced gcode_file {gcode_file.id}')
                gcode_file_id = gcode_file.id
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_print_start API call failed {e}')
                gcode_file_id = None


            # print job
            api_instance = PrintJobsApi(api_client=api_client)
            request = print_nanny_client.model.print_job_request.PrintJobRequest(                
                gcode_file=gcode_file_id,
                gcode_file_hash=file_hash,
                dt=event_data['dt'],
                name=event_data['name'],
                printer_profile=printer_profile_id
            )
            try:
                print_job = await api_instance.print_jobs_create(request)
                self._api_objects['print_job'] = print_job
                logger.info(f'Created print_job {print_job.id}')
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_print_start API call failed {e}')



    async def _handle_predict_upload(self, event_type, event_data, annotated_image, prediction, original_image):
        file_hash = hashlib.md5(original_image.read()).hexdigest()

        # reset stream position to prepare for upload
        original_image.seek(0)
        annotated_image.seek(0)
        event_data.update(self._get_metadata())

        async with AsyncApiClient(self._api_config) as api_client:

            api_instance = PredictEventFilesApi(api_client=api_client)

            predict_event_files = await api_instance.predict_event_files_create(
                original_image=original_image,
                annotated_image=annotated_image,
                hash=file_hash
            )
            if not self._api_objects.get('print_job'):
                logger.info('No print_job is active, skipping _handle_predict_upload()')
                return
            request = PredictEventRequest(
                dt=event_data.get('dt'),
                plugin_version=event_data.get('plugin_version'),
                octoprint_version=event_data.get('octoprint_version'),
                event_data=json.loads(json.dumps(event_data, cls=NumpyEncoder)),
                files = predict_event_files.id,
                predict_data=json.loads(json.dumps(prediction, cls=NumpyEncoder)),
                print_job=self._api_objects.get('print_job').id
            )
            try:
                predict_event = await api_instance.predict_events_create(request)
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_predict_upload API call failed failed {e}')

    async def _handle_octoprint_event(self, event_type, event_data, **kwargs):
        # predict events serialize differently
        logger.debug(f'_handle_octoprint_event processing {event_type}')
        if event_type == self.PREDICT_DONE:

            return
        if event_data is not None:
            event_data.update(self._get_metadata())
        else:
            event_data = self._get_metadata()

        if self._api_objects.get('print_job') is not None:
            print_job_id = self._api_objects.get('print_job').id
        else:
            print_job_id = None
            
        async with AsyncApiClient(self._api_config) as api_client:
            api_instance = OctoprintEventsApi(api_client=api_client)
            request = print_nanny_client.model.octo_print_event_request.OctoPrintEventRequest(
                dt=event_data['dt'],
                event_type=event_type,
                event_data=event_data,
                plugin_version=self._plugin_version,
                octoprint_version=event_data['octoprint_version'],
                print_job=print_job_id
            )
            try:
                event = await api_instance.octoprint_events_create(request)
                return event
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_octoprint_event API called failed {e}')

    async def _upload_worker(self):
        '''
            async
        '''
        logger.info('Started _upload_worker thread')
        while True:
            event = await self._upload_queue.get()
            event_type = event.get('event_type')
            if event.get('event_type') is None:
                logger.warning('Ignoring enqueued msg without type declared {event}'.format(event_type=event))
                continue
            handler_fn = self._queue_event_handlers.get(event['event_type'])

            if handler_fn:
                logger.debug(f'Calling handler_fn {handler_fn} in _upload_worker for {event_type}')
                
                try:
                    await handler_fn(**event)
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f'_handle_fn {handler_fn} failed with error {e}')
                logger.debug(f'Calling _handle_octoprint_event {handler_fn} in _upload_worker for {event_type}')

                try:
                    await self._handle_octoprint_event(**event)
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f'_handle_fn {handler_fn} failed with error {e}')
            else:
                try:
                    await self._handle_octoprint_event(**event)
                except CLIENT_EXCEPTIONS as e:
                    logger.error(f'_handle_fn {handler_fn} failed with error {e}')
                    
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
            try:
                handler_fn(**msg)
            except CLIENT_EXCEPTIONS as e:
                logger.error(f'_handle_fn {handler_fn} failed with error {e}')
            self._predict_queue.task_done()

    ##
    ## Octoprint api routes + handlers
    ##
    # def register_custom_routes(self):
    @octoprint.plugin.BlueprintPlugin.route("/startPredict", methods=["POST"])
    def start_predict(self):

        # settings test#
        if self._settings.global_get(['webcam', 'snapshot']) is None:
            raise WebcamSettingsHTTPException()
        url = self._settings.global_get(['webcam', 'snapshot'])
        res = requests.get(url)
        res.raise_for_status()

        if not self._active:
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
        api_url = flask.request.json.get('api_url')
        
        user = asyncio.run_coroutine_threadsafe(self._test_api_auth(
            auth_token,
            api_url
        ), self._event_loop).result()
        self._settings.set(['auth_token'], auth_token)
        self._settings.set(['api_url'], api_url)
        self._settings.set(['user_email'], user.email)
        self._settings.set(['user_url'], user.url)

        self._settings.save()

        logger.info(f'Authenticated as {user}')
        return flask.json.jsonify(user.to_dict())

    def register_custom_events(self):
        return [
            "predict_done", 
            "predict_failed", 
            "upload_done", 
            "upload_failed"
        ]
    
    @property
    def _api_config(self):
        parsed_uri = urlparse(self._settings.get(['api_url']))
        host = f'{parsed_uri.scheme}://{parsed_uri.netloc}'
        config = print_nanny_client.Configuration(
            host = host
        )

        config.access_token = self._settings.get(['auth_token'])
        return config

    def on_event(self, event_type, event_data):
        IGNORED = [ Events.PLUGIN_PRINT_NANNY_PREDICT_DONE ]
        if event_type not in IGNORED:
            self._queue_upload({ 'event_type': event_type, 'event_data': event_data})
            logger.info(f'{event_type} added to upload queue')

    def on_settings_initialized(self):
        '''
            Called after plugin initialization
        '''
        if self._settings.get(['auth_token']) is not None:

            user = asyncio.run_coroutine_threadsafe(self._test_api_auth(
                auth_token=self._settings.get(['auth_token']),
                api_url=self._settings.get(['api_url'])
            ), self._event_loop).result()
            logger.info(f'Authenticated as {user}')

            if user is not None:
                self._settings.set(['user_email'], user.email)
                self._settings.set(['user_url'], user.url)

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
            user=None,
            api_host='http://localhost:8000',
            api_url='http://localhost:8000/api/', # 'https://api.print-nanny.com',
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
            self._settings.get(["api_url"]) is None,
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
