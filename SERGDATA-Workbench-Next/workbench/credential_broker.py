"""Secret broker: plaintext exists only in process memory or the caller's input buffer.
Persistent secrets are protected with Windows DPAPI (CurrentUser scope).
"""
from __future__ import annotations
import base64
import ctypes
import json
import os
import secrets
import threading
from pathlib import Path
from ctypes import wintypes


class CredentialError(RuntimeError):
    pass


class DPAPIProtector:
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [('cbData', wintypes.DWORD), ('pbData', ctypes.POINTER(ctypes.c_byte))]

    def __init__(self):
        if os.name != 'nt':
            raise CredentialError('Постоянное хранилище секретов доступно только через Windows DPAPI')
        self.crypt32 = ctypes.WinDLL('crypt32', use_last_error=True)
        self.kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        blob_ptr = ctypes.POINTER(self.DATA_BLOB)
        self.crypt32.CryptProtectData.argtypes = [blob_ptr, wintypes.LPCWSTR, blob_ptr,
                                                   ctypes.c_void_p, ctypes.c_void_p,
                                                   wintypes.DWORD, blob_ptr]
        self.crypt32.CryptProtectData.restype = wintypes.BOOL
        self.crypt32.CryptUnprotectData.argtypes = [blob_ptr, ctypes.POINTER(wintypes.LPWSTR),
                                                     blob_ptr, ctypes.c_void_p, ctypes.c_void_p,
                                                     wintypes.DWORD, blob_ptr]
        self.crypt32.CryptUnprotectData.restype = wintypes.BOOL
        self.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        self.kernel32.LocalFree.restype = ctypes.c_void_p

    @staticmethod
    def _blob(data: bytes):
        buf = ctypes.create_string_buffer(data, len(data))
        blob = DPAPIProtector.DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte)))
        return blob, buf

    def protect(self, plaintext: bytes) -> bytes:
        source, keepalive = self._blob(plaintext)
        target = self.DATA_BLOB()
        ok = self.crypt32.CryptProtectData(ctypes.byref(source), ctypes.c_wchar_p('SERGDATA Workbench credential'), None, None, None, 1, ctypes.byref(target))
        if not ok:
            raise CredentialError('Windows DPAPI не смог защитить секрет')
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            self.kernel32.LocalFree(target.pbData)

    def unprotect(self, ciphertext: bytes) -> bytes:
        source, keepalive = self._blob(ciphertext)
        target = self.DATA_BLOB()
        ok = self.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target))
        if not ok:
            raise CredentialError('Windows DPAPI не смог расшифровать секрет текущего пользователя')
        try:
            return ctypes.string_at(target.pbData, target.cbData)
        finally:
            self.kernel32.LocalFree(target.pbData)


class CredentialBroker:
    def __init__(self, path: Path, protector=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._memory: dict[str, str] = {}
        self._protector = protector
        self._persistent: dict[str, str] = {}
        if self._protector is None and os.name == 'nt':
            self._protector = DPAPIProtector()
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text('utf-8'))
            if data.get('version') != 1 or not isinstance(data.get('items'), dict):
                raise ValueError('unsupported credential store format')
            self._persistent = {str(k): str(v) for k, v in data['items'].items()}
        except Exception as exc:
            raise CredentialError(f'Не удалось открыть защищённое хранилище секретов: {type(exc).__name__}') from exc

    @property
    def persistence_available(self) -> bool:
        return self._protector is not None

    def _save(self):
        payload = json.dumps({'version': 1, 'items': self._persistent}, separators=(',', ':'))
        tmp = self.path.with_suffix(self.path.suffix + '.tmp')
        tmp.write_text(payload, encoding='utf-8')
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        os.replace(tmp, self.path)

    def put(self, value: str, persist: bool = False) -> str:
        value = str(value or '')
        if not value:
            raise CredentialError('Пустой секрет не принимается')
        if len(value.encode('utf-8')) > 16384:
            raise CredentialError('Секрет превышает лимит 16 КБ')
        if persist and not self.persistence_available:
            raise CredentialError('На этой ОС нельзя безопасно сохранить секрет постоянно; отключи сохранение и используй временный режим')
        ref = 'cred_' + secrets.token_urlsafe(24)
        with self._lock:
            if len(set(self._memory) | set(self._persistent)) >= 256:
                raise CredentialError('Достигнут лимит 256 сохранённых/временных секретов. Удали ненужные SSH-профили.')
            self._memory[ref] = value
            if persist:
                try:
                    encrypted = self._protector.protect(value.encode('utf-8'))
                    self._persistent[ref] = base64.b64encode(encrypted).decode('ascii')
                    self._save()
                except Exception:
                    self._persistent.pop(ref, None)
                    self._memory.pop(ref, None)
                    raise
        return ref

    def resolve(self, ref: str) -> str:
        ref = str(ref or '')
        if not ref.startswith('cred_') or len(ref) > 128:
            raise CredentialError('Некорректная ссылка на учётные данные')
        with self._lock:
            if ref in self._memory:
                return self._memory[ref]
            encoded = self._persistent.get(ref)
            if not encoded or not self._protector:
                raise CredentialError('Секрет отсутствует в хранилище или временный секрет потерян после перезапуска Workbench')
            try:
                value = self._protector.unprotect(base64.b64decode(encoded, validate=True)).decode('utf-8')
            except Exception as exc:
                raise CredentialError(f'Не удалось получить секрет: {type(exc).__name__}') from exc
            self._memory[ref] = value
            return value

    def delete(self, ref: str) -> bool:
        with self._lock:
            existed = self._memory.pop(ref, None) is not None
            if ref in self._persistent:
                del self._persistent[ref]
                self._save()
                existed = True
            return existed

    def exists(self, ref: str) -> bool:
        with self._lock:
            if ref in self._memory:
                return True
            if self._protector is None or ref not in self._persistent:
                return False
            try:
                self.resolve(ref)
                return True
            except CredentialError:
                return False

    def status(self, ref: str) -> str:
        """Return availability without exposing the secret or its encrypted payload."""
        ref = str(ref or '')
        with self._lock:
            in_memory = ref in self._memory
            encoded = self._persistent.get(ref)
            if encoded and self._protector is not None:
                try:
                    wrapped = base64.b64decode(encoded, validate=True)
                    self._protector.unprotect(wrapped)
                    return 'persistent'
                except Exception:
                    return 'session' if in_memory else 'missing'
            return 'session' if in_memory else 'missing'

    def prune(self, used_refs: set[str]):
        used = {str(x) for x in used_refs if x}
        with self._lock:
            for ref in list(self._memory):
                if ref not in used:
                    self._memory.pop(ref, None)
            removed = False
            for ref in list(self._persistent):
                if ref not in used:
                    self._persistent.pop(ref, None)
                    removed = True
            if removed:
                self._save()

    def close(self):
        with self._lock:
            self._memory.clear()
