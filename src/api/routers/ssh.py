import asyncio
import json
import paramiko
import traceback
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class SSH:
    def __init__(self, websocket: WebSocket, host, port, username, password):
        self.websocket = websocket
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Try to connect with more detailed error handling
        try:
            self.ssh.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
                allow_agent=False,  # Don't use SSH agent
                look_for_keys=False,  # Don't look for SSH keys, use password only
                banner_timeout=10,
            )
        except paramiko.AuthenticationException as e:
            raise Exception(f"Authentication failed: {str(e)}")
        except paramiko.SSHException as e:
            raise Exception(f"SSH error: {str(e)}")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

        self.channel = self.ssh.get_transport().open_session()
        self.channel.get_pty(term="xterm", width=80, height=24)
        self.channel.invoke_shell()
        self.channel.settimeout(0.0)  # Non-blocking

    async def read_data(self):
        """Continuously read data from SSH channel and send to WebSocket"""
        try:
            while True:
                if self.channel.recv_ready():
                    data = self.channel.recv(4096)
                    if not data:
                        break
                    await self.websocket.send_bytes(data)

                # Check if channel is still open
                if self.channel.closed:
                    await self.websocket.send_text(
                        json.dumps(
                            {"type": "error", "data": "SSH channel closed"})
                    )
                    break

                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error reading SSH data: {e}")
            traceback.print_exc()
            try:
                await self.websocket.send_text(
                    json.dumps(
                        {"type": "error", "data": f"Read error: {str(e)}"})
                )
            except:
                pass

    async def write_data(self, data):
        """Write data to SSH channel"""
        try:
            if self.channel.send_ready():
                self.channel.send(data)
        except Exception as e:
            print(f"Error writing SSH data: {e}")
            await self.websocket.send_text(
                json.dumps({"type": "error", "data": f"Write error: {str(e)}"})
            )

    def close(self):
        """Close SSH connection"""
        try:
            if self.channel:
                self.channel.close()
            if self.ssh:
                self.ssh.close()
        except Exception as e:
            print(f"Error closing SSH connection: {e}")


@router.websocket("/ws/ssh")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ssh_connection = None
    read_task = None

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "connect":
                details = message["data"]
                try:
                    print(
                        f"Attempting SSH connection to {details['username']}@{details['host']}:{details['port']}"
                    )

                    ssh_connection = SSH(
                        websocket,
                        details["host"],
                        details["port"],
                        details["username"],
                        details["password"],
                    )

                    # Start reading task
                    read_task = asyncio.create_task(ssh_connection.read_data())

                    print(f"SSH connection successful to {details['host']}")
                    await websocket.send_text(
                        json.dumps(
                            {"type": "connected", "data": "Successfully connected"}
                        )
                    )

                except Exception as e:
                    error_msg = f"Connection failed: {str(e)}"
                    print(f"SSH connection failed: {error_msg}")
                    traceback.print_exc()
                    await websocket.send_text(
                        json.dumps({"type": "error", "data": error_msg})
                    )

            elif message["type"] == "data" and ssh_connection:
                await ssh_connection.write_data(message["data"])

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        if read_task:
            read_task.cancel()
            try:
                await read_task
            except asyncio.CancelledError:
                pass
        if ssh_connection:
            ssh_connection.close()
            print("SSH connection closed")
