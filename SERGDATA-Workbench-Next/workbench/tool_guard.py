import json


def tool_call_fingerprint(name, args, sandbox_revision=0):
    """Return a repeat-guard key that changes when a sandbox workspace mutates."""
    stateful = name in {
        'sandbox_list_files', 'sandbox_read_file', 'sandbox_run_check', 'sandbox_diff'
    }
    return (
        name,
        json.dumps(args, sort_keys=True, ensure_ascii=False),
        int(sandbox_revision) if stateful else None,
    )
