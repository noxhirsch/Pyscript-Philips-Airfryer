################### SETTINGS ###################
airfryer_ip       = '192.168.0.123'
client_id         = 'XXXXXXXXXXXXXXXXXXXXXX=='
client_secret     = 'XXXXXXXXXXXXXXXXXXXXXX=='
airspeed          = False   # True for HD9880/90 else set to False
probe             = False   # True for HD9880/90 & HD9875/90 else set to False
command_url       = "/di/v1/products/1/airfryer" # replace with "/di/v1/products/1/venusaf" for some devices (HD9880/90, ...?)

update_interval   = '20sec' # Interval to update sensor - you can also call service 'pyscript.airfryer_sensors_update' to get an instant update
sleep_time        = 0.1     # Since I added a new type of "command-crash-detection", 100ms sleep time should be enough
replace_timestamp = False   # If internet access is blocked for the airfryer, it loses the time. This replaces the device timestamp with the server timestamp (time display may be off by 1-2 seconds as a result)

response_time     = False   # For debugging purposes
debug_offline     = False   # For debugging purposes

############## AVAILABLE SERVICES ##############
### All services are described when you select them in Home Assistant Dev Tools > Services (or of course in the code below)
### For all devices:
# pyscript.airfryer_sensors_update
# pyscript.airfryer_turn_on
# pyscript.airfryer_turn_off
# pyscript.airfryer_start_cooking
# pyscript.airfryer_adjust_time
# pyscript.airfryer_adjust_temp
# pyscript.airfryer_pause
# pyscript.airfryer_start_resume
# pyscript.airfryer_stop

### Additional/Modified services for HD9880/90:
# pyscript.airfryer_start_cooking
# pyscript.airfryer_toggle_airspeed

################### CREDITS ####################
# Based on Carsten T.'s findings on how to authenticate:
# https://community.home-assistant.io/t/philips-airfryer-nutriu-integration-alexa-only/544333/15

################################################
##################### CODE #####################
################################################
import base64
import hashlib
import requests
import json
import datetime
import asyncio

state.persist('pyscript.airfryer_token', '')
state.persist('pyscript.airfryer_status')
state.persist('pyscript.airfryer_temp',default_attributes={'unit_of_measurement':'°C'})
state.persist('pyscript.airfryer_timestamp')
state.persist('pyscript.airfryer_total_time')
state.persist('pyscript.airfryer_disp_time')
state.persist('pyscript.airfryer_progress',default_attributes={'unit_of_measurement':'%'})
state.persist('pyscript.airfryer_drawer_open')
state.persist('pyscript.airfryer_dialog')
if airspeed:
    state.persist('pyscript.airfryer_airspeed')
else:
    if 'pyscript.airfryer_airspeed' in state.names('pyscript'):
        state.delete('pyscript.airfryer_airspeed')
if probe:
    state.persist('pyscript.airfryer_temp_probe',default_attributes={'unit_of_measurement':'°C'})
    state.persist('pyscript.airfryer_probe_unplugged')
else:
    if 'pyscript.airfryer_temp_probe' in state.names('pyscript'):
        state.delete('pyscript.airfryer_temp_probe')
    if 'pyscript.airfryer_probe_unplugged' in state.names('pyscript'):
        state.delete('pyscript.airfryer_probe_unplugged')
if response_time:
    state.persist('pyscript.airfryer_response_time',default_attributes={'unit_of_measurement':'sec'})
else:
    if 'pyscript.airfryer_response_time' in state.names('pyscript'):
        state.delete('pyscript.airfryer_response_time')


airfryer_session = requests.Session()
requests.packages.urllib3.disable_warnings()
command_in_progress = False
false = False


@service
@time_trigger("startup", "period(now, "+update_interval+")")
def airfryer_sensors_update():
    global command_in_progress
    if not command_in_progress:
        command_in_progress = True
        response = get_status(pyscript.airfryer_token)
        if response[0] == "token":
            pyscript.airfryer_token = response[1]
            response = get_status(pyscript.airfryer_token)
            log.info("Airfryer: New Token generated")
        if debug_offline and response[0] == "offline":
            log.error(response[1])
        set_entities(response)
        await asyncio.sleep(sleep_time)
        command_in_progress = False
    else:
        log.info("Airfryer: Sensor update command crash avoided")


