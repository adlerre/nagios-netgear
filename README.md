# Nagios Command - Check Netgear

## Compatible devices

This has currently only been tested with the Netgear switch *GS724TPv3*. 

## Usage

optional arguments:

* **-h, --help**<br>
  *optional*
  
  show this help message and exit

API options:

* **-H, --hostname**<br>
  *required*

  hostname or ip address

* **-P, --password**<br>
  *required*

  password

* **-v, --verbose**<br>
  *optional*

  verbose output

check options:

* **-wT, --warningThermal**<br>
  *Default:* `50`

  Warning threshold for thermal value

* **-cT, --criticalThermal**<br>
  *Default:* `70`

  Critical threshold for thermal value

* **-wF, --warningFan**<br>
  *Default:* `90`

  Warning threshold for fan duty value (percent)

* **-cF, --criticalFan**<br>
  *Default:* `100`

  Critical threshold for fan duty value (percent)

* **-cT, --criticalThermal**<br>
  *Default:* `70`

  Critical threshold for thermal value

* **-wM, --warningMemory**<br>
  *Default:* `80`

  Warning threshold for memory (percent)

* **-cM, --criticalMemory**<br>
  *Default:* `90`

  Critical threshold for memory (percent)
