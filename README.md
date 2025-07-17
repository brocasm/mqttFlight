# ⚠️ Work In Progress (WIP) ⚠️

This project is currently a work in progress and is not yet available in an alpha version. Please stay tuned for updates as we continue to develop and improve the system.


# Home Cockpit DIY

A modular Home Cockpit system for flight simulators (like Microsoft Flight Simulator) using a distributed architecture based on ESP32 or D1 Mini microcontrollers, connected to a central Raspberry Pi server via Wi-Fi.

## Features

- **Modular Design**: Each module corresponds to a physical piece of equipment (group of buttons, gauges, LEDs, etc.).
- **Wireless Communication**: Uses Wi-Fi for communication between modules and the server.
- **MQTT Protocol**: Efficient and lightweight communication protocol between modules and server.
- **Central Server**: Raspberry Pi running an MQTT broker, a Node.js server, and a web interface in Svelte.
- **Easy Configuration**: Configurations stored in readable, versionable, and portable JSON files.

## Components

1. **Raspberry Pi Server**:
   - Hosts an MQTT broker.
   - Runs a Node.js server that converts data from FSUI-PC7 via WebSocket and relays information via MQTT.
   - Provides a web interface built with Svelte.
   - Stores configurations in JSON files.

2. **ESP32/D1 Mini Modules**:
   - Each module corresponds to a physical piece of equipment.
   - Connects to the Wi-Fi network.
   - Downloads its script (`main.py`) on startup via HTTP or MQTT.
   - Communicates with the server via MQTT.

## Installation

1. Clone this repository.
2. Follow the instructions in the [Installation Guide](docs/installation.md) to set up the Raspberry Pi server and configure the ESP32/D1 Mini modules.
3. Customize the configurations as needed for your specific setup.

## Usage

1. Power on the Raspberry Pi server and ensure it is connected to the network.
2. Power on the ESP32/D1 Mini modules. They will automatically connect to the Wi-Fi network and download their configurations.
3. Access the web interface to monitor and control the Home Cockpit system.

## Configuration

- Configuration files are stored in JSON format for easy editing and version control.
- Each module's configuration can be customized to match the specific hardware setup.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
