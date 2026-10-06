from __future__ import annotations

import socket
from typing import Optional, List, Tuple

import paramiko


class AgentNotAvailableError(Exception):
    pass


class ConnectionError(Exception):
    pass


class SFTPConnection:
    def __init__(self, profile) -> None:
        self.profile = profile
        self._ssh: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None

    # ------------------------------------------------------------------
    def connect(self) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        kwargs: dict = {
            "hostname": self.profile.host,
            "port": self.profile.port,
            "username": self.profile.user,
            "timeout": 15,
            "allow_agent": False,
            "look_for_keys": False,
        }

        if self.profile.auth == "agent":
            agent = paramiko.Agent()
            keys = agent.get_keys()
            if not keys:
                raise AgentNotAvailableError(
                    "SSH agent has no keys loaded. Run: ssh-add ~/.ssh/id_ed25519"
                )
            kwargs["pkey"] = keys[0]

        elif self.profile.auth == "key_file":
            if not self.profile.key_file:
                raise ConnectionError("Key file path is not set in profile.")
            kwargs["key_filename"] = self.profile.key_file

        elif self.profile.auth == "password":
            kwargs.pop("allow_agent")
            kwargs.pop("look_for_keys")
            # password will be handled interactively — caller must set
            # kwargs["password"] before connecting if non-interactive
            raise ConnectionError(
                "Password auth: set profile.password before connecting."
            )

        client.connect(**kwargs)
        self._ssh = client
        self._sftp = client.open_sftp()

    def connect_with_password(self, password: str) -> None:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.profile.host,
            port=self.profile.port,
            username=self.profile.user,
            password=password,
            timeout=15,
        )
        self._ssh = client
        self._sftp = client.open_sftp()

    # ------------------------------------------------------------------
    def disconnect(self) -> None:
        try:
            if self._sftp:
                self._sftp.close()
            if self._ssh:
                self._ssh.close()
        except Exception:
            pass
        finally:
            self._sftp = None
            self._ssh = None

    def is_connected(self) -> bool:
        transport = self._ssh.get_transport() if self._ssh else None
        return transport is not None and transport.is_active()

    # ------------------------------------------------------------------
    @property
    def sftp(self) -> paramiko.SFTPClient:
        if not self._sftp:
            raise ConnectionError("Not connected.")
        return self._sftp

    def exec(self, cmd: str) -> Tuple[str, str]:
        if not self._ssh:
            raise ConnectionError("Not connected.")
        _, stdout, stderr = self._ssh.exec_command(cmd)
        return stdout.read().decode(errors="replace"), stderr.read().decode(errors="replace")


# ---------------------------------------------------------------------------

def get_agent_keys() -> List[dict]:
    """Returns info about keys loaded in the SSH agent."""
    try:
        agent = paramiko.Agent()
        result = []
        for key in agent.get_keys():
            fp_bytes = key.get_fingerprint()
            fp_hex = ":".join(f"{b:02x}" for b in fp_bytes)
            result.append(
                {
                    "type": key.get_name(),
                    "fingerprint": fp_hex,
                    "bits": getattr(key, "get_bits", lambda: 0)(),
                    "comment": getattr(key, "comment", ""),
                }
            )
        return result
    except Exception:
        return []
