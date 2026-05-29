<?php
/**
 * Pruebas unitarias para scripts/traffic_simulator_lib.php (sin PHPUnit; código 0 si todo pasa).
 */

declare(strict_types=1);

require_once __DIR__ . '/../scripts/traffic_simulator_lib.php';

$fails = [];

function t(string $name, bool $ok): void
{
    global $fails;
    if (!$ok) {
        $fails[] = $name;
        echo "FAIL: {$name}\n";
    }
}

$pl = traffic_simulator_parse_metrics_log_line('GET 200 source=app');
t('parse new app line', $pl !== null && $pl['method'] === 'GET' && $pl['status'] === 200 && $pl['source'] === 'app' && $pl['path'] === null);

$ps = traffic_simulator_parse_metrics_log_line('GET 404 /x source=simulator');
t('parse simulator line', $ps !== null && $ps['status'] === 404 && $ps['path'] === '/x' && $ps['source'] === 'simulator');

$lg = traffic_simulator_parse_metrics_log_line('GET 200');
t('parse legacy app', $lg !== null && $lg['source'] === 'app');

$lsx = traffic_simulator_parse_metrics_log_line('GET 500 /does-not-exist');
t('parse legacy sim', $lsx !== null && $lsx['source'] === 'simulator' && $lsx['status'] === 500);

t('parse rejects junk', traffic_simulator_parse_metrics_log_line('not a metric line') === null);

$rtSim = traffic_simulator_parse_response_time_line('0.1 source=simulator');
t('parse response_time simulator', $rtSim !== null && abs($rtSim['time'] - 0.1) < 0.0001 && $rtSim['source'] === 'simulator');

$rtLegacy = traffic_simulator_parse_response_time_line('0.2');
t('parse response_time legacy app', $rtLegacy !== null && $rtLegacy['source'] === 'app');

$td = sys_get_temp_dir() . '/traffic_sim_test_' . bin2hex(random_bytes(4));
mkdir($td, 0755, true);
$ml = $td . '/metrics.log';
$rl = $td . '/response_time.log';
traffic_simulator_append_log($ml, $rl, ['method' => 'GET', 'status' => 201, 'time' => 0.12], '/foo', 'example.com', 'run-test-1');
$appended = file_get_contents($ml);
t('append_log includes source=simulator', is_string($appended) && str_contains($appended, 'source=simulator') && str_contains($appended, 'GET 201 /foo'));
t('append_log includes target_host', is_string($appended) && str_contains($appended, 'target_host=example.com'));
t('append_log includes run_id', is_string($appended) && str_contains($appended, 'run_id=run-test-1'));
$rtAppended = trim((string) file_get_contents($rl));
t('append_log response_time source=simulator', str_contains($rtAppended, '0.12') && str_contains($rtAppended, 'source=simulator'));
t('append_log response_time run_id', str_contains($rtAppended, 'run_id=run-test-1'));

$ph = traffic_simulator_host_from_base_url('https://Example.com/app');
t('host_from_base_url', $ph === 'example.com');

$pt = traffic_simulator_parse_metrics_log_line('GET 200 /x target_host=example.com run_id=run1 source=simulator');
t('parse metrics with host and run', $pt !== null && $pt['target_host'] === 'example.com' && $pt['run_id'] === 'run1');

file_put_contents($ml, "GET 200 source=app\nGET 404 /a source=simulator\nGET 200\nbogus\nGET 500 /z source=simulator\n");
file_put_contents($rl, "0.1\n0.2\n");
$st = traffic_simulator_read_log_stats($ml, $rl, 20);
t('read_log_stats success count', ($st['success_requests'] ?? -1) === 2);
t('read_log_stats error count', ($st['error_requests'] ?? -1) === 2);
t('read_log_stats recent matches all lines', ($st['recent_success'] ?? -1) === 2 && ($st['recent_errors'] ?? -1) === 2);
t('read_log_stats has recent_window', ($st['recent_window'] ?? 0) === 20);

