"""
Native reimplementation of i3status's `volume` module.

Outputs the volume of the specified mixer on the specified device.

Configuration parameters:
    cache_timeout: refresh interval for this module (default None)
    device: 'default' tries PulseAudio first, falling back to ALSA;
        'pulse', 'pulse:N' (sink index) or 'pulse:name' (sink name)
        force PulseAudio; anything else is used as an ALSA device name
        (default 'default')
    format: see placeholders below (default '♪: %volume')
    format_muted: format used when muted (default '♪: 0%%')
    mixer: ALSA mixer control name, ignored for PulseAudio
        (default 'Master')
    mixer_idx: ALSA mixer control index, ignored for PulseAudio
        (default 0)

Format placeholders:
    %volume the volume percentage, 0-100 (PulseAudio volumes can
        exceed 100%; this is clamped at 0 but not at the top end)
    %devicename the mixer element's name (ALSA) or sink description
        (PulseAudio)
    %% a literal percent sign

Color options:
    color_degraded: muted

Type: Instance (supports multiple sections via an instance/title)

Notes:
    Talks to ALSA's mixer API directly via ctypes bindings to
    libasound, and to PulseAudio's native client API directly via
    ctypes bindings to libpulse (no subprocess, no amixer/pactl). Opens
    a fresh connection on every call, unlike real i3status's
    persistent, subscription-based PulseAudio connection - trades its
    stale-until-next-event read for an always-current one.

    Struct layouts (pa_sink_info, pa_cvolume, pa_channel_map, etc.)
    were ported from real i3status's src/pulse.c and src/print_volume.c
    against PulseAudio's stable public ABI (ctypes.CDLL has no header,
    so these are handwritten to match).

    Device dispatch matches real i3status's print_volume.c exactly:
    'pulse'/'pulse:N'/'pulse:name' always use PulseAudio with no ALSA
    fallback (an unreachable sink renders as %volume=0, unmuted,
    through the normal format). 'default' tries PulseAudio first and
    falls back to ALSA. Any other string goes straight to ALSA.

    Verified against a real PipeWire system: matched `pactl
    get-sink-volume`/`get-sink-mute` exactly via device='default' and
    the underlying ALSA device directly.

    ALSA volume mapping: logarithmic if the mixer has a usable dB range
    above 24 dB, linear otherwise (or if dB info isn't available at
    all) - matching i3status's ALSA_VOLUME macro. PulseAudio volumes
    are averaged across channels via pa_cvolume_avg(), matching real
    i3status exactly.

@author claude
"""

import ctypes
from time import monotonic

from py3status.i3status.helpers import format_placeholders, resolve_cache_timeout

MAX_LINEAR_DB_SCALE = 24
SND_CTL_TLV_DB_GAIN_MUTE = -9999999

PA_CHANNELS_MAX = 32
PA_CONTEXT_READY = 4
PA_CONTEXT_FAILED = 5
PA_CONTEXT_TERMINATED = 6
PA_CONTEXT_NOAUTOSPAWN = 0x0001
PA_CONTEXT_NOFAIL = 0x0002
PA_OPERATION_RUNNING = 0
PA_VOLUME_NORM = 65536


class _PaSampleSpec(ctypes.Structure):
    _fields_ = [
        ("format", ctypes.c_int),
        ("rate", ctypes.c_uint32),
        ("channels", ctypes.c_uint8),
    ]


class _PaChannelMap(ctypes.Structure):
    _fields_ = [
        ("channels", ctypes.c_uint8),
        ("map", ctypes.c_int * PA_CHANNELS_MAX),
    ]


class _PaCVolume(ctypes.Structure):
    _fields_ = [
        ("channels", ctypes.c_uint8),
        ("values", ctypes.c_uint32 * PA_CHANNELS_MAX),
    ]


class _PaSinkPortInfo(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("description", ctypes.c_char_p),
        ("priority", ctypes.c_uint32),
        ("available", ctypes.c_int),
    ]


