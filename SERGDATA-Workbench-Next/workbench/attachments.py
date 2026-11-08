"""Safe text extraction for Workbench uploads. Uploaded files are stored, never executed."""
from __future__ import annotations
import io
import re
import zipfile
from pathlib import PurePosixPath
from typing import Iterable
from .security import is_sensitive_path

TEXT_EXTENSIONS = {
    '.txt', '.md', '.rst', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.py', '.pyw', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.html', '.htm',
    '.css', '.scss', '.sass', '.sql', '.sh', '.bash', '.ps1', '.bat', '.cmd',
    '.xml', '.csv', '.log', '.diff', '.patch', '.gitignore', '.dockerfile',
    '.go', '.rs', '.java', '.kt', '.c', '.h', '.cpp', '.hpp', '.cs', '.php',
    '.rb', '.lua', '.conf', '.service', '.properties', '.env.example'
}
BLOCKED_NAMES = {'.env', 'id_rsa', 'id_ed25519', 'credentials', 'secrets.json', '.npmrc', '.pypirc', '.netrc', '.git-credentials'}
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 300
MAX_ARCHIVE_TOTAL = 80 * 1024 * 1024
MAX_ARCHIVE_MEMBER = 2 * 1024 * 1024
MAX_CHUNKS = 500
CHUNK_CHARS = 5000
CHUNK_OVERLAP = 350


def _safe_name(name: str) -> str:
    name = str(name or 'file').replace('\\', '/')
    name = name.rsplit('/', 1)[-1]
    name = re.sub(r'[^\w.() -]+', '_', name, flags=re.UNICODE).strip(' ')
    name = name.strip(' ').rstrip(' .')
    return (name or 'file')[:180]


def _is_secret_name(name: str) -> bool:
    low = PurePosixPath(name).name.lower()
    return (is_sensitive_path(name) or low in BLOCKED_NAMES
            or low.endswith(('.ppk', '.kdbx')))


def _decode(data: bytes) -> str:
    if data.startswith((b'\xff\xfe', b'\xfe\xff')):
        return data.decode('utf-16', errors='replace')
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return data.decode('cp1251', errors='replace')


def _chunks(path: str, text: str) -> list[dict]:
    text = text.replace('\x00', '').strip()
    if not text:
        return []
    out = []
    start = 0
    while start < len(text) and len(out) < MAX_CHUNKS:
        end = min(len(text), start + CHUNK_CHARS)
        out.append({'source_path': path, 'chunk_index': len(out), 'content': text[start:end]})
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return out


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for idx, page in enumerate(reader.pages[:200]):
        text = page.extract_text() or ''
        if text.strip():
            pages.append(f'--- Страница {idx + 1} ---\n{text}')
    return '\n\n'.join(pages)


def _extract_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(' | '.join(cell.text for cell in row.cells))
    return '\n'.join(parts)


def extract_document(filename: str, data: bytes) -> tuple[str, list[dict], str]:
    """Return (kind, chunks, note). Never writes or executes archive members."""
    safe = _safe_name(filename)
    low = safe.lower()
    suffix = PurePosixPath(low).suffix
    chunks: list[dict] = []
    note = ''
    if _is_secret_name(safe):
        raise ValueError('Загрузка секретных файлов (.env, ключей и сертификатов) заблокирована. Удали секреты и загрузи безопасную копию.')
    if suffix == '.zip':
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                infos = [i for i in zf.infolist() if not i.is_dir()]
                if len(infos) > MAX_ARCHIVE_MEMBERS:
                    raise ValueError(f'В ZIP слишком много файлов: максимум {MAX_ARCHIVE_MEMBERS}')
                total = sum(max(0, i.file_size) for i in infos)
                if total > MAX_ARCHIVE_TOTAL:
                    raise ValueError('Распакованный объём ZIP превышает безопасный лимит 80 МБ')
                for info in infos:
                    raw_name = info.filename.replace('\\', '/')
                    p = PurePosixPath(raw_name)
                    leaf = p.name
                    if is_sensitive_path(raw_name) or _is_secret_name(leaf):
                        raise ValueError(f'ZIP содержит потенциально секретный файл «{leaf}». Удали секреты из архива и загрузи безопасную копию.')
                    if p.is_absolute() or '..' in p.parts or (info.external_attr >> 28) == 0xA:
                        continue
                    if not leaf or info.file_size > MAX_ARCHIVE_MEMBER:
                        continue
                    ext = PurePosixPath(leaf.lower()).suffix
                    if ext not in TEXT_EXTENSIONS or info.file_size <= 0:
                        continue
                    try:
                        raw = zf.read(info)
                    except Exception:
                        continue
                    text = _decode(raw[:MAX_ARCHIVE_MEMBER])
                    chunks.extend(_chunks(raw_name, text))
                    if len(chunks) >= MAX_CHUNKS:
                        break
            note = f'ZIP: проиндексировано текстовых фрагментов: {len(chunks)}. Файлы не распаковывались на диск.'
            return 'zip', chunks, note
        except zipfile.BadZipFile as e:
            raise ValueError('Файл не является корректным ZIP-архивом') from e
    if suffix == '.pdf':
        try:
            text = _extract_pdf(data)
        except ImportError as e:
            raise ValueError('Для чтения PDF установи зависимости из requirements.txt') from e
        except Exception as e:
            raise ValueError(f'Не удалось прочитать PDF: {e}') from e
        chunks = _chunks(safe, text)
        return 'pdf', chunks, f'PDF: извлечено фрагментов текста: {len(chunks)}. Сканированные страницы без текстового слоя могут не индексироваться.'
    if suffix == '.docx':
        try:
            text = _extract_docx(data)
        except ImportError as e:
            raise ValueError('Для чтения DOCX установи зависимости из requirements.txt') from e
        except Exception as e:
            raise ValueError(f'Не удалось прочитать DOCX: {e}') from e
        chunks = _chunks(safe, text)
        return 'docx', chunks, f'DOCX: извлечено фрагментов текста: {len(chunks)}.'
    if suffix in TEXT_EXTENSIONS or low in {'.gitignore', 'dockerfile'} or low.endswith('.env.example'):
        if len(data) > MAX_TEXT_BYTES:
            text = _decode(data[:MAX_TEXT_BYTES])
            note = 'Индексирован только первый 2 МБ текстового файла.'
        else:
            text = _decode(data)
        chunks = _chunks(safe, text)
        return 'text', chunks, note or f'Текстовых фрагментов: {len(chunks)}.'
    return 'binary', [], 'Файл сохранён. Формат не индексируется; он доступен для скачивания и как вложение к сообщению.'