@service
def airfryer_turn_on():
    """yaml
    name: Airfryer Turn On
    description: Turns the Airfryer on (into precook mode).
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    command = {"probe_required": false ,"method":0,"status":"precook","temp_unit":false}
    response = send_command(pyscript.airfryer_token,command)
    set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False

@service
def airfryer_turn_off():
    """yaml
    name: Airfryer Turn Of
    description: Turns the Airfryer off (and stops it before if needed).
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    if pyscript.airfryer_status == "cooking":
        command = {"status":"pause"}
        response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
    if pyscript.airfryer_status != "mainmenu":
        command = {"status":"mainmenu"}
        response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
    command = {"status":"powersave"}
    response = send_command(pyscript.airfryer_token,command)
    set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False

if airspeed:
    @service
    def airfryer_start_cooking(temp=180,total_time=60,airspeed=2,start_cooking=True,force_update=True):
        """yaml
        name: Airfryer Start Cooking
        description: Turns the Airfryer on, sets it up and starts cooking (if not disabled).
        fields:
            temp:
                description: Cooking temperature (range depends on your device)
                name: Temperature
                example: 180
                selector:
                    number:
                        min: 40
                        max: 200
                        mode: box
                        unit_of_measurement: "°C"
            total_time:
                description: Cooking duration in seconds
                name: Total Time
                example: 600
                selector:
                    number:
                        min: 60
                        max: 86400
                        mode: box
                        unit_of_measurement: s
            airspeed:
                description: Airspeed 1 or 2
                name: Airspeed
                example: 1
                selector:
                    number:
                        min: 1
                        max: 2
                        mode: box
            start_cooking:
                description: If disabled, everything is set up, but not started
                name: Start Cooking
                example: True
                selector:
                    boolean:
            force_update:
                description: Only set to False if you know what you are doing.
                name: Force Sensor Update
                example: True
                advanced: True
                selector:
                    boolean:
        """
        global command_in_progress
        loop_count = 0
        while(command_in_progress == True and loop_count<50):
            loop_count += 1
            await asyncio.sleep(0.1)
            log.info("Airfryer: Waiting ...")
        command_in_progress = True
        if force_update:
            airfryer_sensors_update()
            await asyncio.sleep(0.1)
        if pyscript.airfryer_status != "cooking":
            if pyscript.airfryer_status == "pause" or pyscript.airfryer_status == "finish":
                command = {"status":"mainmenu"}
                response = send_command(pyscript.airfryer_token,command)
                await asyncio.sleep(sleep_time)
            command = {"probe_required": false ,"method":0,"status":"precook","temp_unit":false}
            response = send_command(pyscript.airfryer_token,command)
            await asyncio.sleep(sleep_time)
            command = {"temp":temp,"method":0,"probe_required":false,"airspeed":airspeed,"total_time":total_time,"temp_unit":false}
            response = send_command(pyscript.airfryer_token,command)
            if start_cooking:
                await asyncio.sleep(sleep_time)
                command = {"status":"cooking"}
                response = send_command(pyscript.airfryer_token,command)
            set_entities(response)
        await asyncio.sleep(sleep_time)
        command_in_progress = False
