import json
import asyncio
import time
import re
import logging
from contextlib import AsyncExitStack
from functools import lru_cache

from openai import AsyncOpenAI
from .tokenizer import LMStudioTokenCounter
from .tool_call_adapter import (extract_tool_calls, visible_response_text,
                                empty_response_notice, strip_text_tool_call_markup,
                                contains_tool_call_markup)
from .tool_guard import tool_call_fingerprint
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger('uvicorn.error')

SYSTEM = '''Ты — инженерный помощник SERGDATA Workbench. Отвечай по-русски, точно и по делу.
ТЕКУЩИЙ ПРОЕКТ: работай с файлами только внутри PROJECT_ROOT. SERGDATA Knowledge — отдельная база знаний; её файлы доступны только через MCP.
Используй инструменты для проверки фактов. Не выдумывай содержимое, результаты команд или успешность проверок.
Перед изменением сначала изучи связанные файлы. Право записи определяется уровнем автономности проекта: analysis — через подтверждение; development/full — самостоятельная запись внутри корня проекта с резервной копией. Произвольный PowerShell запускай только через execute_powershell: он всегда создаёт запрос подтверждения, а не выполняет команду сразу. Типовые тесты и Git status/diff доступны через run_project_check. Для экспериментов используй sandbox_create, затем sandbox_read_file/sandbox_write_file/sandbox_run_check и sandbox_diff. Изменяй файлы основного проекта только если пользователь отдельно разрешил это. Песочница является отдельной файловой копией, но не полноценной изоляцией ОС; не запускай в ней недоверенный код с опасными побочными эффектами.
SSH: доступны ssh_read_file (только чтение удалённого файла) и ssh_run_command (команда только через подтверждение пользователя). Для SSH ВСЕГДА используй специализированные SSH-инструменты (ssh_read_file, ssh_run_command или ssh_run_profile_command); запрещено создавать PowerShell/Bash-обёртки, запускать ssh.exe через execute_powershell или обходить SSH Execution Engine. Для ключевой авторизации используй OpenSSH с заранее установленным host key в known_hosts и ключом/ssh-agent. Для любого адреса, который совпадает с зарегистрированным SSH-профилем, используй ssh_run_profile_command с его profile_id. Для парольной авторизации сначала запроси пароль через request_user_secret, затем обнови профиль через update_server_profile с credential_ref. Не вызывай ssh_run_command для зарегистрированного парольного профиля. Workbench дополнительно автоматически направляет generic SSH-вызов через точный совпадающий профиль, чтобы не потерять парольную авторизацию. Никогда не проси пароль в обычном чате, не помещай его в аргументы обычных инструментов и не передавай модели. SSH-профили используют строгую проверку host key и отклоняют неизвестные ключи. Не пытайся обходить проверку. Для удалённой диагностики сначала используй ssh_read_file и безопасные read-only команды через ssh_run_command только после подтверждения. Не читай приватные ключи, .env, пароли, токены, базы учётных данных и /etc/shadow. Не меняй конфигурацию, не перезапускай службы и не выполняй деплой без явного запроса и подтверждения.
ЗАЩИЩЁННЫЙ ВВОД: если для задачи нужен пароль, PIN, OTP, passphrase, API-токен или секретная фраза подтверждения, обязательно создай `request_user_secret` и дождись формы в панели. Никогда не проси такие значения сообщением в обычном чате и не проси пользователя отправить их текстом. Для обычных параметров (имя, адрес, путь, выбор, комментарий) используй `request_user_input`. После отправки формы Workbench автоматически продолжит исходный tool-call; не создавай дублирующий запрос и не начинай параллельную задачу.
Не запускай деплой, не меняй сетевые настройки и не обращайся к внешним сервисам без явного запроса пользователя.
АВТОНОМНЫЙ РЕЖИМ АНАЛИЗА: если пользователь просит аудит, поиск ошибок или диагностику, выполняй работу без дополнительных вопросов: самостоятельно изучи структуру и связанные файлы, используй search_project_files/read_project_file и безопасные run_project_check (pytest, ruff, compile, git_status, git_diff), анализируй результаты и продолжай проверки до исчерпания разумного плана. Не проси подтверждения для чтения, поиска и этих типовых проверок. Не заявляй об отсутствии ошибок только на основании одной проверки.
ИЗМЕНЕНИЯ: соблюдай текущий уровень автономности проекта. В development/full разрешено изменять файлы только через write_project_file и только внутри проекта; после правок запускай проверки и анализируй ошибки. Не удаляй данные и не выполняй системные/сетевые операции без подтверждения. В analysis все записи остаются ожидающими подтверждения.
Для проверок доступны pytest, ruff, compile, git_status и git_diff. Поиск по файлам выполняй через search_project_files. Произвольные команды PowerShell только подготавливай через execute_powershell и жди подтверждения в панели выполнения; не утверждай, что команда выполнена до результата.
ПРОТОКОЛ ДОКАЗАТЕЛЬСТВ И РАБОТЫ С ФАЙЛАМИ:
- Поиск по Knowledge/вложениям возвращает ФРАГМЕНТЫ, а не полный документ. Никогда не делай вывод о полноте документа по результатам поиска.
- Если пользователь просит анализ/резюме/извлечение из конкретного вложенного документа, сначала найди его ID через list_uploaded_files, затем читай read_uploaded_file последовательно до complete=true. Если файл не индексируется или чтение недоступно, прямо укажи ограничение; не выдумывай пропущенные разделы.
- В ответах отделяй подтверждённые факты (с указанием файла/части), выводы/гипотезы и то, что не удалось проверить. Нельзя писать «прочитал полностью», если инструмент не подтвердил complete=true.
- Для search_knowledge и search_uploaded_files явно обозначай, что вывод основан на найденных фрагментах. Не называй документ неполным, пока не проверена его полная структура/все части.
- Результаты инструментов из истории доступны только в пределах фактически сохранённого текста. Если в истории есть сообщение о сокращении результата, исходный полный текст не считай прочитанным.
- Для `read_project_file` читай большие файлы последовательно: внимательно разбирай заголовок результата. Если указан `СТАТУС ЧТЕНИЯ: INCOMPLETE` и `NEXT_START_LINE=N`, обязательно вызови `read_project_file` для того же пути с `start_line=N`. Повторяй до `END_OF_FILE`/`COMPLETE`. Не объявляй файл обрезанным только потому, что получен один фрагмент; не делай выводов по строкам, которые ещё не прочитаны. Не запрашивай уже полученные диапазоны без причины.
- Если генерация завершилась без пользовательского текста и без вызова инструмента, Workbench может один раз попросить продолжить. В таком случае продолжи с последнего подтверждённого состояния: если чтение файла было неполным — запроси следующий диапазон; если анализ завершён — сформируй обычный ответ. Не повторяй уже выполненные действия.
ПРОТОКОЛ РАЗРАБОТКИ:
- Перед изменением изучи спецификацию, дерево проекта и связанные файлы. Сверяйся с обязательными ограничениями и отвергнутыми решениями из спецификации.
- Если спецификация задаёт предварительные проверки/этапы до реализации, выполняй их в указанном порядке. Не начинай массовую генерацию файлов и не обходи архитектурные ворота по собственной инициативе.
- Сначала подготовь проверяемый план/DDL/контракты/сценарии, затем предлагай небольшой этап. Не создавай несколько вариантов одного файла и не дублируй уже ожидающие подтверждения изменения.
- После записи говори только «ожидает подтверждения»; не утверждай, что файл изменён до успешного подтверждения. После подтверждения проверь фактический файл чтением и тестом.
ЭКОНОМИЯ КОНТЕКСТА: не повторяй уже выполненные поиски/чтения, если результат полный и доступен. Не заменяй полный read поиском фрагментов.
ПОЛИТИКА ИСПОЛЬЗОВАНИЯ SERGDATA KNOWLEDGE:
- Для каждой НОВОЙ технической задачи по зарегистрированному локальному проекту до технических выводов, диагностики или реализации выполни хотя бы один целевой search_knowledge. Самостоятельно сформулируй запрос по компоненту, функции, ошибке или изменяемому поведению; не ищи по слишком общему описанию задачи.
- Сначала используй результаты поиска, уже присутствующие в текущем контексте или памяти задачи, если они относятся именно к текущему вопросу и не устарели. В таком случае повторный поиск не нужен. Для обычных уточнений и продолжения той же задачи не запускай поиск механически на каждое сообщение.
- После поиска оцени релевантность. Если найденные фрагменты достаточны, продолжай без чтения дополнительных файлов. Вызывай read_knowledge_file только для проверки конкретного пробела в найденных данных; обычно достаточно поиска и одного чтения.
- Сопоставляй Knowledge с текущими исходниками проекта: Knowledge описывает накопленный контекст и прежние решения, а актуальная реализация и конфигурация подтверждают текущее поведение. При расхождении явно укажи его и не подменяй проверку исходников сведениями из базы.
- Если инструменты Knowledge не подключены, поиск завершился ошибкой или релевантных результатов нет, прямо обозначь это и продолжай по доступным исходникам/документации. Не утверждай, что поиск выполнен, если вызова не было.
- Не выполняй поиск Knowledge для общих вопросов, не относящихся к локальным проектам, и не повторяй его только ради формального соблюдения правила.

МЕЖПРОЕКТНОЕ ИСПОЛЬЗОВАНИЕ SERGDATA KNOWLEDGE:
- SERGDATA Knowledge — единая централизованная база знаний для ВСЕХ проектов пользователя, а не часть текущего проекта и не подкаталог PROJECT_ROOT.
- PROJECT_ROOT ограничивает только локальные файловые операции Workbench. Это ограничение НЕ распространяется на поиск и чтение через MCP SERGDATA Knowledge.
- Не требуй, чтобы исходники или документы искомого проекта находились внутри PROJECT_ROOT. Например, работая в SERGDATA Workbench, можно исследовать Xray-core, исходники которого проиндексированы в коллекции «Колледж».
- Для межпроектного вопроса ищи по названию нужного проекта/технологии и конкретному компоненту. Учитывай пути, названия коллекций, версии и происхождение найденных фрагментов, если MCP их возвращает.
- Сначала используй наиболее релевантные материалы по запрошенному проекту, но не ограничивай поиск текущим PROJECT_ROOT или названием активного проекта. При необходимости используй общие технические материалы и сведения из других проектов.
- Не считай, что MCP поддерживает фильтр по коллекциям или проектам, если такого параметра нет в фактической схеме инструмента. Не выдумывай параметры поиска. Если явная фильтрация недоступна, сформулируй запрос так, чтобы однозначно указать нужный проект и технологию, а релевантность оцени по фактическим результатам.
- Knowledge предоставляет сведения и фрагменты через MCP; это не разрешение читать или изменять расположенные вне PROJECT_ROOT файлы обычными файловыми инструментами. Не обходи границы PROJECT_ROOT.
- ЯВНО УКАЗАННЫЙ ВНЕШНИЙ ПРОЕКТ: если пользователь в текущем запросе явно указал точный корневой путь другого зарегистрированного проекта Workbench, можно использовать только `list_registered_project_files` и `read_registered_project_file` для чтения внутри этого корня. Это временное read-only разрешение текущего запроса; оно не меняет PROJECT_ROOT. Не записывай файлы, не запускай команды и не используй абсолютные/родительские пути для выхода из указанного корня. Если путь не зарегистрирован или не указан пользователем в текущем сообщении, доступ запрещён; попроси зарегистрировать проект или выбрать его в интерфейсе.
- При анализе текущей реализации сопоставляй сведения из общей базы с исходниками именно активного проекта. Материалы другого проекта могут объяснять технологию или прежний опыт, но не доказывают поведение текущего проекта.

ВАЖНО ДЛЯ SERGDATA KNOWLEDGE: search_knowledge может возвращать виртуальные пути из разных коллекций. Для read_knowledge_file используй только путь, который явно поддерживается результатом поиска/инструкцией MCP. Если получен отказ «Файл не найден или путь находится вне разрешённых папок», не повторяй тот же вызов и не перебирай варианты. Если поиск уже вернул фрагмент кода, анализируй этот фрагмент и сообщи, что полный файл по этому виртуальному пути недоступен для чтения.
Если задача большая, разбивай её на этапы. По достижении лимита инструментов дай полезный промежуточный итог и точный следующий шаг; не проси пользователя просто написать «продолжай» без объяснения, что уже сделано.
'''


