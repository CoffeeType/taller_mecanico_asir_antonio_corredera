# Simulator log lines tagged by target host and run id

Each JMeter-imported line in `metrics.log` records `target_host` (from the run’s base URL) and `run_id` (one id per «Iniciar prueba»), in addition to `source=simulator`. The traffic UI can filter by host and by current execution without clearing shared logs.

**Considered options:** (1) separate log file per run; (2) UI-only filtering on JTL paths; (3) tag each line in the shared log. We chose (3) to keep a single Prometheus scrape path and Grafana datasource while making external vs internal targets visible.

**Consequences:** Prometheus gains a `target_host` label on simulator counters (low cardinality in lab use). Legacy lines without tags remain parseable; «solo esta ejecución» excludes them. Application traffic (`source=app`) is unchanged.