else:
    @service
    def airfryer_start_cooking(temp=180,total_time=60,start_cooking=True,force_update=True):
        """yaml
        name: Airfryer Start Cooking
        description: Turns the Airfryer on, sets it up and starts cooking (if not disabled).
        fields:
            temp:
                description: Cooking temperature (range depends on your device)
                name: Temperature
                example: 180
                selector:
                    number:
                        min: 40
                        max: 200
                        mode: box
                        unit_of_measurement: "°C"
            total_time:
                description: Cooking duration in seconds
                name: Total Time
                example: 600
                selector:
                    number:
                        min: 60
                        max: 86400
                        mode: box
                        unit_of_measurement: s
            start_cooking:
                description: If disabled, everything is set up, but not started
                name: Start Cooking
                example: True
                selector:
                    boolean:
            force_update:
                description: Only set to False if you know what you are doing.
                name: Force Sensor Update
                example: True
                advanced: True
                selector:
                    boolean:
        """
        global command_in_progress
        loop_count = 0
        while(command_in_progress == True and loop_count<50):
            loop_count += 1
            await asyncio.sleep(0.1)
            log.info("Airfryer: Waiting ...")
        command_in_progress = True
        if force_update:
            airfryer_sensors_update()
            await asyncio.sleep(0.1)
        if pyscript.airfryer_status != "cooking":
            if pyscript.airfryer_status == "pause" or pyscript.airfryer_status == "finish":
                command = {"status":"mainmenu"}
                response = send_command(pyscript.airfryer_token,command)
                await asyncio.sleep(sleep_time)
            command = {"probe_required": false ,"method":0,"status":"precook","temp_unit":false}
            response = send_command(pyscript.airfryer_token,command)
            await asyncio.sleep(sleep_time)
            command = {"temp":temp,"method":0,"probe_required":false,"total_time":total_time,"temp_unit":false}
            response = send_command(pyscript.airfryer_token,command)
            if start_cooking:
                await asyncio.sleep(sleep_time)
                command = {"status":"cooking"}
                response = send_command(pyscript.airfryer_token,command)
            set_entities(response)
        await asyncio.sleep(sleep_time)
        command_in_progress = False

@service
def airfryer_adjust_time(time=0,method="add",restart_cooking=True,force_update=True):
    """yaml
    name: Airfryer Adjust Time
    description: Adjust the time if Airfryer is in precook mode, paused or cooking. Subtraction is limited - remaining time must be at least a minute.
    fields:
        time:
            description: Seconds to add or subtract
            name: Time
            example: 600
            required: true
            selector:
                number:
                    min: 1
                    max: 86400
                    mode: box
                    unit_of_measurement: s
        method:
            description: Add or subtract
            name: Method
            example: add
            required: true
            selector:
                select:
                    options:
                        - add
                        - subtract
        restart_cooking:
            description: If disabled, the Airfryer will not restart cooking (if it was cooking before).
            name: Restart Cooking
            example: True
            selector:
                boolean:
        force_update:
            description: Only set to False if you know what you are doing.
            name: Force Sensor Update
            example: True
            advanced: True
            selector:
                boolean:
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    if force_update:
        airfryer_sensors_update()
        await asyncio.sleep(0.1)
    if pyscript.airfryer_status == "cooking":
        command = {"status":"pause"}
        response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
        if method == "add":
            command = {"total_time":int(pyscript.airfryer_total_time) + time}
            response = send_command(pyscript.airfryer_token,command)
        elif method == "subtract":
            command = {"total_time":int(pyscript.airfryer_total_time) - time}
            response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
        if restart_cooking:
            await asyncio.sleep(sleep_time)
            command = {"status":"cooking"}
            response = send_command(pyscript.airfryer_token,command)
        set_entities(response)
    elif pyscript.airfryer_status == "pause" or pyscript.airfryer_status == "precook":
        if method == "add":
            command = {"total_time":int(pyscript.airfryer_total_time) + time}
            response = send_command(pyscript.airfryer_token,command)
        elif method == "subtract":
            command = {"total_time":int(pyscript.airfryer_total_time) - time}
            response = send_command(pyscript.airfryer_token,command)
        set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False

@service
def airfryer_adjust_temp(temp=0,method="add",restart_cooking=True,force_update=True):
    """yaml
    name: Airfryer Adjust Temperature
    description: Adjust the temperature if Airfryer is in precook mode, paused or cooking. Limited to the available range on your device
    fields:
        temp:
            description: Degrees to add or subtract
            name: Temperature
            example: 10
            required: true
            selector:
                number:
                    min: 1
                    max: 160
                    mode: box
                    unit_of_measurement: "°C"
        method:
            description: Add or subtract
            name: Method
            example: add
            required: true
            selector:
                select:
                    options:
                        - add
                        - subtract
        restart_cooking:
            description: If disabled, the Airfryer will not restart cooking (if it was cooking before).
            name: Restart Cooking
            example: True
            selector:
                boolean:
        force_update:
            description: Only set to False if you know what you are doing.
            name: Force Sensor Update
            example: True
            advanced: True
            selector:
                boolean:
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    if force_update:
        airfryer_sensors_update()
        await asyncio.sleep(0.1)
    if pyscript.airfryer_status == "cooking":
        command = {"status":"pause"}
        response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
        if method == "add":
            command = {"temp":int(pyscript.airfryer_temp) + temp}
            response = send_command(pyscript.airfryer_token,command)
        elif method == "subtract":
            command = {"temp":int(pyscript.airfryer_temp) - temp}
            response = send_command(pyscript.airfryer_token,command)
        if restart_cooking:
            await asyncio.sleep(sleep_time)
            command = {"status":"cooking"}
            response = send_command(pyscript.airfryer_token,command)
        set_entities(response)
    elif pyscript.airfryer_status == "pause" or pyscript.airfryer_status == "precook":
        if method == "add":
            command = {"temp":int(pyscript.airfryer_temp) + temp}
            response = send_command(pyscript.airfryer_token,command)
        elif method == "subtract":
            command = {"temp":int(pyscript.airfryer_temp) - temp}
            response = send_command(pyscript.airfryer_token,command)
        set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False