@lru_cache(maxsize=1)
def _encoding():
    try:
        import tiktoken
        return tiktoken.get_encoding('cl100k_base')
    except Exception:
        return None


def _normalise_project_path(value):
    """Normalise a displayed project root for Windows-style exact matching."""
    import ntpath
    raw = str(value or '').strip().strip('`\"\'')
    if not raw:
        return ''
    return ntpath.normcase(ntpath.normpath(raw.replace('/', '\\'))).rstrip('\\')


def _explicit_external_project_roots(user_text, projects, active_project_id=None):
    """Return registered non-active roots literally named in this user turn."""
    import ntpath
    text = ntpath.normcase(str(user_text or '').replace('/', '\\'))
    allowed = []
    for project in projects or []:
        if project.get('archived_at'):
            continue
        if active_project_id is not None and int(project.get('id', -1)) == int(active_project_id):
            continue
        root = str(project.get('root') or '').strip()
        key = _normalise_project_path(root)
        if not key:
            continue
        pos = text.find(key)
        while pos >= 0:
            end = pos + len(key)
            next_char = text[end:end + 1]
            exact_end = not next_char or next_char in ' \t\r\n`\"\'.,;:)]}'
            trailing_separator_only = next_char == '\\' and (
                not text[end + 1:end + 2] or text[end + 1:end + 2] in ' \t\r\n`\"\'.,;:)]}'
            )
            # A child path such as <root>\src is NOT explicit consent to the
            # entire registered root; require the root itself to be named.
            if exact_end or trailing_separator_only:
                allowed.append(root)
                break
            pos = text.find(key, pos + 1)
    return tuple(dict.fromkeys(allowed))


