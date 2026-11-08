"""Bounded, auditable context collection for task handoff."""


def collect_handoff_scope(store, project_row, source_task, branch_id, scope, recent_messages=12):
    if scope not in {"branch", "task", "project"}:
        raise ValueError("Недопустимый уровень переноса контекста")

    task_rows = [source_task]
    omitted_task_count = 0
    if scope == "project":
        task_rows = store.tasks(project_row["id"])
        task_rows.sort(key=lambda row: 0 if int(row["id"]) == int(source_task["id"]) else 1)
        omitted_task_count = max(0, len(task_rows) - 40)
        task_rows = task_rows[:40]

    selected_branches = []
    for task_row in task_rows:
        for branch_row in store.branches(task_row["id"]):
            if scope == "branch" and int(branch_row["id"]) != int(branch_id):
                continue
            selected_branches.append((task_row, branch_row))

    # Put the active branch first so shared fork ancestry is represented once,
    # with the most relevant branch taking precedence. Bound project-wide input.
    selected_branches.sort(key=lambda pair: 0 if int(pair[1]["id"]) == int(branch_id) else 1)
    omitted_branch_count = max(0, len(selected_branches) - 60)
    selected_branches = selected_branches[:60]
    history_by_branch = {}
    branch_memory_by_id = {}
    for _, branch_row in selected_branches:
        bid = int(branch_row["id"])
        history_by_branch[bid] = store.messages(bid, limit=500)
        branch_memory_by_id[bid] = store.get_memory(bid)

    task_memory_lines = []
    if scope in {"task", "project"}:
        for task_row in task_rows:
            summary = (task_row.get("summary") or "").strip()
            if summary:
                task_memory_lines.append(
                    f"Задача «{task_row['title']}» (ID {task_row['id']}):\\n{summary[:9000]}"
                )

    branch_memory_lines = []
    for task_row, branch_row in selected_branches:
        mem = branch_memory_by_id[int(branch_row["id"])]
        if mem and (mem.get("summary") or "").strip():
            branch_memory_lines.append(
                f"Задача «{task_row['title']}», ветка «{branch_row['name']}» "
                f"(ID {branch_row['id']}, до сообщения {mem.get('through_message_id')}):\\n"
                f"{mem['summary'][:1400]}"
            )

    evidence_messages = []
    seen_message_ids = set()
    for task_row, branch_row in selected_branches:
        bid = int(branch_row["id"])
        hist = history_by_branch[bid]
        if not hist:
            continue
        if bid == int(branch_id):
            n = max(12, min(60, int(recent_messages or 12)))
            chosen = hist[:12] + hist[-n:] if len(hist) > 24 else hist
        else:
            chosen = hist[-8:]
        unique_chosen = []
        for message in chosen:
            mid = int(message.get("id", 0) or 0)
            if mid and mid in seen_message_ids:
                continue
            if mid:
                seen_message_ids.add(mid)
            unique_chosen.append(message)
        if not unique_chosen:
            continue
        evidence_messages.append({
            "role": "tool",
            "content": (
                f"[КОНТЕКСТ ВЕТКИ: задача «{task_row['title']}», "
                f"ветка «{branch_row['name']}», ID {bid}]\\n" +
                "\\n".join(
                    f"{m.get('role', '?')}: {(m.get('content') or '')[:1200]}"
                    for m in unique_chosen
                )
            ),
        })

    seen_attachments = set()
    attachment_lines = []
    attachment_ids = []
    for history in history_by_branch.values():
        for message in history:
            for attachment in message.get("attachments", []):
                aid = int(attachment.get("id", 0))
                if aid and aid not in seen_attachments:
                    seen_attachments.add(aid)
                    attachment_ids.append(aid)
                    attachment_lines.append(
                        f"- {attachment.get('original_name', 'файл')} (ID {aid}; "
                        f"{attachment.get('kind', 'тип неизвестен')}; "
                        f"{attachment.get('size', 0)} байт): "
                        f"{attachment.get('note') or 'описание отсутствует'}"
                    )

    # Keep the summarization request bounded even for very large projects.
    evidence_budget = 52000
    bounded_evidence = []
    used_chars = 0
    for item in evidence_messages:
        remaining = evidence_budget - used_chars
        if remaining <= 0:
            break
        content = item["content"][:remaining]
        bounded_evidence.append({"role": item["role"], "content": content})
        used_chars += len(content)
    omitted_evidence_branches = max(0, len(evidence_messages) - len(bounded_evidence))

    return {
        "task_rows": task_rows,
        "selected_branches": selected_branches,
        "history_by_branch": history_by_branch,
        "branch_memory_by_id": branch_memory_by_id,
        "task_memory_lines": task_memory_lines,
        "branch_memory_lines": branch_memory_lines,
        "evidence_messages": bounded_evidence,
        "attachment_lines": attachment_lines[:120],
        "attachment_count": len(seen_attachments),
        "attachment_ids": attachment_ids,
        "total_source_messages": len({int(m.get("id", 0)) for h in history_by_branch.values() for m in h if m.get("id")}),
        "omitted_task_count": omitted_task_count,
        "omitted_branch_count": omitted_branch_count,
        "omitted_evidence_branches": omitted_evidence_branches,
    }
