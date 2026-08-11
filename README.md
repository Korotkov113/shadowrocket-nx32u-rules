# Актуальные правила Shadowrocket

Компактный конфиг для селективного проксирования: выбранные сервисы идут через `PROXY`, остальной трафик — через `DIRECT`.

Репозиторий ежедневно собирает Shadowrocket-совместимые правила из открытых списков [itdoginfo/allow-domains](https://github.com/itdoginfo/allow-domains):

- [`rules/domains.list`](rules/domains.list) — домены в формате `DOMAIN-SUFFIX`;
- [`rules/ipv4.list`](rules/ipv4.list) — IPv4-подсети в формате `IP-CIDR`;
- [`shadowrocket.conf`](shadowrocket.conf) — обезличенный пример конфига без прокси-узлов и персональных DNS-адресов.

## Установка

Добавьте в Shadowrocket удалённый конфиг по адресу:

```text
https://raw.githubusercontent.com/Korotkov113/shadowrocket-nx32u-rules/main/shadowrocket.conf
```

Либо используйте два стабильных URL правил в своём конфиге:

```ini
RULE-SET,https://raw.githubusercontent.com/Korotkov113/shadowrocket-nx32u-rules/main/rules/domains.list,PROXY
RULE-SET,https://raw.githubusercontent.com/Korotkov113/shadowrocket-nx32u-rules/main/rules/ipv4.list,PROXY,no-resolve
```

В Shadowrocket включите `Настройки → Конфигурация → Автоматическое фоновое обновление`. Для немедленного обновления удалённых правил откройте конфиг и нажмите «Использовать конфигурацию» или «Компилировать».

Публичный пример использует обычный AdGuard DNS-over-HTTPS через выбранный прокси. Свой персональный DoH можно указать только в локальной копии; не публикуйте его URL.

## Обновление

GitHub Actions запускает генератор каждый день в 03:17 UTC и коммитит изменения только при изменении upstream-списков. Локальная проверка:

```bash
python3 scripts/update_rules.py --check
```