file_put_contents($ml, "GET 200 source=app\nGET 404 /a source=simulator\n");
$stTail = traffic_simulator_read_log_stats($ml, $rl, 2);
t('read_log_stats tail one ok one err', ($stTail['recent_success'] ?? -1) === 1 && ($stTail['recent_errors'] ?? -1) === 1);

file_put_contents($ml, "GET 200 source=app\nGET 404 /a source=simulator\nGET 200\nGET 500 /z source=simulator\n");
$stSim = traffic_simulator_read_log_stats($ml, $rl, 20, 'simulator');
t('read_log_stats simulator filter total', ($stSim['total_requests'] ?? -1) === 2);
t('read_log_stats simulator filter success', ($stSim['success_requests'] ?? -1) === 0);
t('read_log_stats simulator filter errors', ($stSim['error_requests'] ?? -1) === 2);

file_put_contents($rl, "0.5 source=app\n0.1 source=simulator\n0.2 source=simulator\n0.9 source=app\n");
$stSimRt = traffic_simulator_read_log_stats($ml, $rl, 20, 'simulator');
t('read_log_stats simulator avg response_time', abs(($stSimRt['avg_response_time'] ?? 0) - 0.15) < 0.0001);
t('read_log_stats simulator max response_time', abs(($stSimRt['max_response_time'] ?? 0) - 0.2) < 0.0001);

file_put_contents($ml, "GET 200 /a target_host=web run_id=r1 source=simulator\nGET 404 /b target_host=example.com run_id=r2 source=simulator\n");
$stHostRun = traffic_simulator_read_log_stats($ml, $rl, 20, 'simulator', 'web', 'r1');
t('read_log_stats filter host and run', ($stHostRun['total_requests'] ?? -1) === 1);

$preview = traffic_simulator_read_metrics_log_preview($ml, 10, 'simulator');
t('log preview simulator lines', count($preview['lines'] ?? []) >= 1);
t('log preview simulator total', ($preview['total'] ?? -1) === 2);
t('log preview total_all', ($preview['total_all'] ?? -1) === 2);

$planned = traffic_simulator_planned_requests('http://web');
t('planned requests non-empty', count($planned) >= 5);
t('planned requests absolute url', isset($planned[0]['url']) && str_starts_with($planned[0]['url'], 'http://web'));
t('planned requests has method', isset($planned[0]['method']) && $planned[0]['method'] === 'GET');

$plannedPath = traffic_simulator_planned_requests('http://web/taller');
t('planned requests base path prefix', count($plannedPath) > 0 && str_contains($plannedPath[0]['url'], '/taller'));

$badProbe = traffic_simulator_probe_base_url('notaurl', ['trusted_cli' => true]);
t('probe rejects bad url', isset($badProbe['ok']) && $badProbe['ok'] === false && ($badProbe['http_code'] ?? -1) === 0);
t('probe bad url has http_ok false', ($badProbe['http_ok'] ?? true) === false);

$plannedWeb = traffic_simulator_planned_requests('http://web');
$probeFields = traffic_simulator_probe_base_url('http://web', ['trusted_cli' => true, 'timeout' => 2]);
t('probe includes planned_requests', isset($probeFields['planned_requests']) && count($probeFields['planned_requests'] ?? []) === count($plannedWeb));
t('probe has http_ok key', array_key_exists('http_ok', $probeFields));

$t = traffic_simulator_normalize_base_url_input('example.com/ruta');
t('auto https for public host', $t === 'https://example.com/ruta');

$t2 = traffic_simulator_normalize_base_url_input('web');
t('auto http for internal web', $t2 === 'http://web');

$t3 = traffic_simulator_validate_base_url('example.com');
t('schemeless validates', isset($t3['ok']) && $t3['ok'] === true && ($t3['base'] ?? '') === 'https://example.com');

