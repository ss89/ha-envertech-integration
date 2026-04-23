# OpenEVT Home Assistant Integration

A Home Assistant custom integration for monitoring Envertech microinverters via the OpenEVT monitoring software. Automatically detects the OpenEVT Supervisor add-on and exposes all inverter data as Home Assistant sensors.

## Features

- **Auto-detection**: Discovers the OpenEVT Supervisor add-on via the Home Assistant Supervisor API
- **Full data exposure**: All inverter fields exposed as sensors (voltage, power, energy, frequency, temperature, firmware info)
- **Manual fallback**: Manual configuration option when the Supervisor add-on is not available
- **Reconfigurable**: Update settings without removing and re-adding the integration
- **Diagnostics**: Built-in diagnostics for troubleshooting
- **Responsive polling**: 5-second update interval for near real-time monitoring
- **Multi-inverter support**: Configure multiple microinverters with semicolon-separated URLs
- **Multiple devices**: One gateway device + one device per microinverter
## Installation

### Prerequisites

- Home Assistant with Supervisor (OS, Supervised, or Core with Supervisor)
- OpenEVT Supervisor add-on installed and running
- Microinverter(s) connected to the same network as the OpenEVT add-on

### Step 1: Install the OpenEVT Supervisor Add-on

Install the OpenEVT add-on from the Home Assistant Community Store (HACS) or manually:

1. Open Home Assistant Supervisor → Add-on Store
2. Search for "OpenEVT" or add the repository
3. Install the OpenEVT add-on
4. Configure the add-on settings:
   - **Address**: LAN address of your microinverter(s) (e.g., `192.168.1.99:14889`)
   - **Serial Number**: Serial number of your microinverter(s)
   - For multiple inverters, separate values with semicolons: `192.168.1.99:14889;192.168.1.100:14889`
5. Start the add-on

### Step 2: Install the Custom Integration

#### Option A: Via HACS (Recommended)

1. Open HACS → Integrations
2. Click the three-dot menu → "Custom repositories"
3. Add this repository URL
4. Search for "OpenEVT" and install
5. Restart Home Assistant

#### Option B: Manual Installation

1. Create the integration directory:
   ```bash
   mkdir -p /config/custom_components/openevt
   ```

2. Copy all files from this repository into `/config/custom_components/openevt/`:
   - `__init__.py`
   - `api.py`
   - `config_flow.py`
   - `const.py`
   - `coordinator.py`
   - `diagnostics.py`
   - `manifest.json`
   - `sensor.py`
   - `strings.json`
   - `py.typed`

3. Restart Home Assistant

## Configuration

After installation, add the integration via the Home Assistant UI:

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for and select **OpenEVT**
4. The integration will **automatically detect** the OpenEVT add-on if it's running
5. If auto-detection fails, you can configure manually:
   - **Inverter Endpoint URL(s)**: HTTP URL to the `/inverter` endpoint (e.g., `http://openevt:9090/inverter`)

For multiple inverters, separate values with semicolons (`;`).

### Configuration Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `url` | String | HTTP URL(s) to the `/inverter` endpoint | `http://openevt:9090/inverter` |

### Reconfiguring

To update the configuration without removing the integration:

1. Go to **Settings** → **Devices & Services**
2. Click on the **OpenEVT** integration
3. Click **Reconfigure**
4. Update the URL(s)
5. Click **Submit**

## Devices & Entities

### Gateway Device: OpenEVT

Tracks the integration status itself.

| Entity | Device Class | Description |
|--------|-------------|-------------|
| Connection Status | Enum | `connected` / `disconnected` |
| Inverter ID | Diagnostic | Inverter ID from the first detected inverter |
### Microinverter Devices: Envertech

One device per microinverter. Each exposes 14 entities:

| Entity | Device Class | Unit | State Class | Description |
|--------|-------------|------|-------------|-------------|
| DC Voltage | Voltage | V | — | Input DC voltage |
| AC Voltage | Voltage | V | — | Output AC voltage |
| Power | Power | W | — | Output AC power |
| Frequency | Frequency | Hz | — | Output AC frequency |
| Energy (Total) | Energy | kWh | Total | Cumulative energy produced |
| Temperature | Temperature | °C | — | Module temperature |

#### Module 1 Sensors
| Entity | Type | Description |
|--------|------|-------------|
| Module ID | Diagnostic | Module identifier string |
| Firmware Version | Diagnostic | Firmware version string |

#### Module 2 Sensors & Info

Identical to Module 1, but for the second microinverter module.

## Data Format

