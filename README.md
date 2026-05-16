# PCS Pool for Home Assistant

Custom integration for Home Assistant that reads pool controller data from PCS Web API.

## Features

- Direct PCS Web API access
- No MQTT required
- No browser automation
- Native Home Assistant entities

## Entities

- pH
- Redox
- Chlorine
- Bound chlorine
- Temperature
- Flow in L/min
- Salt
- Pump mode
- Last update
- Pump state
- Online state

## Installation with HACS

1. In HACS, open the three-dot menu.
2. Choose **Custom repositories**.
3. Add this repository URL.
4. Select category **Integration**.
5. Install **PCS Pool**.
6. Restart Home Assistant.
7. Go to **Settings → Devices & services → Add integration → PCS Pool**.
8. Enter your PCS portal login and password.

## Manual installation

Copy:

```text
custom_components/pcs_pool
```

to:

```text
/config/custom_components/pcs_pool
```

Then restart Home Assistant.