$bad = traffic_simulator_validate_base_url('ftp://example.com');
t('reject non-http(s)', isset($bad['ok']) && $bad['ok'] === false);

$cred = traffic_simulator_validate_base_url('http://user:pass@example.com/');
t('reject embedded credentials', isset($cred['ok']) && $cred['ok'] === false);

$ok = traffic_simulator_validate_base_url('http://web/path');
t('accept http://web', isset($ok['ok']) && $ok['ok'] === true && ($ok['base'] ?? '') === 'http://web/path');

$needExt = traffic_simulator_validate_target_url('https://example.com', [
    'trusted_cli'      => false,
    'confirm_external' => false,
]);
t('external needs confirm', ($needExt['code'] ?? '') === 'NEED_CONFIRM_EXTERNAL');

$extOk = traffic_simulator_validate_target_url('https://example.com', [
    'trusted_cli'      => false,
    'confirm_external' => true,
]);
t('external with confirm ok', isset($extOk['ok']) && $extOk['ok'] === true);

$privDeny = traffic_simulator_validate_target_url('http://10.10.10.10', ['allow_private' => false]);
t('reject private literal IP', isset($privDeny['ok']) && $privDeny['ok'] === false);

$privOk = traffic_simulator_validate_target_url('http://192.168.0.1', ['allow_private' => true]);
t('allow private literal IP with option', isset($privOk['ok']) && $privOk['ok'] === true);

$defaults = traffic_simulator_resolve_config([]);
t('default config no error', !isset($defaults['error']));
t('default port base', ($defaults['base_url'] ?? '') === 'http://localhost:8081');

$ext = traffic_simulator_resolve_config(['base-url' => 'https://example.com/']);
t('https trim', ($ext['base_url'] ?? '') === 'https://example.com');

$inv = traffic_simulator_resolve_config(['base-url' => 'notaurl']);
t('invalid URL error', isset($inv['error']));

$jsonPath = __DIR__ . '/fixtures/traffic_routes_test.json';
$withRoutes = traffic_simulator_resolve_config(['routes-file' => $jsonPath, 'base-url' => 'http://mock.test']);
t('routes JSON loaded', !isset($withRoutes['error']) && count($withRoutes['pages'] ?? []) === 2);

$w = traffic_simulator_build_weighted([
    ['path' => '/', 'method' => 'GET', 'weight' => 2],
]);
t('weighted size', count($w) === 2);

$joined = traffic_simulator_join_paths('/base/', '/ruta');
t('join base route paths', $joined === '/base/ruta');

$rows = traffic_simulator_jmeter_route_rows([
    ['path' => '/', 'method' => 'GET', 'weight' => 1],
], ['min_sleep_ms' => 1, 'max_sleep_ms' => 2, 'error_rate' => 0], '/', 3);
t('jmeter route rows generated', count($rows) === 3 && ($rows[0]['method'] ?? '') === 'GET');

$jtl = $td . '/results.jtl';
file_put_contents($jtl, "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,IdleTime,Connect\n");
file_put_contents($jtl, "1,123,GET /jmeter,200,OK,t,text,true,,1,1,1,1,http://web/jmeter,100,0,10\n", FILE_APPEND);
file_put_contents($ml, '');
file_put_contents($rl, '');
$imported = traffic_simulator_import_jmeter_jtl($jtl, $ml, $rl, 0, 'web', 'jtl-run-1');
t('jmeter jtl imported count', $imported === 1);
$jtlMetrics = trim((string) file_get_contents($ml));
t('jmeter jtl metrics line', $jtlMetrics === 'GET 200 /jmeter target_host=web run_id=jtl-run-1 source=simulator');
$jtlRt = trim((string) file_get_contents($rl));
t('jmeter jtl response seconds', $jtlRt === '0.123 run_id=jtl-run-1 source=simulator');

echo empty($fails) ? "PASS: traffic_simulator_lib tests OK.\n" : "FAILURES: " . count($fails) . "\n";
exit(empty($fails) ? 0 : 1);
