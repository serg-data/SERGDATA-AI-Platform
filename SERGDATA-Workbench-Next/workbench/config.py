from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

@dataclass
class Config:
    lm_base_url: str
    lm_api_key: str
    lm_model: str
    kb_enabled: bool
    kb_server: Path
    kb_cwd: Path
    kb_python: str
    project_root: Path
    context_limit: int
    max_tool_rounds: int
    host: str
    port: int

def load_config():
    load_dotenv()
    return Config(
        lm_base_url=os.getenv('LM_BASE_URL','http://127.0.0.1:1234/v1'),
        lm_api_key=os.getenv('LM_API_KEY','lm-studio'),
        lm_model=os.getenv('LM_MODEL','local-model'),
        kb_enabled=os.getenv('KB_ENABLED','true').lower() in ('1','true','yes','on'),
        kb_server=Path(os.getenv('KB_SERVER',r'F:\AI-Knowledge\server.py')),
        kb_cwd=Path(os.getenv('KB_CWD',r'F:\AI-Knowledge')),
        kb_python=os.getenv('KB_PYTHON','python'),
        project_root=Path(__file__).resolve().parent.parent,
        context_limit=max(8192, int(os.getenv('CONTEXT_LIMIT','50000') or 50000)),
        max_tool_rounds=max(4, min(24, int(os.getenv('MAX_TOOL_ROUNDS','16')))),
        host=os.getenv('HOST','127.0.0.1'), port=int(os.getenv('PORT','8787')),
    )
