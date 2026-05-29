# Response time log lines tagged by traffic source

HTTP response durations are stored in `response_time.log` with an explicit `source=app` or `source=simulator` suffix, matching `metrics.log`. Legacy lines that contain only a number are treated as `source=app`.

**Considered options:** (1) keep a single shared latency stream; (2) separate files per source; (3) tag each line in the existing file. We chose (3) because it preserves one scrape path via `/metrics.php`, stays consistent with ADR 0001, and allows Prometheus summaries and the traffic UI to filter latencies without duplicating volumes.

**Consequences:** Exporters and dashboards must use the `source` label on `app_http_response_time_seconds`; old dashboards querying quantiles without `source` need updating. Log rotation and mixed legacy lines remain supported via the parser in `traffic_simulator_lib.php`.
