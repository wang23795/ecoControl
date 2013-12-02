import logging
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import utc

from server.models import Actuator, Device, Sensor, SensorEntry
from helpers import create_json_response, create_json_response_from_QuerySet, is_in_group

logger = logging.getLogger('webapi')

def index(request):
    return HttpResponse("BP2013H1")

def api_index(request):
    return create_json_response({ 'version':0.1 })

def api_login(request):
    if request.method == 'POST' and 'username' in request.POST and 'password' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return create_json_response({"login": "successful", "user": request.user.username})
            else:
                return create_json_response({"login": "disabled", "user": request.user.username})
        else:
            return create_json_response({"login": "invalid"})
    else:
        return create_json_response({"login": "failed"})

def api_logout(request):
    logout(request)
    return create_json_response({"logout": "successful"})

def api_status(request):
    if request.user.is_authenticated():
        return create_json_response({"login": "active", "user": request.user.username})
    else:
        return create_json_response({"login": "inactive"})
    
def show_device(request, device_id):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        device = Device.objects.filter(id = int(device_id))
        return create_json_response_from_QuerySet(device)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Device #" + device_id + " does not exists")
        return HttpResponse("Device #" + device_id + " does not exists")

def list_devices(request, limit):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        if not limit:
            limit = 10
        devices = Device.objects.all().order_by('name')[:int(limit)]
            
        return create_json_response_from_QuerySet(devices)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    
def list_actuators(request, device_id, limit):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        if not limit:
            limit = 10
        device_id = int(device_id)
        actuators = Actuator.objects.filter(device_id = device_id).order_by('parameter_name')[:int(limit)]

        return create_json_response_from_QuerySet(actuators)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Device #" + device_id + " does not exists")
        return HttpResponse("Device #" + device_id + " does not exists")

def list_sensors(request, device_id, limit):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        if not limit:
            limit = 10
        device_id = int(device_id)
        sensors = Sensor.objects.filter(device_id = device_id).order_by('name')[:int(limit)]

        return create_json_response_from_QuerySet(sensors)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Device #" + device_id + " does not exists")
        return HttpResponse("Device #" + device_id + " does not exists")
        
def show_actuator(request, actuator_id):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        actuator = Actuator.objects.filter(id = int(actuator_id))
        return create_json_response_from_QuerySet(actuator)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Actuator #" + actuator_id + " does not exists")
        return HttpResponse("Actuator #" + actuator_id + " does not exists")

def show_sensor(request, sensor_id):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        sensor = Sensor.objects.filter(id = int(sensor_id))
        return create_json_response_from_QuerySet(sensor)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Sensor #" + sensor_id + " does not exists")
        return HttpResponse("Sensor #" + sensor_id + " does not exists")

    
def list_sensor_entries(request, sensor_id, start, end, limit):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        sensor_id = int(sensor_id)
        entries = SensorEntry.objects.filter(sensor_id = sensor_id)

        if start:
            start_time = datetime.fromtimestamp(int(start)/1000.0).replace(tzinfo=utc)
            entries = entries.filter(timestamp__gte = start_time)

        if end:
            end_time = datetime.fromtimestamp(int(end)/1000.0).replace(tzinfo=utc)
            entries = entries.filter(timestamp__lte = end_time)

        entries = entries.order_by('-timestamp')
 
        if limit:
            entries = entries[:int(limit)]

        return create_json_response_from_QuerySet(entries)

    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Sensor #" + sensor_id + " does not exists")
        return HttpResponse("Sensor #" + sensor_id + " does not exists")
    
def list_entries(request, device_id, start, end, limit):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        device_id = int(device_id)
        sensors = Sensor.objects.filter(device_id = device_id)

        start_time = end_time = 0
        if start:
                start_time = datetime.fromtimestamp(int(start)/1000.0).replace(tzinfo=utc)
        if end:
                end_time = datetime.fromtimestamp(int(end)/1000.0).replace(tzinfo=utc)

        output = []
        for sensor in sensors:
            if not is_in_group(request.user, sensor.group):
                continue

            entries = SensorEntry.objects.filter(sensor = sensor)
            if start:
                entries = entries.filter(timestamp__gte = start_time)

            if end:
                entries = entries.filter(timestamp__lte = end_time)

            entries = entries.order_by('timestamp')
 
            if limit:
                entries = entries[:int(limit)]

            output.append({
                    'id': sensor.id,
                    'name': sensor.name,
                    'unit': sensor.unit,
                    'data': list(entries.values_list('timestamp', 'value'))
                })

        return create_json_response(output)

    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Device #" + device_id + " does not exists")
        return HttpResponse("Device #" + device_id + " does not exists")

def show_entry(request, entry_id):
    if not request.user.is_authenticated():
        return create_json_response({"permission": "denied"})

    try:
        entry = SensorEntry.objects.filter(id = int(entry_id))
        return create_json_response_from_QuerySet(entry)
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Entry #" + entry_id + " does not exists")
        return HttpResponse("Entry #" + entry_id + " does not exists")

def set_device(request, device_id):
    # if not request.user.is_authenticated():
        # return create_json_response({"permission": "denied"})

    try:
        device = Device.objects.get(id = int(device_id))

        if request.method == 'POST':
            plugin_name = device.name.lower()
            try:
                logger.debug("Trying to load 'plugins." + plugin_name + "'")
                plugin = __import__('plugins.' + plugin_name, globals(), locals(), ['handle_post_data'], -1)
            except ImportError:
                plugin = __import__('plugins.default', globals(), locals(), ['handle_post_data'], -1)

            plugin.handle_post_data(request.POST.dict())
            logger.debug("Post request triggered by " + request.META['REMOTE_ADDR'])
            return create_json_response({"status": "ok"})
        else:
            return create_json_response({"status": "fail"})
    except ValueError:
        logger.error("ValueError")
        return HttpResponse("ValueError")
    except ObjectDoesNotExist:
        logger.warning("Device #" + device_id + " does not exists")
        return HttpResponse("Device #" + device_id + " does not exists")