if airspeed:
    @service
    def airfryer_toggle_airspeed():
        """yaml
        name: Airfryer Toggle Airspeed
        description: Toggles the Airspeed between high and low.
        """
        global command_in_progress
        loop_count = 0
        while(command_in_progress == True and loop_count<50):
            loop_count += 1
            await asyncio.sleep(0.1)
            log.info("Airfryer: Waiting ...")
        command_in_progress = True
        airfryer_sensors_update()
        await asyncio.sleep(0.1)
        if pyscript.airfryer_status == "cooking":
            status_before = "cooking"
            command = {"status":"pause"}
            response = send_command(pyscript.airfryer_token,command)
            await asyncio.sleep(sleep_time)
            if pyscript.airfryer_airspeed == "2":
                command = {"airspeed":1}
                response = send_command(pyscript.airfryer_token,command)
                set_entities(response)
            elif pyscript.airfryer_airspeed == "1":
                command = {"airspeed":2}
                response = send_command(pyscript.airfryer_token,command)
                set_entities(response)
            command = {"status":"cooking"}
            response = send_command(pyscript.airfryer_token,command)
        elif pyscript.airfryer_status == "precook" or pyscript.airfryer_status == "pause":
            if pyscript.airfryer_airspeed == "2":
                command = {"airspeed":1}
                response = send_command(pyscript.airfryer_token,command)
                set_entities(response)
            elif pyscript.airfryer_airspeed == "1":
                command = {"airspeed":2}
                response = send_command(pyscript.airfryer_token,command)
                set_entities(response)
        await asyncio.sleep(sleep_time)
        command_in_progress = False


@service
def airfryer_pause():
    """yaml
    name: Airfryer Pause
    description: Pauses the Airspeed.
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    command = {"status":"pause"}
    response = send_command(pyscript.airfryer_token,command)
    set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False


@service
def airfryer_start_resume():
    """yaml
    name: Airfryer Start/Resume
    description: Startes the Airfryer if everything is set up or resumes if paused.
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    command = {"status":"cooking"}
    response = send_command(pyscript.airfryer_token,command)
    set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False


@service
def airfryer_stop():
    """yaml
    name: Airfryer Stop
    description: Stops the Airfryer and returns to main menu.
    """
    global command_in_progress
    loop_count = 0
    while(command_in_progress == True and loop_count<50):
        loop_count += 1
        await asyncio.sleep(0.1)
        log.info("Airfryer: Waiting ...")
    command_in_progress = True
    airfryer_sensors_update()
    await asyncio.sleep(0.1)
    if pyscript.airfryer_status == "cooking":
        command = {"status":"pause"}
        response = send_command(pyscript.airfryer_token,command)
        await asyncio.sleep(sleep_time)
    # command = {"preheat":false,"status":"finish"}
    command = {"status":"mainmenu"}
    response = send_command(pyscript.airfryer_token,command)
    set_entities(response)
    await asyncio.sleep(sleep_time)
    command_in_progress = False




