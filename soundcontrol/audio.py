"""Windows audio device access built on pycaw (Core Audio APIs)."""

from __future__ import annotations

from _ctypes import COMError
from dataclasses import dataclass

from pycaw.constants import DEVICE_STATE, EDataFlow, ERole
from pycaw.utils import AudioUtilities


@dataclass
class Device:
    id: str
    name: str
    is_capture: bool
    is_default: bool
    _dev: object

    @property
    def volume(self) -> float:
        """Current volume as a 0-100 integer."""
        return round(self._dev.EndpointVolume.GetMasterVolumeLevelScalar() * 100)

    @volume.setter
    def volume(self, value: float) -> None:
        value = max(0, min(100, value))
        self._dev.EndpointVolume.SetMasterVolumeLevelScalar(value / 100, None)

    @property
    def muted(self) -> bool:
        return bool(self._dev.EndpointVolume.GetMute())

    @muted.setter
    def muted(self, value: bool) -> None:
        self._dev.EndpointVolume.SetMute(bool(value), None)

    def set_as_default(self) -> None:
        """Make this device the default for console, multimedia and communications."""
        AudioUtilities.SetDefaultDevice(
            self.id, roles=[ERole.eConsole, ERole.eMultimedia, ERole.eCommunications]
        )


def _default_ids() -> set[str]:
    ids = set()
    enumerator = AudioUtilities.GetDeviceEnumerator()
    for flow in (EDataFlow.eRender, EDataFlow.eCapture):
        for role in (ERole.eConsole, ERole.eMultimedia, ERole.eCommunications):
            try:
                endpoint = enumerator.GetDefaultAudioEndpoint(flow.value, role.value)
            except COMError:
                continue
            # Avoid AudioUtilities.CreateDevice here: it walks the full property
            # store, which is slow right after switching the default device.
            ids.add(endpoint.GetId())
    return ids


def list_devices() -> list[Device]:
    """List all active playback (render) and recording (capture) devices."""
    defaults = _default_ids()
    devices: list[Device] = []
    for flow, is_capture in ((EDataFlow.eRender, False), (EDataFlow.eCapture, True)):
        raw_devices = AudioUtilities.GetAllDevices(
            data_flow=flow.value, device_state=DEVICE_STATE.ACTIVE.value
        )
        for dev in raw_devices:
            devices.append(
                Device(
                    id=dev.id,
                    name=dev.FriendlyName or dev.id,
                    is_capture=is_capture,
                    is_default=dev.id in defaults,
                    _dev=dev,
                )
            )
    return devices


def default_microphone() -> Device | None:
    for device in list_devices():
        if device.is_capture and device.is_default:
            return device
    return None


def default_playback() -> Device | None:
    for device in list_devices():
        if not device.is_capture and device.is_default:
            return device
    return None