The integration polls the OpenEVT `/inverter` endpoint which returns JSON:

```json
{
  "InverterId": "31583078",
  "Module1": {
    "ModuleId": "...",
    "FirmwareVersion": "1/0",
    "InputVoltageDC": 23.64,
    "OutputPowerAC": 3.59,
    "TotalEnergy": 26.31,
    "Temperature": 29.40,
    "OutputVoltageAC": 233.97,
    "OutputFrequencyAC": 49.97
  },
  "Module2": {
    "ModuleId": "...",
    "FirmwareVersion": "1/0",
    "InputVoltageDC": 24.08,
    "OutputPowerAC": 3.56,
    "TotalEnergy": 22.25,
    "Temperature": 30.20,
    "OutputVoltageAC": 233.97,
    "OutputFrequencyAC": 49.97
  }
}
```

## Diagnostics

The integration provides diagnostics for troubleshooting:

1. Go to **Settings** → **Devices & Services**
2. Click on the **OpenEVT** integration
3. Click the three-dot menu → **Download diagnostics**

The diagnostics include:
- Configuration data (URLs redacted for security)
- Last inverter data collected
- Last update success/failure status
- Last update exception (if any)

Device-specific diagnostics are also available from the device page.

## Troubleshooting

### Integration not detecting the add-on

- Ensure the OpenEVT add-on is **running** (state: `started`)
- Verify the add-on is installed in Home Assistant Supervisor
- Check that `SUPERVISOR` and `SUPERVISOR_TOKEN` environment variables are available
- Use manual configuration as a fallback

### No sensor data appearing

- Verify the inverter endpoint is reachable from Home Assistant
- Check the OpenEVT add-on logs for connection errors
- Confirm the microinverter is powered on and connected
- Check Home Assistant logs for `openevt` errors
- Download diagnostics for more details

### Multiple inverters not working

- Ensure each inverter has a unique address
- Verify addresses are separated by semicolons: `addr1;addr2`

### Entities showing as unavailable

- This is normal when the OpenEVT endpoint is unreachable
- Entities will automatically recover when the connection is restored
- Check the Connection Status entity for the gateway device

## Known Limitations

- Requires Home Assistant Supervisor (not available on Home Assistant Container or Core without Supervisor)
- Only supports Envertech microinverters accessible via the OpenEVT monitoring software
- Does not support firmware updates of microinverters through Home Assistant
- Auto-detection only works when the OpenEVT add-on is installed on the same Supervisor instance

## Supported Devices

This integration works with all Envertech microinverters that are monitored by the OpenEVT software. The OpenEVT software reads data from the microinverters via LAN and exposes it via a REST API.

## Use Cases

### Real-time monitoring

Monitor your solar production in real-time using the power and energy sensors. Create dashboards to visualize daily, weekly, and monthly production.

### Temperature monitoring

Monitor microinverter temperatures to detect overheating issues. Create automations to alert you when temperatures exceed safe thresholds.

### Multi-inverter setup

Track production from multiple microinverters separately. Create automations that respond to individual inverter performance.

## Removal

To remove the OpenEVT integration:

1. Go to **Settings** → **Devices & Services**
2. Click on the **OpenEVT** integration
3. Click the three-dot menu → **Delete**
4. Confirm deletion

This will remove all associated devices and entities. The OpenEVT Supervisor add-on is not affected and can be kept or removed independently.

## Support

This project consists of two separate components:

### OpenEVT (Monitoring Software)

- **Maintained by**: [brandon1024](https://github.com/brandon1024)
- **Repository**: [github.com/brandon1024/openevt](https://github.com/brandon1024/openevt)
- **Issues**: [OpenEVT Issues](https://github.com/brandon1024/openevt/issues)

OpenEVT is the monitoring software that runs as a Home Assistant Supervisor add-on. It communicates with Envertech microinverters over the LAN and exposes their data via a REST API. Report bugs, feature requests, or any issues related to inverter communication, data parsing, or the add-on itself to the OpenEVT repository.

### Home Assistant Integration

- **Maintained by**: [ss89](https://github.com/ss89)
- **Repository**: [github.com/ss89/ha-envertech-integration](https://github.com/ss89/ha-envertech-integration)
- **Issues**: [ha-envertech-integration Issues](https://github.com/ss89/ha-envertech-integration/issues)

This integration connects Home Assistant to the OpenEVT add-on, exposing inverter data as native Home Assistant sensors. Report issues related to integration setup, configuration, sensor data, or Home Assistant compatibility to this repository.

## License

Apache-2.0
