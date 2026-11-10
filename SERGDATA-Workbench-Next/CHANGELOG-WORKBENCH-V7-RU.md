# Workbench v7 — изменения

- CredentialBroker: единый достоверный статус `persistent/session/missing`.
- SSH: отдельное сообщение при отклонении пароля сервером.
- SSH cancellation: CancellationToken с callbacks для Paramiko client/channel.
- ProcessRegistry: подтверждаемое завершение дерева процессов Windows и fallback.
- Agent: продолжения после защищённого ввода и SSH-результатов включены в общий реестр отменяемых задач ветки.
- UI: видимый статус остановки процесса, polling до терминального состояния.
- UI: увеличенная 14 px зона перетаскивания разделителя панели выполнения.
- Добавлены регрессионные тесты статусов секретов, SSH cancellation, stop callbacks и UI.