@pyscript_executor
def get_status(airfryer_token):
    if airfryer_token == "":
        headers = {"User-Agent":"cml","Content-Type":"application/json"}
    else:
        headers = {"User-Agent":"cml","Content-Type":"application/json","Authorization":"PHILIPS-Condor "+airfryer_token}
    
    try:
        response = airfryer_session.get("https://" + airfryer_ip + command_url, headers=headers, verify=False, timeout=10)
    except requests.exceptions.RequestException as e:
        return "offline", e
    
    if response.status_code == 401:
        challenge = response.headers.get('WWW-Authenticate')
        challenge = challenge.replace('PHILIPS-Condor ', '')
        auth = getAuth(client_id, client_secret, challenge)
        return "token", auth
    elif response.status_code != 200:
        return "offline", response.status_code
    else:
        return "online", response


@pyscript_executor
def send_command(airfryer_token,command):
    headers = {"User-Agent":"cml","Content-Type":"application/json","Authorization":"PHILIPS-Condor "+airfryer_token}
    try:
        response = airfryer_session.put("https://" + airfryer_ip + command_url, headers=headers, data=json.dumps(command), verify=False, timeout=10)
    except requests.exceptions.RequestException as e:
        return "offline", e

    if response.status_code != 200:
        return "offline", response.status_code
    else:
        return "online", response


@pyscript_compile
def decode(txt):
    return base64.standard_b64decode(txt)


@pyscript_compile
def getAuth(client_id, client_secret, challenge):
    vvv = decode(challenge) + decode(client_id) + decode(client_secret)
    myhash = hashlib.sha256(vvv).hexdigest()
    myhashhex = bytes.fromhex(myhash)
    res = decode(client_id) + myhashhex
    encoded = base64.b64encode(res)
    return encoded.decode("ascii")


def set_entities(response):
    if response[0] == "offline":
        pyscript.airfryer_status = "offline"
        pyscript.airfryer_temp = "0"
        pyscript.airfryer_drawer_open = False
        pyscript.airfryer_dialog = "none"
        pyscript.airfryer_timestamp = ""
        pyscript.airfryer_total_time = ""
        pyscript.airfryer_disp_time = ""
        pyscript.airfryer_progress = 0
        pyscript.airfryer_response_time = 0
        if airspeed:
            pyscript.airfryer_airspeed = 0
        if probe:
            pyscript.airfryer_temp_probe = 0
            pyscript.airfryer_probe_unplugged = True
    elif response[0] == "online":
        content = json.loads(response[1].content)
        pyscript.airfryer_status = content.get('status')
        pyscript.airfryer_temp = content.get('temp')
        pyscript.airfryer_drawer_open = content.get('drawer_open')
        pyscript.airfryer_dialog = content.get('dialog')
        pyscript.airfryer_response_time = round(response[1].elapsed.total_seconds(),3)
        if content.get('disp_time') == 0 or content.get('status') == "standby" or content.get('status') == "powersave":
            pyscript.airfryer_progress = 0
            pyscript.airfryer_timestamp = ""
            pyscript.airfryer_total_time = ""
            pyscript.airfryer_disp_time = ""
        else:
            pyscript.airfryer_progress = round((content.get('total_time')-content.get('disp_time'))/content.get('total_time')*100,1)
            if replace_timestamp:
                pyscript.airfryer_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                pyscript.airfryer_timestamp = datetime.datetime.strptime(content.get('timestamp'), '%Y-%m-%dT%H:%M:%SZ')
            pyscript.airfryer_total_time = content.get('total_time')
            pyscript.airfryer_disp_time = content.get('disp_time')
        if airspeed:
            pyscript.airfryer_airspeed = content.get('airspeed')
        if probe:
            pyscript.airfryer_temp_probe = content.get('temp_probe')
            pyscript.airfryer_probe_unplugged = content.get('probe_unplugged')
