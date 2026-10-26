import ctypes
import json
import os
from ctypes import wintypes


TARGET = "AX-Navigator/OpenAI"


class WindowsCredentialStore:
    @property
    def supported(self):
        return os.name == "nt"

    def _api(self):
        class Credential(ctypes.Structure):
            _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                        ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
                        ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                        ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]

        library = ctypes.WinDLL("advapi32", use_last_error=True)
        library.CredWriteW.argtypes = [ctypes.POINTER(Credential), wintypes.DWORD]
        library.CredWriteW.restype = wintypes.BOOL
        library.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(Credential))]
        library.CredReadW.restype = wintypes.BOOL
        library.CredFree.argtypes = [ctypes.c_void_p]
        library.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        library.CredDeleteW.restype = wintypes.BOOL
        return library, Credential

    def read(self):
        if not self.supported:
            return None
        library, credential_type = self._api()
        pointer = ctypes.POINTER(credential_type)()
        if not library.CredReadW(TARGET, 1, 0, ctypes.byref(pointer)):
            if ctypes.get_last_error() == 1168:
                return None
            raise RuntimeError("Windows credential read failed")
        try:
            raw = ctypes.string_at(pointer.contents.CredentialBlob, pointer.contents.CredentialBlobSize)
            return json.loads(raw.decode("utf-8"))
        finally:
            library.CredFree(pointer)

    def save(self, api_key, model):
        if not self.supported:
            raise RuntimeError("Windows credential storage unavailable")
        library, credential_type = self._api()
        raw = json.dumps({"api_key": api_key, "model": model}).encode("utf-8")
        buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        credential = credential_type(Type=1, TargetName=TARGET, Comment="AX Navigator OpenAI connection",
                                     CredentialBlobSize=len(raw), CredentialBlob=buffer, Persist=2, UserName="OpenAI")
        if not library.CredWriteW(ctypes.byref(credential), 0):
            raise RuntimeError("Windows credential write failed")

    def delete(self):
        if not self.supported:
            return
        library, credential_type = self._api()
        if not library.CredDeleteW(TARGET, 1, 0) and ctypes.get_last_error() != 1168:
            raise RuntimeError("Windows credential delete failed")
