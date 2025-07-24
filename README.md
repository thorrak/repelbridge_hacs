# RepelBridge Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant integration for Liv Repeller devices via WiFi control through RepelBridge.

## Features

This integration provides comprehensive control and monitoring of Liv Repeller devices through Home Assistant:

### Device Control
- **Light Entity**: RGB color control and brightness adjustment (0-255 HA scale)
- **Switch Entity**: Simple power on/off control
- **Number Entities**: Configure auto-shutoff and cartridge warning thresholds

### Monitoring
- **Runtime Tracking**: Monitor cartridge usage in hours
- **Cartridge Life**: Track remaining cartridge life as percentage
- **Device Count**: Number of connected repellers per bus
- **System Status**: WiFi connection, uptime, and device information

### Services
- **Reset Cartridge**: Reset runtime counter to zero via service call

## Installation

### HACS (Recommended)

1. Add this repository to HACS as a custom repository
2. Install "RepelBridge" from the HACS integration page
3. Restart Home Assistant
4. Add the integration through the UI

### Manual Installation

1. Copy the `repelbridge` folder to your `custom_components` directory
2. Restart Home Assistant
3. Add the integration through the UI

## Configuration

### Device Setup

1. Ensure your RepelBridge device is in WiFi mode (`MODE_WIFI_CONTROLLER`)
2. Connect the device to your WiFi network using the captive portal
3. In Home Assistant, go to **Settings** → **Devices & Services**
4. Click **Add Integration** and search for "RepelBridge"
5. Enter the device IP address or hostname

### Automatic Discovery

The integration supports automatic discovery via mDNS. Devices will appear as discovered integrations when connected to the same network.

## Entities

For each bus (0 and 1), the following entities are created:

### Light Entities
- `light.repelbridge_bus_0` - RGB light control with brightness
- `light.repelbridge_bus_1` - RGB light control with brightness

### Switch Entities  
- `switch.repelbridge_bus_0_power` - Power control
- `switch.repelbridge_bus_1_power` - Power control

### Sensor Entities
- `sensor.repelbridge_bus_0_runtime_hours` - Cartridge runtime
- `sensor.repelbridge_bus_0_cartridge_life` - Remaining cartridge life
- `sensor.repelbridge_bus_0_device_count` - Connected repellers
- `sensor.repelbridge_wifi_status` - WiFi connection status
- `sensor.repelbridge_uptime` - System uptime

### Number Entities
- `number.repelbridge_bus_0_auto_shutoff` - Auto shutoff time (seconds)
- `number.repelbridge_bus_0_cartridge_warning` - Warning threshold (hours)

## Services

### Reset Cartridge

Reset the cartridge runtime counter to zero:

```yaml
service: repelbridge.reset_cartridge
data:
  bus_id: 0  # or 1
```

## Automation Examples

### Low Cartridge Warning

```yaml
automation:
  - alias: "RepelBridge Low Cartridge Warning"
    trigger:
      platform: numeric_state
      entity_id: sensor.repelbridge_bus_0_cartridge_life
      below: 10
    action:
      service: notify.mobile_app_your_phone
      data:
        message: "RepelBridge Bus 0 cartridge is running low ({{ states('sensor.repelbridge_bus_0_cartridge_life') }}% remaining)"
```

### Daily Schedule

```yaml
automation:
  - alias: "RepelBridge Daily Schedule"
    trigger:
      platform: time
      at: "20:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.repelbridge_bus_0
        data:
          rgb_color: [0, 213, 255]  # Cyan-blue
          brightness: 200
  
  - alias: "RepelBridge Turn Off"
    trigger:
      platform: time
      at: "06:00:00"
    action:
      service: light.turn_off
      target:
        entity_id: light.repelbridge_bus_0
```

## REST API Endpoints

The integration uses the device's REST API. Direct API access is available at:

- `GET /api/system/status` - System information
- `GET /api/bus/{0,1}/status` - Bus status and settings
- `POST /api/bus/{0,1}/power` - Power control
- `POST /api/bus/{0,1}/brightness` - Brightness control (0-254)
- `POST /api/bus/{0,1}/color` - RGB color control (0-255 each)
- `GET /api/bus/{0,1}/cartridge` - Cartridge monitoring
- `POST /api/bus/{0,1}/cartridge/reset` - Reset cartridge tracking

## Troubleshooting

### Device Not Discovered
- Ensure device is on the same network
- Check device is in WiFi mode (`MODE_WIFI_CONTROLLER`)
- Verify mDNS service `_repelbridge._tcp.local.` is broadcast

### Connection Issues
- Verify IP address is correct
- Check device web interface is accessible at `http://device-ip/api/system/status`
- Ensure firewall allows HTTP traffic on port 80

### Entity Updates
- Default update interval is 30 seconds
- Entities update automatically after control commands
- Check Home Assistant logs for API communication errors

## Support

For issues and feature requests, please use the GitHub repository issue tracker.

## License

This integration is provided under the MIT License.# repelbridge_hacs
