# mcp-mcu

This is an MCP (Model Context Protocol) server that supports uploading firmware to ESP32 devices using PlatformIO.

## Features

- 🛠️ Build and upload code to ESP32 boards using the `pio` command
- 🤖 Given an ESP32 board model and a connected module (e.g., BME280), the server can suggest connection guides and code examples
- 📦 Supports both complete PlatformIO projects and inline definitions of `platformio.ini` and `main.cpp`

## Requirements

- Python 3.12 or higher
- [PlatformIO CLI](https://platformio.org/install/cli) must be available in your environment
- `mcp[cli]` must be installed
- Tested on macOS; may also work on Linux or Windows
- Tested using VS Code Copilot integration

## Tested Devices

- Seeed Studio XIAO ESP32C3
- M5Stack Core2

> ⚠️ This project has not been extensively tested. If it doesn't work as expected, I apologize in advance. Contributions and feedback are very welcome!

## Configuration for Copilot settings.json
```
   "mcp": {
       "servers": {
           "esp32-mcp": {
                "timeout": 300,
                "command": "/path/to/uv",
                "args": [
                "--directory",
                "/path/to/mcp_mcu",
                "run",
                "server.py"
                ],
                "env": {},
                "transportType": "stdio"
           }
       }
    }
```