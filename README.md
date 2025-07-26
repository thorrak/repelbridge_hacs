# RepelBridge Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant integration for Liv Repeller pest control devices via WiFi-enabled RepelBridge controllers. This integration enables smart home automation and monitoring of dual-bus RS-485 repeller systems.

## Features

### Device Control
- **RGB Light Control**: Full RGB color selection and brightness adjustment (0-255 HA scale)
- **Power Management**: Simple on/off control per bus with warm-up sequences
- **Dual Bus Support**: Independent control of Bus 0 and Bus 1 with separate repeller networks
- **Auto-Shutoff Configuration**: Set automatic power-off timers (0-16 hours)
- **Cartridge Warning Thresholds**: Configure low-cartridge alerts

### Monitoring & Diagnostics
- **Real-time Cartridge Tracking**: Monitor runtime hours and remaining life percentage
- **Device Count Monitoring**: Track connected repellers per bus
- **System Health**: WiFi status, uptime, and device information
- **Bus State Monitoring**: Online/offline status for each bus

### Smart Home Integration
- **Automatic Discovery**: Zero-configuration setup via mDNS (Zeroconf)
- **Service Actions**: Reset cartridge counters, power cycling
- **Entity Status**: Binary sensors for operational states
- **Configuration Entities**: Number inputs for thresholds and timers

## Installation

### HACS (Recommended)

1. **Add Custom Repository**:
   - Open HACS in Home Assistant
   - Go to **Integrations** → **⋮** → **Custom repositories**
   - Add repository URL: `https://github.com/thorrak/repelbridge_hacs`
   - Select category: **Integration**

2. **Install Integration**:
   - Search for "RepelBridge" in HACS
   - Click **Download**
   - Restart Home Assistant

3. **Configure Device**:
   - Go to **Settings** → **Devices & Services**
   - Click **Add Integration** and search for "RepelBridge"
   - Enter device IP or use automatic discovery

### Manual Installation

1. Download the latest release from GitHub
2. Extract `custom_components/repelbridge/` to your Home Assistant config directory
3. Restart Home Assistant
4. Add the integration through **Settings** → **Devices & Services**

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
- `number.repelbridge_bus_0_auto_shutoff` - Auto shutoff time (minutes)
- `number.repelbridge_bus_0_cartridge_warning` - Warning threshold (hours)

### Button Entities
- `button.repelbridge_bus_0_reset_cartridge` - Reset cartridge runtime counter
- `button.repelbridge_bus_1_reset_cartridge` - Reset cartridge runtime counter

### Binary Sensor Entities
- `binary_sensor.repelbridge_bus_0_status` - Bus operational status
- `binary_sensor.repelbridge_bus_1_status` - Bus operational status

## Services

### Reset Cartridge

Reset the cartridge runtime counter to zero:

```yaml
service: repelbridge.reset_cartridge
target:
  entity_id: light.repelbridge_bus_0
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

## Device Requirements

### Hardware Setup
- **RepelBridge ESP32-C6 Controller** configured in WiFi mode
- **Dual RS-485 Bus Support** for independent repeller networks  
- **WiFi Network Connection** on same network as Home Assistant

### Firmware Configuration
Ensure RepelBridge device is running in `MODE_WIFI_CONTROLLER` mode with:
- Web server enabled on port 80
- mDNS service broadcasting `_repelbridge._tcp.local.`
- REST API endpoints active

## Troubleshooting

### Device Not Discovered
- Ensure device is on the same network as Home Assistant
- Verify device is in WiFi mode (`MODE_WIFI_CONTROLLER`)
- Check mDNS service `_repelbridge._tcp.local.` is broadcasting
- Try manual IP configuration if auto-discovery fails

### Connection Issues
- Verify IP address is correct and device is online
- Test device web interface: `http://device-ip/api/system/status`
- Ensure firewall allows HTTP traffic on port 80
- Check Home Assistant logs for specific error messages

### Entity Updates
- Default update interval is 30 seconds
- Entities update automatically after control commands
- Partial failures handled gracefully (one bus can fail without affecting the other)
- Check Home Assistant logs for API communication errors

### Performance Optimization
- Monitor network latency to device
- Verify stable WiFi connection
- Consider static IP assignment for device
- Check for conflicting integrations polling the same device

## Support

- **Documentation**: [GitHub Repository](https://github.com/thorrak/repelbridge_hacs)
- **Issues**: [Issue Tracker](https://github.com/thorrak/repelbridge_hacs/issues)
- **Maintainer**: [@thorrak](https://github.com/thorrak)

## License

This integration is provided under the MIT License.
