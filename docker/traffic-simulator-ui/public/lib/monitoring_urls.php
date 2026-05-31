<?php
declare(strict_types=1);

/**
 * External monitoring UI URLs injected via compose environment.
 *
 * @return array{prometheus: string, grafana: string, alertmanager: string}
 */
function traffic_simulator_monitoring_external_urls(): array
{
    return [
        'prometheus'    => getenv('PROMETHEUS_EXTERNAL_URL') ?: '',
        'grafana'       => getenv('GRAFANA_EXTERNAL_URL') ?: '',
        'alertmanager'  => getenv('ALERTMANAGER_EXTERNAL_URL') ?: '',
    ];
}
