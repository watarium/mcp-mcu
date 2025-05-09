# uploader_service/src/uploader_service/server.py

import asyncio, logging, subprocess, tempfile
from pathlib import Path
from typing import Any, List

from mcp.server import Server
from mcp.types import TextContent, Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uploader")

app = Server("firmware-uploader")

# ---------------------------------------------------------------------------
# 1) Tool Definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="build_upload",
            description=(
                "Build and flash a microcontroller using either an existing PlatformIO project (project_dir), "
                "or by providing both platformio_ini and main.cpp source code."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string", "description": "e.g., esp32dev, uno"},
                    "project_dir": {"type": "string", "description": "Path to an existing PlatformIO project (optional)"},
                    "platformio_ini": {"type": "string", "description": "Contents of platformio.ini (required if project_dir not provided)"},
                    "src": {"type": "string", "description": "Contents of main.cpp (required if project_dir not provided)"},
                    "port": {"type": "string", "description": "e.g., /dev/ttyUSB0", "default": "/dev/ttyUSB0"},
                    "baud": {"type": "integer", "default": 115200}
                },
                "required": ["board_id"]
            }
        ),
        Tool(
            name="check_connection_guide",
            description=(
                "Given a board_id (e.g., seeed_xiao_esp32c3) and a module (e.g., BME280), "
                "the LLM should respond with a pin connection guide. "
                "If the combination is unknown, search the internet or use known patterns to make a best effort guess."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "board_id": {"type": "string"},
                    "module": {"type": "string", "description": "e.g. BME280, OLED SSD1306, etc."}
                },
                "required": ["board_id", "module"]
            }
        )
    ]

# ---------------------------------------------------------------------------
# 2) Tool Implementations
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: Any):
    if name == "build_upload":
        return await handle_build_upload(arguments)

    elif name == "check_connection_guide":
        return [
            TextContent(
                type="text",
                text=(
                    "ℹ️ This tool is designed to suggest how to connect your board and module.\n"
                    "Please wait while the AI composes a connection guide, or try describing the hardware in more detail."
                )
            )
        ]

    else:
        raise ValueError(f"unknown tool {name}")

# ---------------------------------------------------------------------------
# Build and upload logic using PlatformIO's native upload
# ---------------------------------------------------------------------------

async def handle_build_upload(arguments: Any):
    try:
        board = arguments["board_id"]
        port = arguments.get("port", "/dev/ttyUSB0")
        baud = int(arguments.get("baud", 115200))

        # Determine project source
        project_dir = arguments.get("project_dir")
        if project_dir:
            project_path = Path(project_dir).expanduser().resolve()
            if not project_path.exists() or not (project_path / "platformio.ini").exists():
                raise FileNotFoundError(f"platformio.ini not found in: {project_path}")
        else:
            platformio_ini = arguments.get("platformio_ini")
            src = arguments.get("src")
            if not platformio_ini or not src:
                raise ValueError("Either project_dir or both platformio_ini and src must be provided.")
            project_path = Path(tempfile.mkdtemp())
            (project_path / "src").mkdir(parents=True, exist_ok=True)
            (project_path / "platformio.ini").write_text(platformio_ini, encoding="utf-8")
            (project_path / "src" / "main.cpp").write_text(src, encoding="utf-8")
            logger.info(f"Temporary project created at: {project_path}")

        # Build the project
        build_cmd = ["pio", "run", "-d", str(project_path), "-e", board]
        logger.info("BUILD: %s", " ".join(build_cmd))
        subprocess.check_output(build_cmd, stderr=subprocess.STDOUT)

        # Upload using PlatformIO's built-in upload target
        upload_cmd = [
            "pio", "run", "-d", str(project_path),
            "-e", board, "-t", "upload",
            "--upload-port", port
        ]
        logger.info("UPLOAD: %s", " ".join(upload_cmd))
        subprocess.check_call(upload_cmd)

        return [TextContent(type="text", text="✅ Build & Upload completed!")]

    except subprocess.CalledProcessError as e:
        return [TextContent(type="text", text=f"❌ Build or Upload Error:\n{e.output.decode(errors='ignore')}")]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ Unexpected error: {str(e)}")]

# ---------------------------------------------------------------------------
# 3) Start Server
# ---------------------------------------------------------------------------

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (reader, writer):
        await app.run(reader, writer, app.create_initialization_options())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
