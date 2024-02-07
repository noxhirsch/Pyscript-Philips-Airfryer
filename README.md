# Pyscript - Philips Airfryer

> ### :warning: **DISCLAIMER: Use at your own risk only! This code is unofficial (not affiliated with Philips), _probably poorly programmed_ and work in progress. It could theoretically damage your device or property. It could cause errors in the Airfryer, bypass safety features that we don't know about and that way, for example, cause a fire. I'm not responsible for any damage if you use this code anyway. Do not use unattended.** :warning:

<img alt="image" src="https://github.com/noxhirsch/Pyscript-Philips-Airfryer/assets/30938717/93ffddc8-aae4-4a8f-b554-a6a98ffc0a8f">

## Compatibility
| Device | Sensors | Service Calls |
| --- | --- | --- |
| HD9880 | ✅ | ✅ |
| HD9285 | ✅ | unchecked |
| HD9255 | in progress | unchecked |

For other devices at least the sensors should work, but I'd not recommend using the service_calls.
More devices might be added, but requiere your help (collect some data via REST commands and sniff traffic via for example Fiddler Classic).

## Setup
- Get your `client_id` & `client_secret` as described below
- Set up your router to give the Airfryer a static IP
- Install pyscript, add your settings (see example below) to Home Assistant's configuration.yaml and restart Home Assistant
  ```
  pyscript:
    allow_all_imports: true
    apps:
      airfryer:
        airfryer_ip: '192.168.0.123'
        client_id: 'XXXXXXXXXXXXXXXXXXXXXX=='
        client_secret: 'XXXXXXXXXXXXXXXXXXXXXX=='
        # Optional settings (only needed in some cases):
        # command_url: '/di/v1/products/1/airfryer' # Set it to "/di/v1/products/1/venusaf" for some devices (HD9880/90, ...?)
        # airspeed: False              # Set it to True only for HD9880/90
        # probe: False                 # Set it to True only for HD9880/90 & HD9875/90
        # update_interval: '20sec'     # Change interval to update sensor - you can also call service 'pyscript.airfryer_sensors_update' to get an instant update
        # replace_timestamp: False     # Set to True if you block internet for the Airfryer. Replaces wrong device timestamp with correct server timestamp
        # time_remaining: 'disp_time'  # Set it to 'cur_time' for HD9255 (Experimental)
        # time_total: 'total_time'     # Set it to 'time' for HD9255 (Experimental)
  ```
- airfryer.py => Download and move to /config/pyscript/ 
- frontend_card.txt => Create a new "manual card" in the Home Assistant UI and copy & paste the content of the file into it (button-card needs to be installed)


## Some information:
- While testing this script from the very beginning until right before v1.0-beta, I crashed my Airfryer multiple times. So far everything was fine after a reboot and I think I fixed it now - but I can't promise anything.
- All services are described in Home Assistant Dev Tools > Services (search for "pyscript.airfryer_")
- All sensors can be found in Home Assistant Dev Tools > States (search for "pyscript.airfryer_")
- All communication with the Airfryer takes place locally. You can also block the internet connection for the Airfryer - only then should you set `replace_timestamp` in the settings to `True`, otherwise the calculation of the remaining time in the frontend will no longer work.

## How to get the `client_id` and `client_secret`:
1. Create a bootstick with Android x86 and boot from it or install it in Proxmox. It seems to be important that Android x86 and the Airfryer are in the same network & subnet. Installing Android x86 in for example VMware might work, but seems to have some problems. *Ignore this step if you have a rooted Android phone or tablet.*
2. Install NutriU and update Chrome (I recommend using Google Play Store and updating everything)
3. Install SQLite Database Editor: https://play.google.com/store/apps/details?id=com.tomminosoftware.sqliteeditor
4. Open SQLite Database Editor and allow Root for it (if that doesn't work Root might need to be enabled in Android 86 Developer Settings)
5. In the SQLite Database Editor select NutriU > network_node.db > network_node
6. The second last two columns are the ones we are interested in (swipe left to get there)