class _PaSinkInfo(ctypes.Structure):
    _fields_ = [
        ("name", ctypes.c_char_p),
        ("index", ctypes.c_uint32),
        ("description", ctypes.c_char_p),
        ("sample_spec", _PaSampleSpec),
        ("channel_map", _PaChannelMap),
        ("owner_module", ctypes.c_uint32),
        ("volume", _PaCVolume),
        ("mute", ctypes.c_int),
        ("monitor_source", ctypes.c_uint32),
        ("monitor_source_name", ctypes.c_char_p),
        ("latency", ctypes.c_uint64),
        ("driver", ctypes.c_char_p),
        ("flags", ctypes.c_int),
        ("proplist", ctypes.c_void_p),
        ("configured_latency", ctypes.c_uint64),
        ("base_volume", ctypes.c_uint32),
        ("state", ctypes.c_int),
        ("n_volume_steps", ctypes.c_uint32),
        ("card", ctypes.c_uint32),
        ("n_ports", ctypes.c_uint32),
        ("ports", ctypes.POINTER(ctypes.POINTER(_PaSinkPortInfo))),
        ("active_port", ctypes.POINTER(_PaSinkPortInfo)),
        ("n_formats", ctypes.c_uint8),
        ("formats", ctypes.c_void_p),
    ]


