<?php
/**
 * Tests public monitoring URL map for traffic-simulator-ui (run: php tests/test_traffic_simulator_monitoring_api.php).
 */
declare(strict_types=1);

$root = dirname(__DIR__);
require_once $root . '/docker/traffic-simulator-ui/public/lib/monitoring_urls.php';

$failures = 0;

function assert_eq(string $name, mixed $expected, mixed $actual): void
{
    global $failures;
    if ($expected !== $actual) {
        fwrite(STDERR, "FAIL: {$name} (expected " . var_export($expected, true) . ", got " . var_export($actual, true) . ")\n");
        $failures++;
    }
}

putenv('PROMETHEUS_EXTERNAL_URL=http://203.0.113.1:9090');
putenv('GRAFANA_EXTERNAL_URL=http://203.0.113.1:3000');
putenv('ALERTMANAGER_EXTERNAL_URL=http://203.0.113.1:9093');

$urls = traffic_simulator_monitoring_external_urls();

assert_eq('prometheus', 'http://203.0.113.1:9090', $urls['prometheus'] ?? null);
assert_eq('grafana', 'http://203.0.113.1:3000', $urls['grafana'] ?? null);
assert_eq('alertmanager', 'http://203.0.113.1:9093', $urls['alertmanager'] ?? null);

if ($failures > 0) {
    fwrite(STDERR, "{$failures} test(s) failed\n");
    exit(1);
}

echo "test_traffic_simulator_monitoring_api.php: OK\n";