def estimate_tokens(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    enc = _encoding()
    if enc:
        return len(enc.encode(text))
    return max(1, len(text) // 3)


class Agent:
    def __init__(self, cfg, store, project):
        self.cfg = cfg
        self.store = store
        from .credential_broker import CredentialBroker
        self.credentials = CredentialBroker(store.path.parent / 'credentials.dpapi')
        self.project = project
        self.llm = AsyncOpenAI(base_url=cfg.lm_base_url, api_key=cfg.lm_api_key)
        self.stack = AsyncExitStack()
        self.kb = None
        self.kbtools = {}
        self.kb_status = 'Отключена'
        self.last_model = cfg.lm_model
        self.token_counter = LMStudioTokenCounter(cfg.lm_base_url, cfg.lm_api_key)
        self.runtime_settings = store.get_app_settings()
        self.activity_callback = None

    def _set_activity(self, branch_id, stage, detail=''):
        callback=getattr(self,'activity_callback',None)
        if callback:
            try: callback(int(branch_id),stage,detail)
            except Exception: pass

    async def connect(self):
        if not self.cfg.kb_enabled:
            return
        try:
            params = StdioServerParameters(command=self.cfg.kb_python, args=[str(self.cfg.kb_server)], cwd=str(self.cfg.kb_cwd), env=None)
            r, w = await self.stack.enter_async_context(stdio_client(params))
            self.kb = await self.stack.enter_async_context(ClientSession(r, w))
            await self.kb.initialize()
            tools = await self.kb.list_tools()
            self.kbtools = {t.name: t for t in tools.tools}
            self.kb_status = 'Подключена: ' + ', '.join(self.kbtools)
        except Exception as e:
            self.kb_status = f'Не подключена: {type(e).__name__}: {e}'

    def specs(self):
        items = [
            ('list_project_files', 'Рекурсивный список файлов и каталогов проекта до 5 уровней. Резервные копии исключены по умолчанию. Путь относительный к PROJECT_ROOT.', {'type': 'object', 'properties': {'path': {'type': 'string'}, 'max_depth': {'type': 'integer', 'minimum': 1, 'maximum': 8}, 'include_backups': {'type': 'boolean'}}}),
            ('read_project_file', 'Прочитать файл текущего проекта. Путь относительный к PROJECT_ROOT.', {'type': 'object', 'properties': {'path': {'type': 'string'}, 'start_line': {'type': 'integer'}, 'end_line': {'type': 'integer'}}, 'required': ['path']}),
            ('write_project_file', 'Изменить файл проекта согласно уровню автономности: analysis создаёт запрос подтверждения; development/full записывают внутри проекта с резервной копией.', {'type': 'object', 'properties': {'path': {'type': 'string'}, 'content': {'type': 'string'}}, 'required': ['path', 'content']}),
            ('run_project_check', 'Запустить безопасную типовую проверку проекта или Git status/diff без произвольного shell.', {'type': 'object', 'properties': {'command': {'type': 'string', 'enum': ['pytest', 'ruff', 'compile', 'git_status', 'git_diff']}}, 'required': ['command']}),
            ('sandbox_create', 'Создать изолированную файловую копию проекта или выбранных файлов для экспериментов. Не копирует секреты, базы данных, .git, виртуальные окружения и пользовательские загрузки.', {'type':'object','properties':{'name':{'type':'string'},'paths':{'type':'array','items':{'type':'string'},'maxItems':200}},'required':[]}),
            ('sandbox_list_files', 'Показать файлы экспериментальной песочницы.', {'type':'object','properties':{'sandbox_id':{'type':'string'}},'required':['sandbox_id']}),
            ('sandbox_read_file', 'Прочитать файл внутри экспериментальной песочницы.', {'type':'object','properties':{'sandbox_id':{'type':'string'},'path':{'type':'string'}},'required':['sandbox_id','path']}),
            ('sandbox_write_file', 'Изменить или создать файл ТОЛЬКО внутри песочницы. Не изменяет исходный проект.', {'type':'object','properties':{'sandbox_id':{'type':'string'},'path':{'type':'string'},'content':{'type':'string'}},'required':['sandbox_id','path','content']}),
            ('sandbox_run_check', 'Запустить типовую проверку внутри песочницы. Для pytest можно передать ограниченные args (относительные пути и безопасные флаги). Для Shell доступны только статические проверки синтаксиса sh -n/bash -n и shellcheck.', {'type':'object','properties':{'sandbox_id':{'type':'string'},'command':{'type':'string','enum':['pytest','compile','ruff','sh_syntax','bash_syntax','shellcheck']},'path':{'type':'string'},'args':{'type':'array','items':{'type':'string'},'maxItems':30}},'required':['sandbox_id','command']}),
            ('sandbox_diff', 'Сравнить файлы песочницы с исходным проектом и показать изменённые/новые файлы.', {'type':'object','properties':{'sandbox_id':{'type':'string'}},'required':['sandbox_id']}),
            ('git_init', 'Создать Git-репозиторий в корне текущего проекта, если его ещё нет. Не создаёт коммит и не публикует файлы.', {'type':'object','properties':{}}),
            ('git_stage', 'Добавить указанные относительные пути в Git index. Не используй для секретов; сначала покажи status и проверь .gitignore.', {'type':'object','properties':{'paths':{'type':'array','items':{'type':'string'},'minItems':1,'maxItems':100}},'required':['paths']}),
            ('git_unstage', 'Убрать указанные относительные пути из Git index, не меняя файлы.', {'type':'object','properties':{'paths':{'type':'array','items':{'type':'string'},'minItems':1,'maxItems':100}},'required':['paths']}),
            ('git_commit', 'Создать локальный коммит только после явного запроса пользователя на коммит. Перед этим обязательно изучи staged diff и проверь, что секреты не добавлены.', {'type':'object','properties':{'message':{'type':'string','minLength':1,'maxLength':200}},'required':['message']}),
            ('git_remote', 'Подключить или обновить remote origin. Не публикует данные.', {'type':'object','properties':{'name':{'type':'string'},'url':{'type':'string'}},'required':['name','url']}),
            ('git_sync', 'Git fetch/pull/push. Pull и Push разрешены только при явном запросе пользователя; перед Push проверь diff, секреты и статус. Pull/Push блокируются при локальных незакоммиченных изменениях.', {'type':'object','properties':{'action':{'type':'string','enum':['fetch','pull','push']}},'required':['action']}),
            ('compare_registered_projects', 'Сравнить текущий проект с другим зарегистрированным проектом по содержимому файлов. Секреты, .git, базы и служебные каталоги исключены. Только чтение.', {'type':'object','properties':{'target_project_id':{'type':'integer'}},'required':['target_project_id']}),
            ('list_registered_project_files', 'Только чтение файлов другого зарегистрированного проекта. Используй только если пользователь явно указал его точный корневой путь в текущем запросе; root должен совпадать с этим путём. PROJECT_ROOT текущей ветки не меняется.', {'type':'object','properties':{'root':{'type':'string'},'path':{'type':'string'},'max_depth':{'type':'integer','minimum':1,'maximum':8}},'required':['root']}),
            ('read_registered_project_file', 'Прочитать текстовый файл другого зарегистрированного проекта. Только чтение; допустимо только если пользователь явно указал точный корневой путь проекта в текущем запросе. Путь файла относителен к root.', {'type':'object','properties':{'root':{'type':'string'},'path':{'type':'string'},'start_line':{'type':'integer'},'end_line':{'type':'integer'}},'required':['root','path']}),
            ('prepare_project_release', 'Подготовить выборочный план переноса указанных файлов из текущего проекта в зарегистрированный целевой проект. Не изменяет целевой проект; применение возможно только через отдельное подтверждение пользователя в интерфейсе.', {'type':'object','properties':{'target_project_id':{'type':'integer'},'paths':{'type':'array','items':{'type':'string'},'minItems':1,'maxItems':500}},'required':['target_project_id','paths']}),
            ('search_project_files', 'Найти текст в файлах проекта. Исключает бинарные файлы, секреты и служебные каталоги.', {'type': 'object', 'properties': {'query': {'type': 'string'}, 'path': {'type': 'string'}}, 'required': ['query']}),
            ('execute_powershell', 'Подготовить команду PowerShell к выполнению. Команда НЕ запускается сразу: пользователь должен явно подтвердить её в панели выполнения. Рабочая папка — корень проекта.', {'type': 'object', 'properties': {'script': {'type': 'string'}}, 'required': ['script']}),
            ('ssh_read_file', 'Прочитать удалённый текстовый файл по SSH. Только чтение; использует системный OpenSSH, ключ/ssh-agent и строгую проверку host key. Сервер должен быть заранее добавлен в known_hosts.', {'type':'object','properties':{'host':{'type':'string'},'user':{'type':'string'},'port':{'type':'integer','minimum':1,'maximum':65535},'path':{'type':'string'}},'required':['host','user','port','path']}),
            ('ssh_run_command', 'Подготовить произвольную команду Ubuntu/Linux по SSH. Команда НЕ запускается до явного подтверждения пользователем в панели выполнения.', {'type':'object','properties':{'host':{'type':'string'},'user':{'type':'string'},'port':{'type':'integer','minimum':1,'maximum':65535},'command':{'type':'string'}},'required':['host','user','port','command']}),
            ('request_user_input', 'Запросить у пользователя обычное несекретное значение (например, имя, путь, параметр или выбор). Ответ будет передан модели после отправки формы.', {'type':'object','properties':{'title':{'type':'string'},'prompt':{'type':'string'}},'required':['title','prompt']}),
            ('request_user_secret', 'Запросить у пользователя пароль, PIN, OTP, passphrase или API-токен. Значение НЕ попадёт в историю модели или SQLite; вернётся только непрозрачный credential_ref для доверенного инструмента.', {'type':'object','properties':{'title':{'type':'string'},'prompt':{'type':'string'}},'required':['title','prompt']}),
            ('list_server_profiles', 'Показать сохранённые SSH-профили. Секреты и ссылки на секреты не раскрываются.', {'type':'object','properties':{}}),
            ('create_server_profile', 'Создать SSH-профиль. Для auth_method=password передай только credential_ref, полученный через request_user_secret; пароль никогда не передавай аргументом.', {'type':'object','properties':{'name':{'type':'string'},'host':{'type':'string'},'port':{'type':'integer','minimum':1,'maximum':65535},'username':{'type':'string'},'auth_method':{'type':'string','enum':['key','password']},'credential_ref':{'type':'string'}},'required':['name','host','port','username','auth_method']}),
            ('update_server_profile', 'Обновить пароль существующего SSH-профиля. Принимай только credential_ref из request_user_secret, не пароль.', {'type':'object','properties':{'profile_id':{'type':'integer','minimum':1},'credential_ref':{'type':'string'}},'required':['profile_id','credential_ref']}),
            ('ssh_run_profile_command', 'Подготовить SSH-команду через сохранённый профиль. Команда запускается только после подтверждения пользователем.', {'type':'object','properties':{'profile_id':{'type':'integer','minimum':1},'command':{'type':'string'}},'required':['profile_id','command']}),
            ('list_uploaded_files', 'Список вложений, загруженных в текущий проект или задачу Workbench. Возвращает ID и число индексированных частей.', {'type': 'object', 'properties': {}}),
            ('read_uploaded_file', 'Последовательно прочитать индексированный документ по ID. Используй для полного анализа документа; читай следующие части по next_chunk, пока complete=true. Поиск не заменяет полное чтение.', {'type': 'object', 'properties': {'attachment_id': {'type': 'integer'}, 'start_chunk': {'type': 'integer', 'minimum': 0}, 'max_chunks': {'type': 'integer', 'minimum': 1, 'maximum': 6}}, 'required': ['attachment_id']}),
            ('search_uploaded_files', 'Поиск по индексированному тексту загруженных вложений, включая текстовые файлы внутри ZIP, PDF и DOCX. Используй, если нужная часть большого вложения не попала в начальный контекст.', {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']}),
        ]
        out = [{'type': 'function', 'function': {'name': n, 'description': d, 'parameters': s}} for n, d, s in items]
        for n, t in self.kbtools.items():
            schema = getattr(t, 'input_schema', None) or getattr(t, 'inputSchema', None)
            if schema is None and hasattr(t, 'model_dump'):
                x = t.model_dump(by_alias=True)
                schema = x.get('inputSchema') or x.get('input_schema')
            desc = getattr(t, 'description', None) or n
            if n == 'read_knowledge_file':
                desc += ' Используй точный относительный путь из результата search_knowledge. Не передавай абсолютный путь и не повторяй вызов, если MCP сообщил о запрете/отсутствии файла.'
            if n == 'search_knowledge':
                desc += ' Результаты могут содержать готовые фрагменты и виртуальные пути; сохраняй эти фрагменты и не считай каждый путь гарантированно доступным для read_knowledge_file.'
            out.append({'type': 'function', 'function': {'name': n, 'description': desc, 'parameters': schema if isinstance(schema, dict) else {'type': 'object', 'properties': {}}}})
        return out

    def project_tools(self, bid):
        from pathlib import Path
        from .tools import ProjectTools
        row = self.store.project_for_branch(bid)
        if not row:
            raise ValueError('Проект для этой ветки не найден')
        return ProjectTools(Path(row['root']))

    # Важно: текст пользователя в чате вроде «подтверждаю» сам по себе не является
    # разрешением на запуск; сообщение «подтверждаю» в чате само по себе не запускает команду.
    # Только отдельная кнопка approve меняет pending_execution.
    async def tool(self, name, args, bid, authorized_external_roots=()):
        if name in {'list_registered_project_files', 'read_registered_project_file'}:
            from pathlib import Path
            from .tools import ProjectTools
            requested_root = str(args.get('root') or '').strip()
            allowed = {_normalise_project_path(root) for root in authorized_external_roots}
            if not requested_root or _normalise_project_path(requested_root) not in allowed:
                return ('Доступ к другому проекту не разрешён: пользователь должен явно указать его точный '
                        'корневой путь в текущем запросе. Это ограничение нельзя обойти абсолютным путём.')
            project = self.store.find_project_by_root(requested_root)
            if not project or project.get('archived_at'):
                return ('Указанный путь не зарегистрирован как активный проект Workbench. '
                        'Сначала добавь его через управление проектами или выбери зарегистрированный проект.')
            project_tools = ProjectTools(Path(project['root']))
            if name == 'list_registered_project_files':
                return project_tools.listing(args.get('path', '.'), args.get('max_depth', 5), limit=500)
            return project_tools.read(args.get('path'), args.get('start_line', 1), args.get('end_line', 0))

        if name in ('list_uploaded_files', 'read_uploaded_file', 'search_uploaded_files'):
            project_row = self.store.project_for_branch(bid)
            task_row = self.store.task_for_branch(bid)
            if not project_row:
                return 'Проект ветки не найден.'
            if name == 'list_uploaded_files':
                files = self.store.attachments(project_row['id'], task_row['id'] if task_row else None, bid)
                if not files:
                    return 'В Workbench пока нет загруженных вложений для этого проекта/ветки.'
                return '\n'.join(f"- ID {x['id']}: {x['original_name']} ({x['size']} байт, {x['kind']}, индексированных частей: {x['chunks']})" for x in files)
            if name == 'read_uploaded_file':
                result = self.store.read_attachment_chunks(
                    int(args['attachment_id']), project_row['id'],
                    task_row['id'] if task_row else None, bid,
                    int(args.get('start_chunk', 0)), int(args.get('max_chunks', 3)),
                )
                meta = result['attachment']
                if result['total_chunks'] == 0:
                    return (f"Файл {meta['original_name']} (ID {meta['id']}) не имеет индексируемого текстового содержимого. "
                            f"Тип: {meta['kind']}. {meta['note']} Полное текстовое чтение невозможно.")
                status = 'ПОЛНОСТЬЮ ПРОЧИТАН' if result['complete'] else 'ЧАСТИЧНО ПРОЧИТАН — НУЖНО ПРОДОЛЖИТЬ'
                header = (f"ДОКУМЕНТ: {meta['original_name']} (ID {meta['id']})\nСТАТУС ПОКРЫТИЯ: {status}\n"
                          f"ЧАСТИ: {result['start_chunk'] + 1}–{result['end_chunk'] + 1} из {result['total_chunks']}\n"
                          f"СЛЕДУЮЩАЯ ЧАСТЬ: {result['next_chunk'] + 1 if result['next_chunk'] is not None else 'нет'}\n")
                body = '\n\n'.join(f"[ЧАСТЬ {x['chunk_index'] + 1}; путь внутри архива: {x['source_path']}]\n{x['content']}" for x in result['chunks'])
                return header + '\n' + body
            query = str(args.get('query') or '').strip()
            if not query:
                return 'Укажи поисковый запрос.'
            hits = self.store.search_attachments(project_row['id'], query, task_row['id'] if task_row else None, bid, limit=12)
            if not hits:
                return 'Совпадений в индексированных вложениях не найдено.'
            parts=[]
            for hit in hits:
                parts.append(f"Файл: {hit['original_name']}\nПуть в архиве: {hit['source_path']}\nФрагмент: {hit['content'][:1800]}")
            return '\n\n---\n\n'.join(parts)[:18000]
        if name in {'request_user_input', 'request_user_secret'}:
            title = str(args.get('title') or '').strip()
            prompt = str(args.get('prompt') or '').strip()
            if not title or not prompt:
                return 'Для запроса ввода нужны непустые title и prompt.'
            if len(title) > 160 or len(prompt) > 2000:
                return 'Заголовок или пояснение запроса превышает допустимую длину.'
            kind = 'secret' if name == 'request_user_secret' else 'text'
            request_id = self.store.add_input_request(bid, title, prompt, kind)
            return f"Запрос {'защищённого секрета' if kind == 'secret' else 'пользовательского ввода'} создан. ID={request_id}. Ожидается ответ в панели Workbench."
        if name == 'list_server_profiles':
            profiles = self.store.server_profiles()
            if not profiles:
                return 'Сохранённых SSH-профилей нет. Пользователь может добавить их в панели SSH-профилей.'
            def auth_label(profile):
                if profile['auth_method'] != 'password':
                    return 'SSH-ключ'
                state = self.credentials.status(profile.get('credential_ref', ''))
                return {
                    'persistent': 'пароль доступен, сохранён через DPAPI',
                    'session': 'пароль доступен только в текущем сеансе Workbench',
                    'missing': 'ссылка на пароль есть в профиле, но секрет недоступен в CredentialBroker'
                }[state]
            return '\n'.join(
                f"ID {p['id']}: {p['name']} — {p['username']}@{p['host']}:{p['port']} ({auth_label(p)})"
                for p in profiles)
        if name == 'create_server_profile':
            try:
                from .ssh import validate_fields
                profile_name = str(args.get('name') or '').strip()
                if not profile_name or len(profile_name) > 80:
                    return 'Название SSH-профиля должно содержать от 1 до 80 символов.'
                host, username, port = validate_fields(args.get('host'), args.get('username'), args.get('port'))
                auth_method = str(args.get('auth_method') or '')
                if auth_method not in {'key', 'password'}:
                    return 'Недопустимый способ SSH-аутентификации.'
                credential_ref = str(args.get('credential_ref') or '')
                if auth_method == 'password':
                    if not self.credentials.exists(credential_ref):
                        return 'credential_ref отсутствует в защищённом хранилище. Сначала запроси пароль через request_user_secret.'
                    self.credentials.resolve(credential_ref)
                if auth_method == 'key':
                    credential_ref = ''
                duplicate = next((p for p in self.store.server_profiles()
                                  if p['name'].casefold() == profile_name.casefold()
                                  and p['host'].casefold() == host.casefold()
                                  and int(p['port']) == port and p['username'] == username), None)
                if duplicate:
                    return f"Профиль уже существует: ID={duplicate['id']}."
                profile_id = self.store.save_server_profile(None, profile_name, host, port, username,
                                                            auth_method, credential_ref)
                if credential_ref:
                    self.store.detach_credential_ref_from_input_requests(credential_ref)
                return f"SSH-профиль «{profile_name}» создан. ID={profile_id}. Секрет хранится отдельно от SQLite."
            except Exception as exc:
                return f'SSH_PROFILE_CREATE_ERROR: {type(exc).__name__}: {exc}'
        if name == 'update_server_profile':
            try:
                profile_id = int(args.get('profile_id') or 0)
                profile = self.store.server_profile(profile_id)
                if not profile:
                    return 'SSH-профиль не найден.'
                if profile['auth_method'] != 'password':
                    return 'Обновление credential_ref доступно только для парольного профиля.'
                credential_ref = str(args.get('credential_ref') or '')
                if not self.credentials.exists(credential_ref):
                    return 'credential_ref отсутствует в CredentialBroker. Сначала запроси пароль через request_user_secret.'
                self.credentials.resolve(credential_ref)
                old_ref = profile.get('credential_ref', '')
                self.store.save_server_profile(profile_id, profile['name'], profile['host'], profile['port'],
                                               profile['username'], 'password', credential_ref)
                self.store.detach_credential_ref_from_input_requests(credential_ref)
                if old_ref and old_ref != credential_ref and not self.store.credential_ref_used_by_profile(old_ref):
                    self.credentials.delete(old_ref)
                return f"Пароль SSH-профиля «{profile['name']}» обновлён."
            except Exception as exc:
                return f'SSH_PROFILE_UPDATE_ERROR: {type(exc).__name__}: {exc}'
        if name == 'ssh_run_profile_command':
            try:
                profile_id = int(args['profile_id'])
                profile = self.store.server_profile(profile_id)
                if not profile:
                    return 'SSH-профиль не найден.'
                command = str(args.get('command') or '').strip()
                from .ssh import MAX_COMMAND, validate_fields
                validate_fields(profile['host'], profile['username'], profile['port'])
                if not command or len(command) > MAX_COMMAND:
                    return 'Команда пуста или превышает лимит 12000 символов.'
                if profile['auth_method'] == 'password' and not self.credentials.exists(profile['credential_ref']):
                    return 'Для SSH-профиля отсутствует пароль в CredentialBroker. Запроси у пользователя новый секрет и обнови профиль.'
                queued = '__SERGDATA_PROFILE_EXEC_V1__' + json.dumps({'kind':'ssh_profile','profile_id':profile_id,'command':command}, ensure_ascii=False)
                existing = self.store.pending_executions(bid)
                if any(x['script'] == queued for x in existing):
                    return f"Такая команда уже ожидает подтверждения (ID={next(x['id'] for x in existing if x['script']==queued)})."
                eid = self.store.add_pending_execution(bid, queued)
                return f"SSH-команда через профиль «{profile['name']}» поставлена на подтверждение. ID={eid}. До подтверждения не выполняется."
            except Exception as exc:
                return f'SSH_PROFILE_PREPARE_ERROR: {type(exc).__name__}: {exc}'

        project_tools = self.project_tools(bid)
        if name == 'list_project_files':
            return project_tools.listing(**args)
        if name == 'read_project_file':
            return project_tools.read(**args)
        if name == 'write_project_file':
            # Validate path before queueing the change.
            project_tools.safe(args['path'])
            existing = self.store.pending_for_path(bid, args['path'])
            if existing:
                if existing['content'] == args['content']:
                    return f"ДУБЛЬ ПРЕДОТВРАЩЁН: для {args['path']} уже есть ожидающее изменение ID={existing['id']}. Новый запрос не создан; файл НЕ изменён."
                return (f"КОНФЛИКТ ОЖИДАЮЩЕГО ИЗМЕНЕНИЯ: для {args['path']} уже есть pending ID={existing['id']} с другим содержимым. "
                        'Не создавай второй вариант и не перезаписывай первый. Сначала покажи пользователю различие и запроси решение.')
            project_row = self.store.project_for_branch(bid)
            autonomy = self.store.get_project_settings(project_row['id'])['autonomy'] if project_row else 'analysis'
            if autonomy in ('development','full'):
                result = project_tools.write(args['path'], args['content'])
                return f'{result}. Автономный режим {autonomy}: создана резервная копия существующего файла (если он был).'
            pid = self.store.add_pending(bid, args['path'], args['content'])
            return f'Изменение поставлено на подтверждение пользователя. ID={pid}. Файл НЕ изменён.'
        if name in {'git_init','git_stage','git_unstage','git_commit','git_remote','git_sync'}:
            from .git_manager import GitManager
            try:
                gm=GitManager(project_tools.root)
                if name == 'git_init':
                    result=gm.init()
                elif name == 'git_stage':
                    result=gm.stage(args.get('paths') or [])
                elif name == 'git_unstage':
                    result=gm.unstage(args.get('paths') or [])
                elif name == 'git_commit':
                    result=gm.commit(args.get('message',''))
                elif name == 'git_remote':
                    result=gm.remote_add(args.get('name','origin'),args.get('url',''))
                else:
                    result=gm.sync(args.get('action',''))
                return json.dumps(result,ensure_ascii=False)
            except Exception as exc:
                return f'GIT_OPERATION_ERROR: {type(exc).__name__}: {exc}'
        if name in {'compare_registered_projects','prepare_project_release'}:
            from .release_manager import ReleaseManager
            try:
                source_row=self.store.project_for_branch(bid)
                target_row=self.store.project(int(args['target_project_id']))
                if not source_row or not target_row: return 'Не найден исходный или целевой зарегистрированный проект.'
                rm=ReleaseManager(source_row['root'],target_row['root'])
                if name=='compare_registered_projects': result=rm.compare()
                else: result=rm.prepare(args.get('paths') or [])
                return json.dumps(result,ensure_ascii=False)
            except Exception as exc:
                return f'RELEASE_OPERATION_ERROR: {type(exc).__name__}: {exc}'
        if name.startswith('sandbox_'):
            from .sandbox import SandboxManager
            try:
                sm=SandboxManager(project_tools.root)
                if name=='sandbox_create': result=sm.create(args.get('name','Эксперимент'),args.get('paths') or None)
                elif name=='sandbox_list_files': result=sm.list_files(args['sandbox_id'])
                elif name=='sandbox_read_file': result=sm.read(args['sandbox_id'],args['path'])
                elif name=='sandbox_write_file': result=sm.write(args['sandbox_id'],args['path'],args['content'])
                elif name=='sandbox_run_check': result=sm.run_check(args['sandbox_id'],args['command'],path=args.get('path'),args=args.get('args'))
                elif name=='sandbox_diff': result=sm.diff(args['sandbox_id'])
                else: return 'Неизвестная операция Sandbox.'
                return json.dumps(result,ensure_ascii=False) if not isinstance(result,str) else result
            except Exception as exc:
                return f'SANDBOX_ERROR: {type(exc).__name__}: {exc}'
        if name == 'run_project_check':
            from .execution import ExecutionEngine
            result=ExecutionEngine(project_tools.root).run_check(args['command'])
            return f"status={result.get('status')} exit_code={result['exit_code']} duration={result.get('duration_sec')}s\nSTDOUT:\n{result.get('stdout','')}\nSTDERR:\n{result.get('stderr','')}"
        if name == 'search_project_files':
            from .execution import ExecutionEngine
            return ExecutionEngine(project_tools.root).search(args['query'],args.get('path','.'))
        if name == 'ssh_read_file':
            from .ssh import read_remote_file
            try:
                r = await asyncio.to_thread(read_remote_file, args['host'], args['user'], args['port'], args['path'])
                return (f"SSH read status={r['status']} exit_code={r['exit_code']}\nSTDOUT:\n{r['stdout']}\nSTDERR:\n{r['stderr']}")
            except Exception as exc:
                return f'SSH_READ_ERROR: {type(exc).__name__}: {exc}'
        if name == 'ssh_run_command':
            from .ssh import validate_fields, validate_target, find_matching_profile, MAX_COMMAND
            try:
                host, username, port = validate_fields(args['host'], args['user'], args['port'])
                command = str(args.get('command') or '').strip()
                if not command or len(command) > MAX_COMMAND:
                    return 'Команда пуста или превышает лимит 12000 символов.'

                # Safety/compatibility bridge: if the model calls the generic SSH tool
                # for a target already registered in Server Profiles, always route it
                # through that profile. This is essential for password profiles: the
                # generic OpenSSH path deliberately disables password auth.
                profile = find_matching_profile(
                    self.store.server_profiles(), args['host'], args['user'], args['port']
                )
                if profile:
                    if profile['auth_method'] == 'password' and not self.credentials.exists(profile.get('credential_ref', '')):
                        return (f"Для профиля «{profile['name']}» CredentialBroker не может получить секрет. "
                                "Запроси его через request_user_secret, затем обнови этот профиль через "
                                "update_server_profile с credential_ref. Не используй ssh_run_command "
                                "для обхода профиля.")
                    queued = '__SERGDATA_PROFILE_EXEC_V1__' + json.dumps(
                        {'kind':'ssh_profile','profile_id':int(profile['id']),'command':command},
                        ensure_ascii=False
                    )
                    existing = self.store.pending_executions(bid)
                    if any(x['script'] == queued for x in existing):
                        return f"Такая команда через профиль «{profile['name']}» уже ожидает подтверждения (ID={next(x['id'] for x in existing if x['script']==queued)})."
                    eid = self.store.add_pending_execution(bid, queued)
                    return (f"SSH-команда автоматически направлена через зарегистрированный профиль "
                            f"«{profile['name']}» и поставлена на подтверждение. ID={eid}. "
                            "До подтверждения не выполняется.")

                validate_target(host, username, port)
                payload = {'kind':'ssh','host':host,'user':username,'port':port,'command':command}
                queued = '__SERGDATA_EXEC_V1__' + json.dumps(payload, ensure_ascii=False)
                existing = self.store.pending_executions(bid)
                if any(x['script'] == queued for x in existing):
                    return f"Такая SSH-команда уже ожидает подтверждения (ID={next(x['id'] for x in existing if x['script']==queued)})."
                eid = self.store.add_pending_execution(bid, queued)
                return f"SSH-команда для {args['user']}@{args['host']}:{args['port']} поставлена на подтверждение. ID={eid}. До подтверждения не выполняется."
            except Exception as exc:
                return f'SSH_PREPARE_ERROR: {type(exc).__name__}: {exc}'
        if name == 'execute_powershell':
            script=str(args.get('script') or '').strip()
            if not script or len(script)>12000: return 'Команда пустая или превышает 12000 символов.'
            if re.search(r'(?i)(?:\bssh(?:\.exe)?\b|ssh[_A-Za-z]*exe|\bssh-add(?:\.exe)?\b|\bplink(?:\.exe)?\b|\bpageant\b|(?:fin|sub)\.sergdata\.top)', script):
                return 'SSH-ОБХОД ЗАБЛОКИРОВАН: не запускай SSH через PowerShell. Используй специализированный инструмент ssh_run_command; он поддерживает подтверждение, строгую проверку host key и возврат результата.'
            existing=self.store.pending_executions(bid)
            if any(x['script']==script for x in existing): return f"Такая команда уже ожидает подтверждения (ID={next(x['id'] for x in existing if x['script']==script)})."
            eid=self.store.add_pending_execution(bid,script)
            return f'Команда PowerShell поставлена в очередь на подтверждение пользователя. ID={eid}. До подтверждения она НЕ выполняется.'
        if name in self.kbtools and self.kb:
            result = await self.kb.call_tool(name, args)
            parts = [x.text for x in result.content if hasattr(x, 'text')]
            text = '\n'.join(parts) or str(result)
            if getattr(result, 'isError', False):
                return 'ОШИБКА MCP: ' + text
            return text
        return 'Инструмент недоступен'

    async def models(self):
        try:
            return [m.id for m in (await self.llm.models.list()).data]
        except Exception as e:
            return [f'Ошибка связи: {e}']

    async def resolve_model_id(self):
        """Resolve the real model ID used by LM Studio instead of the local-model alias."""
        if self.last_model and self.last_model != 'local-model':
            return self.last_model
        if self.cfg.lm_model and self.cfg.lm_model != 'local-model':
            return self.cfg.lm_model
        available = await self.models()
        return next((x for x in available if x and not x.startswith('Ошибка')), self.cfg.lm_model)

    def prompt_metrics(self, messages, tools=None, model_id=None):
        """Model-aware preflight token count; falls back transparently if SDK is unavailable."""
        model_id = model_id or self.last_model or self.cfg.lm_model
        try:
            return self.token_counter.count(model_id, messages, tools or [])
        except Exception as exc:
            msg_count = estimate_tokens(messages)
            tool_count = estimate_tokens(tools or [])
            return {
                'messages_tokens': msg_count,
                'tools_tokens_estimate': tool_count,
                'format_overhead_estimate': 0,
                'estimated_prompt_tokens': msg_count + tool_count,
                'model_context_limit': None,
                'tokenizer_status': 'fallback_estimate',
                'estimate_method': 'tiktoken cl100k_base; токенизатор модели LM Studio недоступен',
                'tokenizer_error': f'{type(exc).__name__}: {exc}'[:240],
            }

    async def model_context_metadata(self, model_id):
        """Read LM Studio's model metadata when SDK can't report the loaded context length."""
        try:
            import httpx
            from urllib.parse import urlsplit
            parsed = urlsplit(self.cfg.lm_base_url)
            base = f'{parsed.scheme}://{parsed.netloc}'
            headers = {}
            if self.cfg.lm_api_key and self.cfg.lm_api_key != 'lm-studio':
                headers['Authorization'] = f'Bearer {self.cfg.lm_api_key}'
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(base + '/api/v0/models', headers=headers)
                response.raise_for_status()
                data = response.json().get('data', [])
            for item in data:
                if item.get('id') == model_id:
                    loaded_length = item.get('loaded_context_length')
                    if item.get('state') == 'loaded' and loaded_length:
                        return {
                            'model_context_limit': int(loaded_length),
                            'model_max_context_limit': item.get('max_context_length'),
                            'model_state': item.get('state'),
                            'context_limit_source': 'LM Studio REST loaded_context_length',
                        }
                    return {
                        'model_context_limit': None,
                        'model_max_context_limit': item.get('max_context_length'),
                        'model_state': item.get('state'),
                        'context_limit_source': 'Активный лимит неизвестен; используется CONTEXT_LIMIT из .env',
                    }
        except Exception:
            pass
        return {'model_context_limit': None, 'model_state': None,
                'context_limit_source': 'CONTEXT_LIMIT из .env (резервный предел Workbench)'}

    async def effective_context_limit(self, model_id):
        configured = max(8192, int(getattr(self, 'runtime_settings', {}).get('context_limit', self.cfg.context_limit) or 50000))
        sdk_limit = None
        try:
            sdk_limit = await asyncio.to_thread(self.token_counter.context_length, model_id)
        except Exception:
            pass
        metadata = await self.model_context_metadata(model_id) if not sdk_limit else {}
        model_limit = sdk_limit or metadata.get('model_context_limit')
        effective = min(int(model_limit), configured) if model_limit else configured
        source = 'Текущий лимит LM Studio' if sdk_limit else (
            metadata.get('context_limit_source') if model_limit else 'CONTEXT_LIMIT из .env'
        )
        return effective, model_limit, source

    def _context_messages(self, history, memory, project_root=None, project_memory='', task_memory=''):
        """Build a chat sequence compatible with LM Studio chat templates.

        Many GGUF chat templates accept exactly one leading system message.
        Older Workbench versions emitted consecutive (and sometimes mid-history)
        system messages for project/task/branch memory and tool results. LM Studio
        rejects those prompts with HTTP 400; its SDK tokenizer reports the same
        issue as 'Multi-part or consecutive system prompts are not supported'.
        Keep one system message and represent persisted tool results as clearly
        labelled user-context messages so their chronology remains intact.
        """
        root = project_root or self.project.root
        project_row = None
        try:
            project_row = next((x for x in self.store.projects() if str(x.get('root')) == str(root)), None)
        except Exception:
            pass
        autonomy = self.store.get_project_settings(project_row['id'])['autonomy'] if project_row else 'analysis'
        autonomy_note = {
            'analysis': 'УРОВЕНЬ АВТОНОМНОСТИ: ANALYSIS. Самостоятельно читай, ищи и запускай разрешённые безопасные проверки. Изменения файлов и произвольные команды требуют подтверждения.',
            'development': 'УРОВЕНЬ АВТОНОМНОСТИ: DEVELOPMENT. Самостоятельно анализируй, изменяй файлы проекта с резервной копией и запускай типовые тесты. Произвольный PowerShell, удаление и системные действия требуют подтверждения.',
            'full': 'УРОВЕНЬ АВТОНОМНОСТИ: FULL. Самостоятельно выполняй цикл разработки и типовые проверки; изменения в пределах проекта разрешены. Произвольный PowerShell, удаление, установка пакетов, системные и сетевые действия всё равно требуют подтверждения.'
        }.get(autonomy, '')
        system_parts = [SYSTEM + f'\nPROJECT_ROOT: {root}\n{autonomy_note}']
        if project_memory:
            system_parts.append('ПОСТОЯННАЯ ПАМЯТЬ ПРОЕКТА. Подтверждённые общие факты, архитектура и ограничения:\n' + project_memory)
        if task_memory:
            system_parts.append('ПАМЯТЬ ЗАДАЧИ. Цель, состояние, ограничения и следующие шаги этой задачи:\n' + task_memory)
        if memory:
            system_parts.append('СОХРАНЁННАЯ ПАМЯТЬ ВЕТКИ. Это сжатое состояние предыдущей работы; используй его вместо повторного изучения старой истории. Новые сообщения имеют приоритет.\n' + memory)
        result = [{'role': 'system', 'content': '\n\n'.join(system_parts)}]
        for m in history:
            role, content = m.get('role'), m.get('content') or ''
            if not content:
                continue
            if role in ('user', 'assistant'):
                result.append({'role': role, 'content': content})
            elif role == 'tool':
                result.append({'role': 'user', 'content': '[ПОДТВЕРЖДЁННЫЙ РЕЗУЛЬТАТ ИНСТРУМЕНТА ИЗ ПРЕДЫДУЩЕЙ ИСТОРИИ]\n' + content})
        return result

    async def _summarize(self, model, old_messages, previous_memory, bid=None, turn_message_id=None):
        transcript = []
        if previous_memory:
            transcript.append('ПРЕДЫДУЩАЯ ПАМЯТЬ:\n' + previous_memory)
        for m in old_messages:
            role = {'user': 'Пользователь', 'assistant': 'Модель', 'tool': 'Результат инструмента'}.get(m.get('role'), m.get('role'))
            content = (m.get('content') or '')[:5000]
            transcript.append(f'{role}: {content}')
        prompt = '''Сформируй компактную долговременную память инженерной задачи на русском языке (ориентир 600-900 токенов). Обязательно сохрани: цель; подтверждённую архитектуру; точные пути и имена функций; решения и причины; фактические результаты инструментов/проверок; что изменено и что не изменено; ошибки и ограничения; следующий конкретный шаг. Удали повторы и разговорный шум. Не превращай гипотезы в факты. Если MCP отказал в чтении файла, сохрани точную причину и не заявляй, что файл прочитан.'''
        response = await self.llm.chat.completions.create(model=model, messages=[{'role': 'system', 'content': prompt}, {'role': 'user', 'content': '\n\n'.join(transcript)}], temperature=0.1)
        usage = getattr(response, 'usage', None)
        prompt_tokens = getattr(usage, 'prompt_tokens', None) if usage else None
        completion_tokens = getattr(usage, 'completion_tokens', None) if usage else None
        if bid is not None:
            self.store.record_llm_call(bid, turn_message_id, model, 'memory_summary', prompt_tokens, completion_tokens)
        answer = response.choices[0].message.content or previous_memory or ''
        return answer, int(prompt_tokens or 0), int(completion_tokens or 0)

    def preview_context(self, bid, user_text, history, attachment_ids=None, model_id=None, model_metadata=None):
        """Estimate the next prompt without mutating history or memory."""
        project_row = self.store.project_for_branch(bid)
        project_root = project_row['root'] if project_row else str(self.project.root)
        project_memory_row = self.store.get_project_memory(project_row['id']) if project_row else None
        project_memory = project_memory_row['summary'] if project_memory_row else ''
        task_row = self.store.task_for_branch(bid)
        task_memory = task_row['summary'] if task_row else ''
        memory_row = self.store.get_memory(bid)
        memory = memory_row['summary'] if memory_row else ''
        through_id = int(memory_row['through_message_id']) if memory_row else 0
        fresh = [m for m in history if int(m.get('id', 0)) > through_id]
        messages = self._context_messages(fresh, memory, project_root, project_memory, task_memory)
        _, attachment_context = self.store.attachment_payload(attachment_ids or [], project_row['id'] if project_row else 0, task_row['id'] if task_row else 0, bid)
        messages.append({'role': 'user', 'content': user_text + attachment_context})
        tools = self.specs()
        metrics = self.prompt_metrics(messages, tools, model_id)
        sdk_limit = metrics.get('model_context_limit')
        metadata_limit = (model_metadata or {}).get('model_context_limit')
        model_limit = sdk_limit or metadata_limit
        configured_limit = max(8192, int(getattr(self, 'runtime_settings', {}).get('context_limit', self.cfg.context_limit) or 50000))
        limit = min(int(model_limit), configured_limit) if model_limit else configured_limit
        prompt_tokens = int(metrics['estimated_prompt_tokens'])
        output_reserve = max(512, min(2048, round(limit * 0.05)))
        percent = round((prompt_tokens + output_reserve) / limit * 100, 1) if limit else 0
        if percent >= 85:
            level, message = 'critical', 'Контекст достиг 85%. Рекомендуется продолжить работу в новой задаче; оценка предварительная.'
        elif percent >= 75:
            level, message = 'high', 'Контекст близок к рабочему пределу. Рекомендуется подготовить перенос в новую задачу.'
        elif percent >= 60:
            level, message = 'warning', 'Контекст растёт. Workbench автоматически сжимает старую историю при приближении к рабочему бюджету около 62%.'
        else:
            level, message = 'ok', 'Запас контекста достаточный.'
        return {
            **metrics,
            'estimated_prompt_tokens': prompt_tokens,
            'context_limit': limit,
            'model_context_limit': model_limit,
            'model_max_context_limit': (model_metadata or {}).get('model_max_context_limit'),
            'workbench_context_limit': configured_limit,
            'limit_source': 'Текущий лимит LM Studio' if sdk_limit else (model_metadata or {}).get('context_limit_source', 'CONTEXT_LIMIT из .env'),
            'output_reserve_tokens': output_reserve,
            'remaining_estimate': max(0, limit - prompt_tokens - output_reserve),
            'percent': min(100, percent),
            'level': level,
            'message': message,
            'memory_active': bool(memory),
        }

    async def _prepare_context(self, bid, history, model, tools, turn_message_id=None):
        project_row = self.store.project_for_branch(bid)
        project_root = project_row['root'] if project_row else str(self.project.root)
        project_memory_row = self.store.get_project_memory(project_row['id']) if project_row else None
        project_memory = project_memory_row['summary'] if project_memory_row else ''
        task_row = self.store.task_for_branch(bid)
        task_memory = task_row['summary'] if task_row else ''
        memory_row = self.store.get_memory(bid)
        memory = memory_row['summary'] if memory_row else ''
        through_id = int(memory_row['through_message_id']) if memory_row else 0
        fresh = [m for m in history if int(m.get('id', 0)) > through_id]
        limit, _, _ = await self.effective_context_limit(model)
        # Keep the working prompt well below the actually loaded model context.
        budget = int(limit * 0.62)
        summary_usage = [0, 0]
        if len(fresh) >= 14 or self.prompt_metrics(self._context_messages(fresh, memory, project_root, project_memory, task_memory), tools, model)['estimated_prompt_tokens'] > budget:
            keep = 8
            old = fresh[:-keep] if len(fresh) > keep else []
            if old:
                new_memory, p, c = await self._summarize(model, old, memory, bid, turn_message_id)
                if new_memory.strip():
                    memory = new_memory
                    through_id = int(old[-1].get('id', through_id) or through_id)
                    self.store.save_memory(bid, memory, through_id)
                summary_usage = [p, c]
                fresh = fresh[len(old):]
        messages = self._context_messages(fresh, memory, project_root, project_memory, task_memory)
        current = (await asyncio.to_thread(self.prompt_metrics, messages, tools, model))['estimated_prompt_tokens']
        # Deterministic last-resort trim: keep the newest conversational turns, never silently drop current user text.
        while current > budget and len(fresh) > 4:
            drop = max(1, len(fresh) - 6)
            old, fresh = fresh[:drop], fresh[drop:]
            new_memory, p, c = await self._summarize(model, old, memory, bid, turn_message_id)
            summary_usage[0] += p; summary_usage[1] += c
            if new_memory.strip():
                memory = new_memory
                through_id = int(old[-1].get('id', through_id) or through_id)
                self.store.save_memory(bid, memory, through_id)
            messages = self._context_messages(fresh, memory, project_root, project_memory, task_memory)
            current = (await asyncio.to_thread(self.prompt_metrics, messages, tools, model))['estimated_prompt_tokens']
        return messages, {'estimated_prompt_tokens': current, 'context_limit': limit, 'soft_limit': budget, 'summary_prompt_tokens': summary_usage[0], 'summary_completion_tokens': summary_usage[1], 'memory_active': bool(memory), 'memory_updated': bool(summary_usage[0] or summary_usage[1])}

    async def _compact_runtime(self, msgs, tools, model, bid, memory, turn_message_id=None):
        limit, _, _ = await self.effective_context_limit(model)
        budget = int(limit * 0.68)
        current = (await asyncio.to_thread(self.prompt_metrics, msgs, tools, model))['estimated_prompt_tokens']
        if current <= budget:
            return msgs, memory, 0, 0
        # Keep system instructions, compress the in-flight transcript into plain factual notes,
        # and preserve the latest user request verbatim. This avoids broken tool_call/tool_result pairs.
        system = [m for m in msgs if m.get('role') == 'system']
        non_system = [m for m in msgs if m.get('role') != 'system']
        if len(non_system) <= 2:
            return msgs, memory, 0, 0

        # Tool execution normally leaves one or more role=tool messages at the
        # end of the conversation.  The previous implementation preserved the
        # user message only when it was the *last* non-system message.  After
        # any successful tool call that condition is false, so compaction
        # silently removed every user message.  LM Studio's chat template then
        # failed with: "No user query found in messages."
        #
        # Preserve the newest user turn regardless of later assistant/tool
        # messages.  Everything else remains in the summary transcript, so
        # tool results are not lost when the runtime context is compacted.
        current_user_index = next(
            (i for i in range(len(non_system) - 1, -1, -1)
             if non_system[i].get('role') == 'user'
             and str(non_system[i].get('content') or '').strip()),
            None,
        )
        if current_user_index is None:
            logger.error(
                'RUNTIME_COMPACTION_NO_USER_MESSAGE branch_id=%s; preserving original messages',
                bid,
            )
            return msgs, memory, 0, 0

        current_user = non_system[current_user_index]
        transcript = non_system[:current_user_index] + non_system[current_user_index + 1:]
        if not transcript:
            return msgs, memory, 0, 0
        pseudo = []
        for m in transcript:
            content = m.get('content') or ''
            if m.get('tool_calls'):
                calls = '; '.join(x.get('function', {}).get('name', 'tool') for x in m['tool_calls'])
                content = (content + '\nВызовы инструментов: ' + calls).strip()
            pseudo.append({'role': 'tool' if m.get('role') == 'tool' else m.get('role', 'assistant'), 'content': content})
        new_memory, p, c = await self._summarize(model, pseudo, memory, bid, turn_message_id)
        compact = system + ([{'role': 'system', 'content': 'ПАМЯТЬ ТЕКУЩЕГО ЗАПРОСА (сводка старых шагов):\n' + new_memory}] if new_memory else [])
        compact.append({'role': 'assistant', 'content': 'Краткая история предыдущих шагов и результатов инструментов сохранена в памяти выше. Продолжай с последнего незавершённого действия.'})
        if current_user:
            compact.append(current_user)
        return compact, new_memory or memory, p, c

    async def chat(self, bid, user_text, history, attachment_ids=None):
        self._set_activity(bid,'preparing','Подготовка контекста')
        self.runtime_settings = self.store.get_app_settings()
        project_row = self.store.project_for_branch(bid)
        task_row = self.store.task_for_branch(bid)
        project_catalog = self.store.projects() if hasattr(self.store, 'projects') else []
        authorized_external_roots = _explicit_external_project_roots(
            user_text, project_catalog, project_row.get('id') if project_row else None)
        allowed_ids, attachment_context = self.store.attachment_payload(
            attachment_ids or [],
            project_row['id'] if project_row else 0,
            task_row['id'] if task_row else 0,
            bid,
        )
        user_message_id = self.store.add_message(bid, 'user', user_text)
        if allowed_ids:
            self.store.link_message_attachments(user_message_id, allowed_ids)
        model = self.cfg.lm_model
        if model == 'local-model':
            available = await self.models()
            if available and not available[0].startswith('Ошибка'):
                model = available[0]
        self.last_model = model
        tools = self.specs()
        msgs, context_info = await self._prepare_context(bid, history, model, tools, user_message_id)
        model_user_text = user_text + (attachment_context if attachment_context else '')
        msgs.append({'role': 'user', 'content': model_user_text})
        total_prompt = context_info['summary_prompt_tokens']
        total_completion = context_info['summary_completion_tokens']
        pending = []
        max_rounds = max(1, min(32, int(self.runtime_settings.get('max_tool_rounds', self.cfg.max_tool_rounds or 16))))
        max_tool_calls = max(1, min(64, int(self.runtime_settings.get('max_tool_calls', 24))))
        tool_calls_count = 0
        request_timeout = max(30, min(600, int(self.runtime_settings.get('request_timeout', 180))))
        temperature = max(0.0, min(1.0, float(self.runtime_settings.get('temperature', 0.2))))
        llm = self.llm.with_options(timeout=request_timeout)
        seen_calls = {}
        call_results = {}
        failed_calls = set()
        tool_rounds = 0
        last_prompt = 0
        blocked_external_root = None
        empty_response_retry_used = False
        last_adapter_error = None
        for round_no in range(max_rounds):
            self._set_activity(bid,'model_generation',f'Раунд модели {round_no+1}')
            msgs, runtime_memory, cp, cc = await self._compact_runtime(msgs, tools, model, bid, '', user_message_id)
            total_prompt += cp; total_completion += cc
            preflight = await asyncio.to_thread(self.prompt_metrics, msgs, tools, model)
            context_info.update(preflight)
            response = await llm.chat.completions.create(model=model, messages=msgs, tools=tools, tool_choice='auto', temperature=temperature)
            usage = getattr(response, 'usage', None)
            prompt_value = getattr(usage, 'prompt_tokens', None) if usage else None
            completion_value = getattr(usage, 'completion_tokens', None) if usage else None
            self.store.record_llm_call(bid, user_message_id, model,
                                       'tool_call' if (response.choices[0].message.tool_calls or '<tool_call' in (response.choices[0].message.content or '').lower()) else 'chat',
                                       prompt_value, completion_value)
            if usage:
                last_prompt = int(prompt_value or 0)
                total_prompt += int(prompt_value or 0)
                total_completion += int(completion_value or 0)
                context_info['last_actual_prompt_tokens'] = prompt_value
                context_info['last_actual_completion_tokens'] = completion_value
            msg = response.choices[0].message
            tool_calls, text_call_detected, adapter_error = extract_tool_calls(msg, tools)
            last_adapter_error = adapter_error if text_call_detected else None
            if text_call_detected:
                if adapter_error:
                    logger.warning('TOOL_CALL_ADAPTER_REJECTED branch_id=%s accepted=%s error_present=1',
                                   bid, len(tool_calls))
                else:
                    logger.info('TOOL_CALL_ADAPTER_OK branch_id=%s accepted=%s', bid, len(tool_calls))
            assistant_content = visible_response_text(msg, '')
            if text_call_detected:
                assistant_content = strip_text_tool_call_markup(assistant_content)
            assistant_msg = {'role': 'assistant', 'content': assistant_content}
            if tool_calls:
                assistant_msg['tool_calls'] = [{'id': tc.id, 'type': 'function', 'function': {'name': tc.function.name, 'arguments': tc.function.arguments}} for tc in tool_calls]
            msgs.append(assistant_msg)
            if text_call_detected and adapter_error and not tool_calls:
                msgs.append({'role':'user','content':'[ОШИБКА ФОРМАТА ВЫЗОВА ИНСТРУМЕНТА] '+adapter_error+' Повтори только отклонённые вызовы в корректном формате. Не выводи транспортную разметку как ответ.'})
                tool_rounds += 1
                continue
            if not tool_calls:
                visible_text = visible_response_text(msg, '')
                if not visible_text.strip() and not empty_response_retry_used and round_no + 1 < max_rounds:
                    empty_response_retry_used = True
                    msgs.append({'role': 'user', 'content': (
                        '[WORKBENCH: ПУСТОЙ ВИДИМЫЙ ОТВЕТ] Предыдущая генерация завершилась без пользовательского текста. '
                        'Продолжи задачу и верни обычный ответ. Если последний результат read_project_file содержит '
                        'INCOMPLETE/NEXT_START_LINE, сначала прочитай следующий диапазон того же файла. '
                        'Не повторяй уже выполненные инструменты и не раскрывай внутренние рассуждения.'
                    )})
                    self._set_activity(bid, 'model_generation', 'Повторная попытка после пустого ответа')
                    continue
                answer = visible_text or empty_response_notice(msg, 'основного ответа')
                self.store.add_message(bid, 'assistant', answer, total_prompt, total_completion, usage_message_id=user_message_id)
                return {'answer': answer, 'usage': {'prompt_tokens': total_prompt, 'completion_tokens': total_completion, 'last_prompt_tokens': last_prompt}, 'model': model, 'pending': self.store.pending(bid), 'context': context_info, 'tool_rounds': tool_rounds, 'tool_calls': tool_calls_count, 'max_tool_calls': max_tool_calls, 'limit_reached': False}

            stop_reason = None
            for tc in tool_calls:
                name = tc.function.name
                self._set_activity(bid,'tool_running',name)
                if stop_reason:
                    blocked_text = 'Вызов не выполнен: предыдущий инструмент уже сообщил об ошибке. Не повторяй этот шаг.'
                    msgs.append({'role': 'tool', 'tool_call_id': tc.id, 'content': blocked_text})
                    event = {'version': 1, 'name': tc.function.name, 'arguments': {}, 'status': 'blocked',
                             'duration_ms': 0, 'result_preview': blocked_text, 'tool_call_id': tc.id}
                    self.store.add_message(bid, 'tool', blocked_text, metadata=event)
                    tool_rounds += 1
                    continue
                tool_calls_count += 1
                if tool_calls_count > max_tool_calls:
                    result_text = f'Лимит вызовов инструментов на один запрос достигнут ({max_tool_calls}). Продолжение остановлено настройкой Workbench.'
                    tool_status = 'blocked'
                    stop_reason = 'Достигнут лимит вызовов инструментов на один запрос. Подведи итог по уже полученным результатам и укажи, что осталось.'
                    event = {'version': 1, 'name': name, 'arguments': {}, 'status': 'blocked',
                             'duration_ms': 0, 'result_preview': result_text[:320], 'tool_call_id': tc.id}
                    msgs.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result_text})
                    self.store.add_message(bid, 'tool', result_text, metadata=event)
                    tool_rounds += 1
                    continue
                try:
                    args = json.loads(tc.function.arguments or '{}')
                    if not isinstance(args, dict): args = {'_raw_arguments': args}
                except Exception as exc:
                    args = {}
                    result_text = f'Некорректные аргументы вызова: {type(exc).__name__}: {exc}'
                    tool_status = 'error'
                else:
                    result_text = ''
                    tool_status = 'completed'
                sandbox_revision = 0
                if name in {'sandbox_list_files','sandbox_read_file','sandbox_run_check','sandbox_diff'}:
                    try:
                        from .sandbox import SandboxManager
                        project_root = project_row.get('root') if project_row else None
                        if project_root and args.get('sandbox_id'):
                            sandbox_revision = SandboxManager(__import__('pathlib').Path(project_root)).revision(args['sandbox_id'])
                    except Exception:
                        sandbox_revision = 0
                fingerprint = tool_call_fingerprint(name, args, sandbox_revision)
                seen_calls[fingerprint] = seen_calls.get(fingerprint, 0) + 1
                started = time.perf_counter()
                if seen_calls[fingerprint] > 1:
                    if fingerprint in call_results:
                        result_text = call_results[fingerprint]
                        tool_status = 'reused'
                    else:
                        result_text = f'Повторный вызов {name} остановлен: предыдущий результат отсутствует.'
                        tool_status = 'blocked'
                        failed_calls.add(fingerprint)
                elif tool_status != 'error':
                    try:
                        if name in {'list_registered_project_files', 'read_registered_project_file'}:
                            result = await self.tool(name, args, bid, authorized_external_roots=authorized_external_roots)
                        else:
                            result = await self.tool(name, args, bid)
                        result_text = str(result)
                        call_results[fingerprint] = result_text
                    except Exception as e:
                        result_text = f'Ошибка инструмента: {type(e).__name__}: {e}'
                        tool_status = 'error'
                    if ('Файл не найден или путь находится вне разрешённых папок' in result_text
                        or 'Запрещён выход за пределы' in result_text
                        or 'Доступ к потенциально секретному файлу запрещён' in result_text
                        or 'Доступ к другому проекту не разрешён' in result_text
                        or 'не зарегистрирован как активный проект Workbench' in result_text):
                        tool_status = 'blocked'
                        failed_calls.add(fingerprint)
                        if name in {'list_registered_project_files', 'read_registered_project_file'} and 'Доступ к другому проекту не разрешён' in result_text:
                            blocked_external_root = str(args.get('root') or '').strip() or None
                        stop_reason = 'Инструмент отказал в доступе к указанному пути. Повторять этот вызов нельзя.'
                duration_ms = round((time.perf_counter() - started) * 1000)
                if len(result_text) > 7000:
                    result_text = result_text[:5500] + '\n\n[Фрагмент сокращён Workbench. Запроси конкретный диапазон строк, если нужен полный текст.]'
                # Store a safe, inspectable argument snapshot. File contents and credentials are never copied into the UI event log.
                safe_args = {}
                for key, value in args.items():
                    if re.search(r'password|secret|token|api.?key|authorization|credential', str(key), re.I):
                        safe_args[key] = '[СКРЫТО]'
                    elif key in {'content'}:
                        safe_args[key] = f'[Содержимое не показывается; символов: {len(str(value))}]'
                    elif isinstance(value, str):
                        safe_args[key] = re.sub(r'(?i)(password|token|api[_-]?key|secret)(\s*[=:]\s*)[^\s,;]+', r'\1\2[СКРЫТО]', value[:4000])
                    else:
                        safe_args[key] = value
                event = {'version': 1, 'name': name, 'arguments': safe_args, 'status': tool_status,
                         'duration_ms': duration_ms, 'result_preview': result_text[:320], 'tool_call_id': tc.id}
                queued_match = re.search(r'(?:поставлена на подтверждение|поставлена в очередь на подтверждение)[^\n]*ID=(\d+)', result_text, re.I)
                input_match = re.search(r'Запрос (?:защищённого секрета|пользовательского ввода) создан\. ID=(\d+)', result_text, re.I)
                if input_match and name in {'request_user_input', 'request_user_secret'}:
                    self.store.set_input_request_context(int(input_match.group(1)), msgs, tc.id, model, user_message_id)
                    self._set_activity(bid,'waiting_input',f'Запрос ввода #{input_match.group(1)}')
                if queued_match and name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'}:
                    self._set_activity(bid,'waiting_approval',f'Команда #{queued_match.group(1)}')
                    # Preserve the exact OpenAI-compatible conversation prefix, including
                    # the assistant tool_calls object, so the tool result can be supplied
                    # to the original tool_call_id after explicit approval.
                    self.store.set_execution_context(int(queued_match.group(1)), msgs, tc.id, model, user_message_id)
                msgs.append({'role': 'tool', 'tool_call_id': tc.id, 'content': result_text})
                self.store.add_message(bid, 'tool', result_text, metadata=event)
                tool_rounds += 1
                if name == 'write_project_file':
                    pending = self.store.pending(bid)
                # Local PowerShell and SSH commands are approval-gated asynchronous
                # operations. Stop this model turn immediately after queueing any of
                # them. Continuing the LLM loop can overwrite waiting_approval with
                # model_generation and leave the UI's Computer button in its busy state.
                if name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'} and queued_match:
                    if name == 'execute_powershell':
                        stop_reason = ('PowerShell-команда поставлена в очередь и ожидает явного подтверждения пользователя. '
                                       'Не выполняй её другим способом и не утверждай, что она уже запущена. Сообщи ID запроса.')
                    else:
                        stop_reason = ('SSH-команда поставлена в очередь и ожидает явного подтверждения пользователя. '
                                       'Не создавай обход и не утверждай, что подключение уже состоялось. Сообщи ID запроса.')
                if name in {'request_user_input', 'request_user_secret'} and input_match:
                    stop_reason = ('Ожидается ввод пользователя в панели Workbench. Не запрашивай значение в обычном чате '
                                   'и не продолжай задачу до получения ответа. Сообщи ID запроса.')
            if text_call_detected and adapter_error and tool_calls and not stop_reason:
                msgs.append({'role': 'user', 'content': (
                    '[ЧАСТИЧНЫЙ РЕЗУЛЬТАТ TOOL-CALL ADAPTER] Выполнены только корректные вызовы инструментов. '
                    + adapter_error + ' Исправь и повтори только отклонённые вызовы; не повторяй уже выполненные.'
                )})
                tool_rounds += 1
            if stop_reason:
                # Waiting for user approval/input is a workflow state, not a reason
                # to launch another model generation just to narrate the wait.
                if 'ожидает подтверждения пользователя' in stop_reason.lower():
                    answer='Команда подготовлена и ожидает подтверждения в панели выполнения. До подтверждения команда не запускается.'
                    self._set_activity(bid,'waiting_approval','Ожидается подтверждение команды')
                elif 'ожидается ввод пользователя' in stop_reason.lower():
                    answer='Ожидается ответ в панели защищённого ввода. После отправки Workbench продолжит исходный вызов инструмента.'
                    self._set_activity(bid,'waiting_input','Ожидается защищённый ввод')
                else:
                    msgs.append({'role':'user','content':(
                        '[ИНСТРУКЦИЯ WORKBENCH ПОСЛЕ ОСТАНОВКИ ИНСТРУМЕНТА]\n'
                        + stop_reason
                        + ' Это заключительный запрос БЕЗ доступных инструментов. Не выводи <tool_call>, <function> или <parameter> и не изображай невыполненные вызовы. '
                        'Сформулируй промежуточный результат и укажи, что именно недоступно.'
                    )})
                    self._set_activity(bid,'model_generation','Формирование промежуточного итога')
                    try:
                        final=await llm.chat.completions.create(model=model,messages=msgs,temperature=temperature)
                        u=getattr(final,'usage',None);up=getattr(u,'prompt_tokens',None) if u else None;uc=getattr(u,'completion_tokens',None) if u else None
                        self.store.record_llm_call(bid,user_message_id,model,'tool_error_final',up,uc)
                        if u:
                            total_prompt+=int(up or 0);total_completion+=int(uc or 0)
                            context_info['last_actual_prompt_tokens']=up;context_info['last_actual_completion_tokens']=uc
                        final_msg = final.choices[0].message
                        answer=visible_response_text(final_msg, stop_reason)
                        if contains_tool_call_markup(answer):
                            logger.warning('TOOL_CALL_FINAL_TEXT_SUPPRESSED branch_id=%s external_root_denied=%s',
                                           bid, bool(blocked_external_root))
                            if blocked_external_root:
                                answer = (
                                    f'Workbench остановил чтение внешнего проекта «{blocked_external_root}»: '
                                    'его точный корневой путь не был явно указан в текущем сообщении пользователя. '
                                    'Путь, предложенный самой моделью, не является разрешением на доступ. '
                                    'Чтобы продолжить, отправьте новое сообщение и включите в него полный корневой путь проекта. '
                                    'После явного указания будет разрешено только чтение.'
                                )
                            else:
                                answer = (
                                    'Workbench остановил выполнение после отказа инструмента. '
                                    + stop_reason + ' Финальный ответ модели содержал неисполненные служебные вызовы; '
                                    'они отброшены и не запускались.'
                                )
                    except Exception: answer=stop_reason+' Результаты предыдущих инструментов сохранены в истории.'
                self.store.add_message(bid,'assistant',answer,total_prompt,total_completion,usage_message_id=user_message_id)
                return {'answer':answer,'usage':{'prompt_tokens':total_prompt,'completion_tokens':total_completion,'last_prompt_tokens':last_prompt},'model':model,'pending':self.store.pending(bid),'context':context_info,'tool_rounds':tool_rounds,'tool_calls':tool_calls_count,'max_tool_calls':max_tool_calls,'limit_reached':False,'tool_error':True}

        if last_adapter_error:
            answer = ('Workbench не смог принять один или несколько вызовов инструментов после повторной попытки. '
                      + last_adapter_error + ' Корректные вызовы, принятые ранее, уже выполнены; отклонённые не запускались.')
            self.store.add_message(bid, 'assistant', answer, total_prompt, total_completion, usage_message_id=user_message_id,
                                   metadata={'kind': 'tool_call_adapter_error', 'error': last_adapter_error[:1200]})
            return {'answer': answer, 'usage': {'prompt_tokens': total_prompt, 'completion_tokens': total_completion, 'last_prompt_tokens': last_prompt}, 'model': model, 'pending': pending or self.store.pending(bid), 'context': context_info, 'tool_rounds': tool_rounds, 'tool_calls': tool_calls_count, 'max_tool_calls': max_tool_calls, 'limit_reached': True, 'tool_error': True, 'adapter_error': last_adapter_error}
        answer = ('Достигнут предел инструментальных шагов за один запрос. Уже полученные результаты сохранены. '
                  'Сформируй следующий запрос с конкретным оставшимся этапом; повторять выполненный поиск не нужно.')
        self.store.add_message(bid, 'assistant', answer, total_prompt, total_completion, usage_message_id=user_message_id)
        return {'answer': answer, 'usage': {'prompt_tokens': total_prompt, 'completion_tokens': total_completion, 'last_prompt_tokens': last_prompt}, 'model': model, 'pending': pending or self.store.pending(bid), 'context': context_info, 'tool_rounds': tool_rounds, 'tool_calls': tool_calls_count, 'max_tool_calls': max_tool_calls, 'limit_reached': True}

    async def resume_execution(self, execution_id: int, result_text: str):
        """Resume an approved/rejected execution using its original tool-call context."""
        item = self.store.execution_by_id(execution_id)
        if not item:
            return {'resumed': False, 'reason': 'Команда не найдена.'}
        if not item.get('context_json') or not item.get('tool_call_id'):
            self.store.mark_execution_resumed(execution_id, 'failed')
            return {'resumed': False, 'reason': 'Для этой команды нет сохранённого контекста продолжения.'}
        if item.get('resume_status') == 'completed':
            return {'resumed': False, 'reason': 'Этот результат уже передан модели.'}
        if not self.store.claim_execution_resume(execution_id):
            return {'resumed': False, 'reason': 'Продолжение уже выполняется или было обработано.'}
        return await self._resume_saved_tool_context(
            item['context_json'], item['tool_call_id'], item.get('model'), item['branch_id'],
            item.get('user_message_id'), result_text, 'execution', execution_id)

    async def resume_input_request(self, request_id: int, result_text: str | None = None):
        """Resume the model after a normal or secret user-input form is submitted."""
        item = self.store.input_request(request_id)
        if not item:
            return {'resumed': False, 'reason': 'Запрос ввода не найден.'}
        if not item.get('context_json') or not item.get('tool_call_id'):
            self.store.mark_input_request_resumed(request_id, 'failed')
            return {'resumed': False, 'reason': 'Для запроса ввода нет сохранённого контекста продолжения.'}
        if item.get('resume_status') == 'completed':
            return {'resumed': False, 'reason': 'Этот ответ уже передан модели.'}
        if not self.store.claim_input_request_resume(request_id):
            return {'resumed': False, 'reason': 'Продолжение уже выполняется или было обработано.'}
        if result_text is None:
            if item['input_type'] == 'secret' and not self.credentials.exists(item.get('credential_ref', '')):
                result_text = ('Временный секрет недоступен после перезапуска Workbench. Не используй старую ссылку; '
                               'повтори запрос через request_user_secret и дождись нового ввода.')
            elif item['input_type'] == 'secret':
                result_text = ('Пользователь передал секрет в CredentialBroker. Значение недоступно модели. '
                               f"Используй только эту ссылку в доверенном инструменте: credential_ref={item.get('credential_ref', '')}")
            else:
                result_text = item.get('result_text', '')
        self.store.add_message(int(item['branch_id']), 'tool', result_text,
                               metadata={'kind':'user_input_result', 'input_request_id':request_id,
                                         'input_type':item['input_type'], 'secret_value_stored':item['input_type'] == 'secret'})
        return await self._resume_saved_tool_context(
            item['context_json'], item['tool_call_id'], item.get('model'), item['branch_id'],
            item.get('user_message_id'), result_text, 'input', request_id)

    def _mark_resume(self, kind, resume_id, status):
        if kind == 'execution':
            self.store.mark_execution_resumed(resume_id, status)
        else:
            self.store.mark_input_request_resumed(resume_id, status)

    async def _resume_saved_tool_context(self, context_json, tool_call_id, saved_model, branch_id,
                                         user_message_id, result_text, resume_kind, resume_id):
        try:
            msgs = json.loads(context_json)
            if not isinstance(msgs, list):
                raise ValueError('Некорректный снимок контекста')
            # The saved prefix must end with the assistant message that declared this call.
            if not any(tc.get('id') == tool_call_id
                       for message in msgs if isinstance(message, dict)
                       for tc in (message.get('tool_calls') or [])):
                raise ValueError('Исходный tool_call_id отсутствует в снимке контекста')
        except Exception as exc:
            self._mark_resume(resume_kind, resume_id, 'failed')
            return {'resumed': False, 'reason': f'Не удалось восстановить контекст: {type(exc).__name__}: {exc}'}

        bid = int(branch_id)
        # Normalize legacy snapshots that were saved before batch placeholders existed.
        if not any(isinstance(m, dict) and m.get('role') == 'tool'
                   and m.get('tool_call_id') == tool_call_id
                   and m.get('content') == self.store.PENDING_TOOL_RESULT for m in msgs):
            try:
                msgs = self.store._resume_context_snapshot(msgs, tool_call_id)
            except Exception:
                pass
        tool_result = f'РЕЗУЛЬТАТ ОЖИДАВШЕГО ВВОДА/ВЫПОЛНЕНИЯ (request_id={resume_id})\n{result_text}'
        replaced = False
        for saved_message in msgs:
            if (isinstance(saved_message, dict) and saved_message.get('role') == 'tool'
                    and saved_message.get('tool_call_id') == tool_call_id
                    and saved_message.get('content') == self.store.PENDING_TOOL_RESULT):
                saved_message['content'] = tool_result
                replaced = True
                break
        if not replaced:
            # Backward compatibility with snapshots created before placeholder batches.
            msgs.append({'role': 'tool', 'tool_call_id': tool_call_id, 'content': tool_result})
        model = saved_model or self.cfg.lm_model
        settings = self.store.get_app_settings()
        max_rounds = max(1, min(16, int(settings.get('max_tool_rounds', 8))))
        max_calls = max(1, min(32, int(settings.get('max_tool_calls', 16))))
        temperature = max(0.0, min(1.0, float(settings.get('temperature', 0.2))))
        llm = self.llm.with_options(timeout=max(30, min(600, int(settings.get('request_timeout', 180)))))
        total_prompt = total_completion = 0
        tool_count = 0
        tools = self.specs()
        try:
            for resume_round in range(max_rounds):
                self._set_activity(bid,'model_generation',f'Продолжение · раунд {resume_round+1}')
                msgs, _runtime_memory, cp, cc = await self._compact_runtime(
                    msgs, tools, model, bid, '', user_message_id)
                total_prompt += int(cp or 0)
                total_completion += int(cc or 0)
                response = await llm.chat.completions.create(model=model, messages=msgs, tools=tools,
                                                             tool_choice='auto', temperature=temperature)
                usage = getattr(response, 'usage', None)
                up = getattr(usage, 'prompt_tokens', None) if usage else None
                uc = getattr(usage, 'completion_tokens', None) if usage else None
                self.store.record_llm_call(bid, user_message_id, model,
                                           'tool_call' if response.choices[0].message.tool_calls else 'chat', up, uc)
                total_prompt += int(up or 0)
                total_completion += int(uc or 0)
                msg = response.choices[0].message
                resume_calls, resume_text_detected, resume_adapter_error = extract_tool_calls(msg, tools)
                if resume_text_detected:
                    if resume_adapter_error:
                        logger.warning('TOOL_CALL_ADAPTER_RESUME_REJECTED branch_id=%s accepted=%s error_present=1',
                                       bid, len(resume_calls))
                    else:
                        logger.info('TOOL_CALL_ADAPTER_RESUME_OK branch_id=%s accepted=%s', bid, len(resume_calls))
                if resume_text_detected and resume_adapter_error and not resume_calls:
                    msgs.append({'role':'assistant','content':strip_text_tool_call_markup(visible_response_text(msg, ''))})
                    msgs.append({'role':'user','content':'[ОШИБКА ФОРМАТА ВЫЗОВА ИНСТРУМЕНТА] '+resume_adapter_error+' Повтори только отклонённые вызовы корректно.'})
                    continue
                if not resume_calls:
                    answer = visible_response_text(msg, empty_response_notice(msg, 'ответа после продолжения'))
                    self.store.add_message(bid, 'assistant', answer, total_prompt, total_completion,
                                           usage_message_id=user_message_id,
                                           metadata={'kind': f'{resume_kind}_resume', 'resume_id': resume_id})
                    self._mark_resume(resume_kind, resume_id, 'completed')
                    return {'resumed': True, 'answer': answer, 'tool_calls': tool_count}

                assistant_content = visible_response_text(msg, '')
                if resume_text_detected:
                    assistant_content = strip_text_tool_call_markup(assistant_content)
                assistant_msg = {'role': 'assistant', 'content': assistant_content, 'tool_calls': [
                    {'id': tc.id, 'type': 'function', 'function': {'name': tc.function.name,
                     'arguments': tc.function.arguments}} for tc in resume_calls]}
                msgs.append(assistant_msg)
                pending_kind = None
                pending_id = None
                for tc in resume_calls:
                    self._set_activity(bid,'tool_running',tc.function.name)
                    tool_count += 1
                    if pending_kind:
                        value = 'Остановлено Workbench: предыдущий инструмент ожидает пользователя. Не выполняй следующие действия до получения ответа.'
                    elif tool_count > max_calls:
                        value = 'Лимит инструментов продолжения достигнут.'
                    else:
                        try:
                            args = json.loads(tc.function.arguments or '{}')
                            if not isinstance(args, dict):
                                args = {}
                            value = str(await self.tool(tc.function.name, args, bid))
                        except Exception as exc:
                            value = f'Ошибка инструмента: {type(exc).__name__}: {exc}'
                        queued = re.search(r'(?:поставлена на подтверждение|поставлена в очередь на подтверждение)[^\n]*ID=(\d+)', value, re.I)
                        input_match = re.search(r'Запрос (?:защищённого секрета|пользовательского ввода) создан\. ID=(\d+)', value, re.I)
                        if queued and tc.function.name in {'ssh_run_command', 'ssh_run_profile_command', 'execute_powershell'}:
                            pending_id = int(queued.group(1))
                            self._set_activity(bid,'waiting_approval',f'Команда #{pending_id}')
                            self.store.set_execution_context(pending_id, msgs, tc.id, model, user_message_id)
                            pending_kind = 'execution'
                        elif input_match and tc.function.name in {'request_user_input', 'request_user_secret'}:
                            pending_id = int(input_match.group(1))
                            self._set_activity(bid,'waiting_input',f'Запрос ввода #{pending_id}')
                            self.store.set_input_request_context(pending_id, msgs, tc.id, model, user_message_id)
                            pending_kind = 'input'
                    msgs.append({'role': 'tool', 'tool_call_id': tc.id, 'content': value})
                    self.store.add_message(bid, 'tool', value, metadata={
                        'version': 1, 'name': tc.function.name,
                        'status': 'pending' if pending_kind else 'completed',
                        'tool_call_id': tc.id,
                        'execution_id': pending_id if pending_kind == 'execution' else None,
                        'input_request_id': pending_id if pending_kind == 'input' else None,
                        'result_preview': value[:320]})
                if resume_text_detected and resume_adapter_error and not pending_kind:
                    msgs.append({'role': 'user', 'content': (
                        '[ЧАСТИЧНЫЙ РЕЗУЛЬТАТ TOOL-CALL ADAPTER] Выполнены только корректные вызовы. '
                        + resume_adapter_error + ' Исправь только отклонённые вызовы; не повторяй выполненные.'
                    )})
                if pending_kind:
                    notice = ('Следующая команда ожидает подтверждения в панели выполнения.' if pending_kind == 'execution'
                              else 'Модель ожидает ответ в панели защищённого ввода пользователя.')
                    self.store.add_message(bid, 'assistant', notice,
                                           metadata={'kind': f'{resume_kind}_resume_pending', 'resume_id': resume_id})
                    self._mark_resume(resume_kind, resume_id, 'completed')
                    return {'resumed': True, 'pending': True, 'pending_kind': pending_kind,
                            'pending_id': pending_id, 'tool_calls': tool_count}

            answer = 'Продолжение остановлено: достигнут лимит раундов инструментов. Уже полученные результаты сохранены.'
            self.store.add_message(bid, 'assistant', answer,
                                   metadata={'kind': f'{resume_kind}_resume_limit', 'resume_id': resume_id})
            self._mark_resume(resume_kind, resume_id, 'completed')
            return {'resumed': True, 'answer': answer, 'limit_reached': True}
        except asyncio.CancelledError:
            self._mark_resume(resume_kind, resume_id, 'cancelled')
            try:
                self.store.add_message(bid, 'assistant', 'Продолжение модели остановлено пользователем.',
                                       metadata={'kind': f'{resume_kind}_resume_cancelled', 'resume_id': resume_id})
            except Exception:
                pass
            raise
        except Exception as exc:
            error = f'Не удалось продолжить модель после ввода/выполнения: {type(exc).__name__}: {exc}'
            self.store.add_message(bid, 'assistant', error,
                                   metadata={'kind': f'{resume_kind}_resume_error', 'resume_id': resume_id})
            self._mark_resume(resume_kind, resume_id, 'failed')
            return {'resumed': False, 'reason': error}

    async def close(self):
        await self.stack.aclose()
        self.credentials.close()
        await self.llm.close()