_PA_SINK_INFO_CB = ctypes.CFUNCTYPE(
    None, ctypes.c_void_p, ctypes.POINTER(_PaSinkInfo), ctypes.c_int, ctypes.c_void_p
)


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = None
    device = "default"
    format = "♪: %volume"
    format_muted = "♪: 0%%"
    mixer = "Master"
    mixer_idx = 0

    def post_config_hook(self):
        self.cache_timeout = resolve_cache_timeout(self.py3, self.cache_timeout)

        self._lib = None
        self._pulse_unavailable = False
        self._pulse_lib = None
        self._force_pulse, self._sink_index, self._sink_name = self._parse_pulse_device(self.device)
        self._device_is_default = self.device.lower() == "default"
        if self._force_pulse:
            if self._sink_index is not None:
                target = f"sink index {self._sink_index}"
            elif self._sink_name:
                target = f"sink '{self._sink_name}'"
            else:
                target = "the default sink"
            self.py3.log(f"volume: device='{self.device}' -> PulseAudio only ({target})", "debug")
        elif self._device_is_default:
            self.py3.log(
                f"volume: device='{self.device}' -> PulseAudio first, ALSA fallback", "debug"
            )
        else:
            self.py3.log(f"volume: device='{self.device}' -> ALSA only", "debug")

    def _get_lib(self):
        if self._lib is None:
            lib = ctypes.CDLL("libasound.so.2")

            lib.snd_strerror.restype = ctypes.c_char_p
            lib.snd_strerror.argtypes = [ctypes.c_int]

            lib.snd_mixer_open.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_int]
            lib.snd_mixer_attach.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.snd_mixer_selem_register.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
            ]
            lib.snd_mixer_load.argtypes = [ctypes.c_void_p]
            lib.snd_mixer_close.argtypes = [ctypes.c_void_p]
            lib.snd_mixer_handle_events.argtypes = [ctypes.c_void_p]

            lib.snd_mixer_selem_id_malloc.argtypes = [ctypes.POINTER(ctypes.c_void_p)]
            lib.snd_mixer_selem_id_free.argtypes = [ctypes.c_void_p]
            lib.snd_mixer_selem_id_set_index.argtypes = [ctypes.c_void_p, ctypes.c_uint]
            lib.snd_mixer_selem_id_set_name.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

            lib.snd_mixer_find_selem.restype = ctypes.c_void_p
            lib.snd_mixer_find_selem.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

            long_p = ctypes.POINTER(ctypes.c_long)
            lib.snd_mixer_selem_get_playback_dB_range.argtypes = [ctypes.c_void_p, long_p, long_p]
            lib.snd_mixer_selem_get_playback_dB.argtypes = [ctypes.c_void_p, ctypes.c_int, long_p]
            lib.snd_mixer_selem_get_capture_dB_range.argtypes = [ctypes.c_void_p, long_p, long_p]
            lib.snd_mixer_selem_get_capture_dB.argtypes = [ctypes.c_void_p, ctypes.c_int, long_p]
            lib.snd_mixer_selem_get_playback_volume_range.argtypes = [
                ctypes.c_void_p,
                long_p,
                long_p,
            ]
            lib.snd_mixer_selem_get_playback_volume.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                long_p,
            ]
            lib.snd_mixer_selem_get_capture_volume_range.argtypes = [
                ctypes.c_void_p,
                long_p,
                long_p,
            ]
            lib.snd_mixer_selem_get_capture_volume.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                long_p,
            ]

            lib.snd_mixer_selem_has_playback_switch.argtypes = [ctypes.c_void_p]
            lib.snd_mixer_selem_has_capture_switch.argtypes = [ctypes.c_void_p]
            int_p = ctypes.POINTER(ctypes.c_int)
            lib.snd_mixer_selem_get_playback_switch.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                int_p,
            ]
            lib.snd_mixer_selem_get_capture_switch.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                int_p,
            ]

            lib.snd_mixer_selem_get_name.restype = ctypes.c_char_p
            lib.snd_mixer_selem_get_name.argtypes = [ctypes.c_void_p]

            self._lib = lib
        return self._lib

    def _read_volume(self, device, mixer, mixer_idx):
        """
        Return (percent, muted, devicename), or None if the mixer couldn't
        be read at all.
        """
        lib = self._get_lib()
        capture = mixer.lower().startswith("capture")

        mixer_handle = ctypes.c_void_p()
        if lib.snd_mixer_open(ctypes.byref(mixer_handle), 0) < 0:
            return None
        try:
            if lib.snd_mixer_attach(mixer_handle, device.encode()) < 0:
                return None
            if lib.snd_mixer_selem_register(mixer_handle, None, None) < 0:
                return None
            if lib.snd_mixer_load(mixer_handle) < 0:
                return None

            sid = ctypes.c_void_p()
            lib.snd_mixer_selem_id_malloc(ctypes.byref(sid))
            try:
                lib.snd_mixer_selem_id_set_index(sid, mixer_idx)
                lib.snd_mixer_selem_id_set_name(sid, mixer.encode())
                elem = lib.snd_mixer_find_selem(mixer_handle, sid)
                if not elem:
                    return None

                lib.snd_mixer_handle_events(mixer_handle)

                force_linear = False
                min_val = ctypes.c_long()
                max_val = ctypes.c_long()
                val = ctypes.c_long()

                get_db_range = (
                    lib.snd_mixer_selem_get_capture_dB_range
                    if capture
                    else lib.snd_mixer_selem_get_playback_dB_range
                )
                get_db = (
                    lib.snd_mixer_selem_get_capture_dB
                    if capture
                    else lib.snd_mixer_selem_get_playback_dB
                )
                err = get_db_range(elem, ctypes.byref(min_val), ctypes.byref(max_val))
                if err == 0:
                    err = get_db(elem, 0, ctypes.byref(val))

                if err != 0 or min_val.value >= max_val.value:
                    get_vol_range = (
                        lib.snd_mixer_selem_get_capture_volume_range
                        if capture
                        else lib.snd_mixer_selem_get_playback_volume_range
                    )
                    get_vol = (
                        lib.snd_mixer_selem_get_capture_volume
                        if capture
                        else lib.snd_mixer_selem_get_playback_volume
                    )
                    err = get_vol_range(elem, ctypes.byref(min_val), ctypes.byref(max_val))
                    if err == 0:
                        err = get_vol(elem, 0, ctypes.byref(val))
                    force_linear = True

                if err != 0:
                    return None

                min_v, max_v, cur_v = min_val.value, max_val.value, val.value

                if force_linear or (max_v - min_v) <= MAX_LINEAR_DB_SCALE * 100:
                    avgf = ((cur_v - min_v) / (max_v - min_v)) * 100
                    avg = int(avgf) if avgf - int(avgf) < 0.5 else int(avgf) + 1
                else:
                    normalized = 10 ** ((cur_v - max_v) / 6000.0)
                    if min_v != SND_CTL_TLV_DB_GAIN_MUTE:
                        min_norm = 10 ** ((min_v - max_v) / 6000.0)
                        normalized = (normalized - min_norm) / (1 - min_norm)
                    avg = round(normalized * 100)

                muted = False
                pbval = ctypes.c_int(1)
                if lib.snd_mixer_selem_has_playback_switch(elem):
                    lib.snd_mixer_selem_get_playback_switch(elem, 0, ctypes.byref(pbval))
                    muted = not pbval.value
                elif lib.snd_mixer_selem_has_capture_switch(elem):
                    lib.snd_mixer_selem_get_capture_switch(elem, 0, ctypes.byref(pbval))
                    muted = not pbval.value

                name = lib.snd_mixer_selem_get_name(elem)
                devicename = name.decode(errors="replace") if name else ""

                return avg, muted, devicename
            finally:
                lib.snd_mixer_selem_id_free(sid)
        finally:
            lib.snd_mixer_close(mixer_handle)

    def _get_pulse_lib(self):
        if self._pulse_unavailable:
            return None
        if self._pulse_lib is None:
            try:
                lib = ctypes.CDLL("libpulse.so.0")
            except OSError:
                self._pulse_unavailable = True
                return None

            lib.pa_mainloop_new.restype = ctypes.c_void_p
            lib.pa_mainloop_get_api.restype = ctypes.c_void_p
            lib.pa_mainloop_get_api.argtypes = [ctypes.c_void_p]
            lib.pa_mainloop_iterate.argtypes = [
                ctypes.c_void_p,
                ctypes.c_int,
                ctypes.POINTER(ctypes.c_int),
            ]
            lib.pa_mainloop_free.argtypes = [ctypes.c_void_p]

            lib.pa_context_new.restype = ctypes.c_void_p
            lib.pa_context_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.pa_context_connect.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_void_p,
            ]
            lib.pa_context_get_state.restype = ctypes.c_int
            lib.pa_context_get_state.argtypes = [ctypes.c_void_p]
            lib.pa_context_disconnect.argtypes = [ctypes.c_void_p]
            lib.pa_context_unref.argtypes = [ctypes.c_void_p]

            lib.pa_context_get_sink_info_by_name.restype = ctypes.c_void_p
            lib.pa_context_get_sink_info_by_name.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                _PA_SINK_INFO_CB,
                ctypes.c_void_p,
            ]
            lib.pa_context_get_sink_info_by_index.restype = ctypes.c_void_p
            lib.pa_context_get_sink_info_by_index.argtypes = [
                ctypes.c_void_p,
                ctypes.c_uint32,
                _PA_SINK_INFO_CB,
                ctypes.c_void_p,
            ]
            lib.pa_operation_get_state.restype = ctypes.c_int
            lib.pa_operation_get_state.argtypes = [ctypes.c_void_p]
            lib.pa_operation_unref.argtypes = [ctypes.c_void_p]

            lib.pa_cvolume_avg.restype = ctypes.c_uint32
            lib.pa_cvolume_avg.argtypes = [ctypes.POINTER(_PaCVolume)]

            self._pulse_lib = lib
        return self._pulse_lib

    @staticmethod
    def _parse_pulse_device(device):
        """
        Match real i3status's device dispatch (print_volume.c): returns
        (force_pulse, sink_index, sink_name). force_pulse=True means always
        use PulseAudio, with no ALSA fallback on failure. sink_index and
        sink_name are mutually exclusive; both None means "the default
        sink" (@DEFAULT_SINK@).
        """
        if not device.lower().startswith("pulse"):
            return False, None, None
        rest = device[len("pulse") :]
        if rest.startswith(":"):
            suffix = rest[1:]
            if suffix[:1].isdigit():
                return True, int(suffix), None
            return True, None, suffix
        return True, None, None

    def _read_pulse_sink(self, sink_index, sink_name, timeout=2.0):
        """
        Return (percent, muted, description) for the given PulseAudio sink
        (by index or by name - mutually exclusive; both None means the
        default sink, @DEFAULT_SINK@), or None if PulseAudio can't be
        reached or the sink can't be found.
        """
        lib = self._get_pulse_lib()
        if lib is None:
            return None

        mainloop = lib.pa_mainloop_new()
        if not mainloop:
            return None
        try:
            api = lib.pa_mainloop_get_api(mainloop)
            context = lib.pa_context_new(api, b"py3status")
            if not context:
                return None
            try:
                flags = PA_CONTEXT_NOAUTOSPAWN | PA_CONTEXT_NOFAIL
                if lib.pa_context_connect(context, None, flags, None) < 0:
                    return None

                deadline = monotonic() + timeout
                state = lib.pa_context_get_state(context)
                while state not in (PA_CONTEXT_READY, PA_CONTEXT_FAILED, PA_CONTEXT_TERMINATED):
                    if lib.pa_mainloop_iterate(mainloop, 1, None) < 0:
                        return None
                    if monotonic() > deadline:
                        return None
                    state = lib.pa_context_get_state(context)
                if state != PA_CONTEXT_READY:
                    return None

                result = {}

                def _callback(c, info_ptr, eol, userdata):
                    if eol or not info_ptr:
                        return
                    info = info_ptr.contents
                    avg = lib.pa_cvolume_avg(ctypes.byref(info.volume))
                    result["volume"] = round(avg * 100 / PA_VOLUME_NORM)
                    result["muted"] = bool(info.mute)
                    if info.active_port and info.active_port.contents.description:
                        result["description"] = info.active_port.contents.description.decode(
                            errors="replace"
                        )
                    elif info.description:
                        result["description"] = info.description.decode(errors="replace")
                    else:
                        result["description"] = ""

                callback = _PA_SINK_INFO_CB(_callback)

                if sink_name is not None:
                    op = lib.pa_context_get_sink_info_by_name(
                        context, sink_name.encode(), callback, None
                    )
                elif sink_index is not None:
                    op = lib.pa_context_get_sink_info_by_index(context, sink_index, callback, None)
                else:
                    op = lib.pa_context_get_sink_info_by_name(
                        context, b"@DEFAULT_SINK@", callback, None
                    )

                if not op:
                    return None
                try:
                    deadline = monotonic() + timeout
                    op_state = lib.pa_operation_get_state(op)
                    while op_state == PA_OPERATION_RUNNING:
                        if lib.pa_mainloop_iterate(mainloop, 1, None) < 0:
                            break
                        if monotonic() > deadline:
                            break
                        op_state = lib.pa_operation_get_state(op)
                finally:
                    lib.pa_operation_unref(op)

                if "volume" not in result:
                    return None
                return result["volume"], result["muted"], result["description"]
            finally:
                lib.pa_context_disconnect(context)
                lib.pa_context_unref(context)
        finally:
            lib.pa_mainloop_free(mainloop)

    def volume(self):
        pulse_result = None
        if self._force_pulse:
            pulse_result = self._read_pulse_sink(self._sink_index, self._sink_name)
        elif self._device_is_default:
            pulse_result = self._read_pulse_sink(None, None)

        if pulse_result is not None:
            volume, muted, devicename = pulse_result
            volume = max(volume, 0)
        elif self._force_pulse:
            # matches real i3status: a forced "pulse..." device that can't
            # be reached renders as 0%, unmuted, through the normal format
            # - not the empty-string bypass ALSA failures use below
            volume, muted, devicename = 0, False, ""
        else:
            try:
                alsa_result = self._read_volume(self.device, self.mixer, self.mixer_idx)
            except OSError:
                alsa_result = None
            if alsa_result is None:
                # matches i3status: a mixer-open/attach/find failure
                # outputs a genuinely empty string, bypassing format
                # entirely - not "0%" rendered through the user's format
                return {"cached_until": self.py3.time_in(self.cache_timeout), "full_text": ""}
            volume, muted, devicename = alsa_result
            volume = max(volume, 0)

        selected_format = self.format_muted if muted else self.format
        color = self.py3.COLOR_DEGRADED if muted else None

        placeholders = [
            ("%%", "%"),
            ("%volume", f"{volume}%"),
            ("%devicename", devicename),
        ]
        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": format_placeholders(selected_format, placeholders),
        }
        if color:
            response["color"] = color
        return response


if __name__ == "__main__":
    from py3status.module_test import module_test

    module_test(Py3status)
