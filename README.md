# Pyscript - Philips Airfryer

> ### :warning: **DISCLAIMER: Use at your own risk only! This code is unofficial (not affiliated with Philips), _probably poorly programmed_ and work in progress. It could damage your device or property. It could cause errors in the Airfryer, bypass its safety features and, for example, cause a fire. I'm not responsible for any damage if you use this code anyway.** :warning:

<img alt="image" src="https://github.com/noxhirsch/Pyscript-Philips-Airfryer/assets/30938717/93ffddc8-aae4-4a8f-b554-a6a98ffc0a8f">

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
        # command_url: '/di/v1/products/1/airfryer' # Optional: Set it to "/di/v1/products/1/venusaf" for some devices (HD9880/90, ...?)
        # airspeed: False          # Optional: Set it to True only for HD9880/90
        # probe: False             # Optional: Set it to True only for HD9880/90 & HD9875/90
        # update_interval: '20sec' # Optional: Change interval to update sensor - you can also call service 'pyscript.airfryer_sensors_update' to get an instant update
        # replace_timestamp: False # Optional: Set to True if you block internet for the Airfryer. Replaces device timestamp with server timestamp
  ```
- airfryer.py => Download and move to /config/pyscript/ 
- frontend_card.txt => Create a new "manual card" in the Home Assistant UI and copy & paste the content of the file into it (button-card needs to be installed)


## Some information:
- While testing I crashed my Airfryer multiple times in the process. So far everything was fine after a reboot and I think I fixed it now - but I can't promise anything.
- You need the clientId & clientSecret of your Airfryer. One way to get it I described below.
- Check the comments in `airfryer.py` for all the settings & services. Also all services are described in Home Assistant Dev Tools > Services (search for "pyscript.airfryer_")
- The file airfryer.py requires pyscript (found in HACS) to run and "Allow All Imports" needs to be enabled in pyscript config.
- The frontend card requires custom:button-card (found in HACS)

## How to get the `client_id` and `client_secret`:
1. Create a bootstick with Android x86 and boot from it or install it in Proxmox. It seems to be important that Android x86 and the Airfryer are in the same network & subnet. Installing Android x86 in for example VMware might work, but seems to have some problems. *Ignore this step if you have a rooted Android phone or tablet.*
2. Install NutriU and update Chrome (I recommend using Google Play Store and updating everything)
3. Install SQLite Database Editor: https://play.google.com/store/apps/details?id=com.tomminosoftware.sqliteeditor
4. Open SQLite Database Editor and allow Root for it (if that doesn't work Root might need to be enabled in Android 86 Developer Settings)
5. In the SQLite Database Editor select NutriU > network_node.db > network_node
6. The second last two columns are the ones we are interested in (swipe left to get there)
