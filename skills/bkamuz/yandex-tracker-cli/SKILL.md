# Yandex Tracker CLI Skill

Простой CLI для Yandex Tracker на чистом bash + curl. Работает напрямую через API с правильными заголовками (`X-Org-Id`). Не требует внешних зависимостей кроме `curl` и `jq`.

## Установка

1. Скопируйте скрипт в директорию в PATH:
```bash
mkdir -p ~/bin
cp yandex-tracker ~/bin/
chmod +x ~/bin/yandex-tracker
```

2. Создайте конфигурационный файл `~/.yandex-tracker-env`:
```bash
TOKEN='y0__...'      # OAuth токен из Tracker UI (Application → OAuth)
ORG_ID='7446...'     # On-premise Org ID (из URL или DevTools → X-Org-Id)
```

3. Убедитесь, что `jq` установлен:
```bash
sudo apt install jq   # Ubuntu/Debian
# или
brew install jq       # macOS
```

## Использование

### Основные команды

| Команда | Описание |
|---------|----------|
| `queues` | Список всех очередей (формат: `key<TAB>name`) |
| `queue-get <key>` | Детали очереди (JSON) |
| `queue-fields <key>` | Все поля очереди (включая локальные) |
| `issue-get <issue-id>` | Получить задачу (формат: `BIMLAB-123`) |
| `issue-create <queue> <summary>` | Создать задачу. Доп. поля через stdin (JSON) |
| `issue-update <issue-id>` | Обновить задачу (JSON через stdin) |
| `issue-delete <issue-id>` | Удалить задачу |
| `issue-comment <issue-id> <text>` | Добавить комментарий |
| `issue-comment-edit <issue-id> <comment-id> <new-text>` | Редактировать комментарий |
| `issue-comment-delete <issue-id> <comment-id>` | Удалить комментарий |
| `issue-transitions <issue-id>` | Возможные переходы статуса |
| `issue-close <issue-id> <resolution>` | Закрыть задачу (resolution: `fixed`, `wontFix`, `duplicate` и др.) |
| `issue-worklog <issue-id> <duration> [comment]` | Добавить worklog (duration: `PT1H30M`) |
| `issue-attachments <issue-id>` | Список вложений задачи (JSON) |
| `attachment-download <issue-id> <fileId> [output]` | Скачать файл. Если output не указано — stdout |
| `attachment-upload <issue-id> <filepath> [comment]` | Загрузить файл в задачу. Опциональный комментарий |
| `issues-search` | Поиск задач через YQL. Запрос JSON через stdin, например: `{"query":"Queue = BIMLAB AND Status = Open","limit":50}` |
| `projects-list` | Список всех проектов (JSON) |
| `project-get <project-id>` | Детали проекта |
| `project-issues <project-id>` | Список задач проекта |
| `sprints-list` | Список спринтов (Agile) |
| `sprint-get <sprint-id>` | Детали спринта |
| `sprint-issues <sprint-id>` | Задачи в спринте |
| `users-list` | Список всех пользователей (справочник) |
| `statuses-list` | Список всех статусов задач |
| `resolutions-list` | Список разрешений для закрытия задач |
| `issue-types-list` | Список типов задач (bug, task, improvement) |

### Примеры

```bash
# Список очередей
yandex-tracker queues

# Создать задачу с дополнительными полями
echo '{"priority":"critical","description":"Подробности"}' | yandex-tracker issue-create BIMLAB "Новая задача"

# Добавить комментарий
yandex-tracker issue-comment BIMLAB-266 "Работаю над этим"

# Добавить spent time
yandex-tracker issue-worklog BIMLAB-266 PT2H "Исследование"

# Получить возможные переходы (чтобы понять, как закрыть)
yandex-tracker issue-transitions BIMLAB-266 | jq .

# Обновить задачу (перевести в другую очередь, например)
echo '{"queue":"RAZRABOTKA"}' | yandex-tracker issue-update BIMLAB-266

# Поиск задач через YQL
echo '{"query":"Queue = BIMLAB AND Status = Open","limit":20}' | yandex-tracker issues-search | jq .

# Список проектов
yandex-tracker projects-list | jq .

# Задачи проекта
yandex-tracker project-issues 104 | jq .

# Вложения (Attachments)
# Список вложений
yandex-tracker issue-attachments BIMLAB-266 | jq .
# Скачать файл (fileId из списка вложений) в указанный путь
yandex-tracker attachment-download BIMLAB-266 abc123 /tmp/downloaded.pdf
# Загрузить файл в задачу (с комментарием)
yandex-tracker attachment-upload BIMLAB-266 /path/to/file.pdf "Служебная записка"

# Спринты (Agile)
yandex-tracker sprints-list | jq .
yandex-tracker sprint-issues 42 | jq .

# Справочники
yandex-tracker users-list | jq .
yandex-tracker statuses-list | jq .
yandex-tracker resolutions-list | jq .
yandex-tracker issue-types-list | jq .

# Редактирование и удаление комментариев
yandex-tracker issue-comment-edit BIMLAB-266 12345 "Обновлённый текст"
yandex-tracker issue-comment-delete BIMLAB-266 12345
```

## Примечания

- **Org-ID for on-premise:** Найдите в DevTools Tracker → Network → любой запрос → заголовок `X-Org-Id`.
- **Для Cloud Tracker** нужно изменить скрипт, заменив `X-Org-Id` на `X-Cloud-Org-Id`.
- Токен можно получить в Tracker UI: Settings → Applications → OAuth → Generate new token.
- Все команды выводят JSON через `jq` для удобной дальнейшей обработки.

## Структура

```
skills/yandex-tracker-cli/
├── yandex-tracker      # Исполняемый скрипт
├── SKILL.md            # Эта документация
└── .yandex-trackerrc   # (не в репо) Конфиг с TOKEN и ORG_ID
```

## Limitations

- Нет пагинации (т. первые 100 элементов)
- Нет продвинутого поиска (`issues_find` можно добавить)
- Простая валидация аргументов

## License

MIT
