<?php
/**
 * API JSON para la UI del simulador — proxy al plano de control (token solo en servidor).
 */
declare(strict_types=1);

header('Content-Type: application/json');

require_once '/opt/inc/traffic_simulator_lib.php';

$controlBase = rtrim(getenv('SIMULATOR_CONTAINER_URL') ?: 'http://traffic-simulator:8085', '/');
$token       = getenv('SIMULATOR_CONTROL_TOKEN') ?: '';

// Misma ruta que el volumen ./logs → /var/www/html/logs (no usar __DIR__/../logs → /var/logs).
$logsDirRaw = getenv('SIM_LOG_DIR');
$logsDir    = ($logsDirRaw !== false && $logsDirRaw !== '') ? $logsDirRaw : (__DIR__ . '/logs');
$logsDir    = rtrim($logsDir, '/\\');
if (!is_dir($logsDir)) {
    @mkdir($logsDir, 0775, true);
}

$metricsLog      = $logsDir . '/metrics.log';
$responseTimeLog = $logsDir . '/response_time.log';

/** @return array{logs_dir:string,metrics_log:string,logs_dir_exists:bool,logs_dir_writable:bool,metrics_log_readable:bool,metrics_log_size:int} */
function simulator_ui_logs_diagnostics(string $logsDir, string $metricsLog): array
{
    $size = (is_file($metricsLog) && is_readable($metricsLog)) ? (int) filesize($metricsLog) : 0;

    return [
        'logs_dir'             => $logsDir,
        'metrics_log'          => $metricsLog,
        'logs_dir_exists'      => is_dir($logsDir),
        'logs_dir_writable'    => is_dir($logsDir) && is_writable($logsDir),
        'metrics_log_readable' => is_readable($metricsLog),
        'metrics_log_size'     => $size,
    ];
}

/**
 * @return array{ok:bool, data?:mixed, http_code?:int, error?:string}
 */
function simulator_ui_control_request(string $method, string $path, ?array $body, string $base, string $token): array
{
    $url     = $base . $path;
    $headers = [
        'Content-Type: application/json',
        'X-Simulator-Token: ' . $token,
    ];
    $opts = [
        'http' => [
            'method'        => $method,
            'header'        => implode("\r\n", $headers),
            'timeout'       => 20,
            'ignore_errors' => true,
        ],
    ];
    if ($body !== null) {
        $opts['http']['content'] = json_encode($body);
    }
    $ctx = stream_context_create($opts);
    $raw = @file_get_contents($url, false, $ctx);
    $code = 0;
    if (!empty($http_response_header) && is_array($http_response_header)) {
        foreach ($http_response_header as $h) {
            if (preg_match('#HTTP/\S+\s+(\d+)#', $h, $m)) {
                $code = (int) $m[1];

                break;
            }
        }
    }
    if ($raw === false) {
        return ['ok' => false, 'error' => 'No se pudo conectar al API de control. ¿traffic-simulator levantado?'];
    }
    $data = json_decode($raw, true);
    if ($code >= 400) {
        $msg = is_array($data) && isset($data['error']) ? (string) $data['error'] : $raw;

        return ['ok' => false, 'http_code' => $code, 'error' => $msg, 'data' => $data];
    }

    return ['ok' => true, 'data' => $data, 'http_code' => $code];
}

/** @return array{running:bool, raw?:array{ok:bool, data?:mixed, http_code?:int, error?:string}, detail?:array<string,mixed>} */
function simulator_ui_running_cached(string $base, string $token): array
{
    $r = simulator_ui_control_request('GET', '/status', null, $base, $token);
    if (!$r['ok'] || !is_array($r['data'])) {
        return ['running' => false, 'raw' => $r];
    }

    return ['running' => !empty($r['data']['running']), 'detail' => $r['data']];
}

function simulator_ui_url_from_logs_path(string $logsDir, string $path): string
{
    $logsReal = realpath($logsDir);
    $pathReal = realpath($path);
    if ($logsReal === false || $pathReal === false) {
        return '';
    }
    $logsReal = rtrim(str_replace('\\', '/', $logsReal), '/');
    $pathReal = str_replace('\\', '/', $pathReal);
    if ($pathReal !== $logsReal && !str_starts_with($pathReal, $logsReal . '/')) {
        return '';
    }
    $rel = ltrim(substr($pathReal, strlen($logsReal)), '/');
    return 'logs/' . implode('/', array_map('rawurlencode', explode('/', $rel)));
}

/** @param array<string,mixed>|null $workerDetail */
function simulator_ui_jmeter_links(string $logsDir, ?array $workerDetail): array
{
    if (!is_array($workerDetail)) {
        return [];
    }
    $jmeter = isset($workerDetail['jmeter']) && is_array($workerDetail['jmeter']) ? $workerDetail['jmeter'] : [];
    $files  = isset($jmeter['files']) && is_array($jmeter['files']) ? $jmeter['files'] : [];
    $links  = [
        'enabled'          => true,
        'tool'             => $jmeter['tool'] ?? 'apache-jmeter',
        'report_ready'     => !empty($jmeter['report_ready']),
        'imported_samples' => $jmeter['imported_samples'] ?? 0,
    ];
    if (isset($files['report_dir']) && is_string($files['report_dir'])) {
        $report = rtrim($files['report_dir'], '/\\') . '/index.html';
        $url = simulator_ui_url_from_logs_path($logsDir, $report);
        if ($url !== '') {
            $links['report_url'] = $url;
        }
    }
    foreach (['results_jtl', 'jmeter_log', 'stdout_log', 'test_jmx'] as $key) {
        if (isset($files[$key]) && is_string($files[$key])) {
            $url = simulator_ui_url_from_logs_path($logsDir, $files[$key]);
            if ($url !== '') {
                $links[$key . '_url'] = $url;
            }
        }
    }

    return $links;
}

/**
 * @return array{target_host:?string,run_id:?string}
 */
function simulator_ui_resolve_log_filters(?array $workerDetail, string $baseUrlInput, string $runScope): array
{
    $baseUrlInput     = trim($baseUrlInput);
    $targetHostFilter = $baseUrlInput !== '' ? traffic_simulator_host_from_base_url($baseUrlInput) : null;
    $runIdFilter      = null;

    if ($runScope === 'current' && is_array($workerDetail)) {
        $jmeter = isset($workerDetail['jmeter']) && is_array($workerDetail['jmeter'])
            ? $workerDetail['jmeter']
            : $workerDetail;
        $rid = $jmeter['run_id'] ?? null;
        if (is_string($rid) && $rid !== '') {
            $runIdFilter = $rid;
        }
    }

    return [
        'target_host' => $targetHostFilter,
        'run_id'      => $runIdFilter,
    ];
}

/**
 * @return array<string,mixed>
 */
function simulator_ui_status_payload(
    string $metricsLog,
    string $responseTimeLog,
    string $logsDir,
    bool $running,
    ?array $workerDetail,
    ?string $error = null
): array {
    $defaultBase = getenv('SIM_UI_DEFAULT_BASE_URL') ?: 'http://web';
    $publicApp   = getenv('SIM_UI_PUBLIC_APP_URL') ?: '';
    $baseForPlan = isset($_GET['base_url']) && trim((string) $_GET['base_url']) !== ''
        ? trim((string) $_GET['base_url'])
        : $defaultBase;
    $routesFile  = isset($_GET['routes_file']) && trim((string) $_GET['routes_file']) !== ''
        ? trim((string) $_GET['routes_file'])
        : null;
    $runScope    = isset($_GET['run_scope']) ? (string) $_GET['run_scope'] : 'current';
    if (!in_array($runScope, ['current', 'all'], true)) {
        $runScope = 'current';
    }

    $logFilters = simulator_ui_resolve_log_filters($workerDetail, $baseForPlan, $runScope);
    $targetHost = $logFilters['target_host'];
    $runId      = $logFilters['run_id'];

    $preview = traffic_simulator_read_metrics_log_preview(
        $metricsLog,
        20,
        'simulator',
        $targetHost,
        $runId
    );

    $activeRun = null;
    if (is_array($workerDetail)) {
        $jmeter = isset($workerDetail['jmeter']) && is_array($workerDetail['jmeter'])
            ? $workerDetail['jmeter']
            : $workerDetail;
        if (!empty($jmeter['run_id'])) {
            $activeRun = [
                'run_id'      => $jmeter['run_id'],
                'target_host' => $jmeter['target_host'] ?? $targetHost,
                'base_url'    => $jmeter['base_url'] ?? $baseForPlan,
            ];
        }
    }

    $payload = [
        'running'          => $running,
        'stats'            => traffic_simulator_read_log_stats(
            $metricsLog,
            $responseTimeLog,
            20,
            'simulator',
            $targetHost,
            $runId
        ),
        'stats_app'        => [
            'total_requests' => traffic_simulator_read_log_stats($metricsLog, $responseTimeLog, 20, 'app')['total_requests'] ?? 0,
        ],
        'log_preview'      => $preview,
        'log_filters'      => [
            'target_host' => $targetHost,
            'run_id'      => $runId,
            'run_scope'   => $runScope,
        ],
        'active_run'       => $activeRun,
        'default_base_url' => $defaultBase,
        'public_app_url'   => $publicApp,
        'planned_requests' => traffic_simulator_planned_requests($baseForPlan, $routesFile),
        'monitoring'       => [
            'prometheus' => getenv('PROMETHEUS_EXTERNAL_URL') ?: '',
            'grafana'    => getenv('GRAFANA_EXTERNAL_URL') ?: '',
        ],
        'diagnostics'      => simulator_ui_logs_diagnostics($logsDir, $metricsLog),
        'worker_detail'    => $workerDetail,
        'jmeter'           => simulator_ui_jmeter_links($logsDir, $workerDetail),
    ];
    if ($error !== null) {
        $payload['error'] = $error;
    }

    return $payload;
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

if ($method === 'GET') {
    $action = $_GET['action'] ?? '';

    if ($action === 'log_preview') {
        $baseForPlan = isset($_GET['base_url']) ? trim((string) $_GET['base_url']) : '';
        $runScope    = isset($_GET['run_scope']) ? (string) $_GET['run_scope'] : 'current';
        if (!in_array($runScope, ['current', 'all'], true)) {
            $runScope = 'current';
        }
        $runningInfo = simulator_ui_running_cached($controlBase, $token);
        $filters     = simulator_ui_resolve_log_filters(
            $runningInfo['detail'] ?? null,
            $baseForPlan,
            $runScope
        );
        $preview = traffic_simulator_read_metrics_log_preview(
            $metricsLog,
            20,
            'simulator',
            $filters['target_host'],
            $filters['run_id']
        );
        echo json_encode([
            'lines'           => $preview['lines'],
            'total'           => $preview['total'],
            'total_simulator' => $preview['total'],
            'total_all'       => $preview['total_all'],
            'log_filters'     => $filters + ['run_scope' => $runScope],
        ]);

        exit;
    }

    if ($token === '') {
        http_response_code(503);
        echo json_encode(simulator_ui_status_payload(
            $metricsLog,
            $responseTimeLog,
            $logsDir,
            false,
            null,
            'SIMULATOR_CONTROL_TOKEN no configurado en traffic-simulator-ui'
        ));

        exit;
    }

    $runningInfo  = simulator_ui_running_cached($controlBase, $token);
    $run          = !empty($runningInfo['running']);
    $workerDetail = isset($runningInfo['detail']) && is_array($runningInfo['detail']) ? $runningInfo['detail'] : null;

    echo json_encode(simulator_ui_status_payload(
        $metricsLog,
        $responseTimeLog,
        $logsDir,
        $run,
        $workerDetail
    ));

    exit;
}

if ($method !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method Not Allowed']);

    exit;
}

$input = json_decode(file_get_contents('php://input') ?: '', true);
if (!is_array($input)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);

    exit;
}

$action = isset($input['action']) ? (string) $input['action'] : '';

if ($token === '') {
    http_response_code(503);
    echo json_encode(['success' => false, 'message' => 'SIMULATOR_CONTROL_TOKEN vacío']);

    exit;
}

switch ($action) {

    case 'probe':
        $baseUrlRaw = isset($input['base_url']) && trim((string) $input['base_url']) !== ''
            ? (string) $input['base_url']
            : (getenv('SIM_UI_DEFAULT_BASE_URL') ?: 'http://web');
        $confirmUi = !empty($input['confirm_external']);
        $chk       = traffic_simulator_validate_target_url($baseUrlRaw, [
            'confirm_external' => $confirmUi,
            'trusted_cli'      => false,
        ]);
        if (!$chk['ok']) {
            if (($chk['code'] ?? '') === 'NEED_CONFIRM_EXTERNAL') {
                http_response_code(428);
                echo json_encode([
                    'success' => false,
                    'code'    => 'NEED_CONFIRM_EXTERNAL',
                    'message' => $chk['message'] ?? 'Confirmation required',
                ]);

                exit;
            }

            echo json_encode([
                'success'   => false,
                'reachable' => false,
                'http_code' => 0,
                'message'   => $chk['message'] ?? 'URL inválida',
            ]);

            exit;
        }

        $routesProbe = isset($input['routes_file']) && trim((string) $input['routes_file']) !== ''
            ? trim((string) $input['routes_file'])
            : null;
        $pr = traffic_simulator_probe_base_url($baseUrlRaw, [
            'confirm_external' => $confirmUi,
            'trusted_cli'      => false,
            'timeout'          => max(3, min(20, (int) ($input['timeout'] ?? 8))),
            'routes_file'      => $routesProbe,
        ]);

        echo json_encode([
            'success'          => $pr['ok'],
            'reachable'        => $pr['reachable'] ?? false,
            'http_ok'          => $pr['http_ok'] ?? false,
            'http_code'        => $pr['http_code'],
            'message'          => $pr['message'],
            'planned_requests' => $pr['planned_requests'] ?? [],
        ]);

        exit;

    case 'start':
        $users    = max(1, min(20, (int) ($input['users'] ?? 3)));
        $duration = max(5, min(300, (int) ($input['duration'] ?? 60)));
        $profile  = in_array($input['profile'] ?? '', ['normal', 'burst', 'idle'], true)
            ? $input['profile'] : 'normal';
        $baseUrlRaw = isset($input['base_url']) && trim((string) $input['base_url']) !== ''
            ? (string) $input['base_url']
            : (getenv('SIM_UI_DEFAULT_BASE_URL') ?: 'http://web');

        $confirmUi = !empty($input['confirm_external']);
        $chk       = traffic_simulator_validate_target_url($baseUrlRaw, [
            'confirm_external' => $confirmUi,
            'trusted_cli'      => false,
        ]);
        if (!$chk['ok']) {
            if (($chk['code'] ?? '') === 'NEED_CONFIRM_EXTERNAL') {
                http_response_code(428);
                echo json_encode([
                    'success' => false,
                    'code'    => 'NEED_CONFIRM_EXTERNAL',
                    'message' => $chk['message'] ?? 'Confirmation required',
                ]);

                exit;
            }

            echo json_encode(['success' => false, 'message' => $chk['message'] ?? 'URL inválida']);

            exit;
        }

        $baseUrl = $chk['base'] ?? '';

        $body = [
            'users'            => $users,
            'duration'         => $duration,
            'profile'          => $profile,
            'base_url'         => $baseUrl,
            'confirm_external' => $confirmUi,
        ];
        if (!empty($input['routes_file'])) {
            $body['routes_file'] = (string) $input['routes_file'];
        }

        $r = simulator_ui_control_request('POST', '/start', $body, $controlBase, $token);
        if (!$r['ok']) {
            $code = isset($r['http_code']) && (int) $r['http_code'] === 428 ? 428 : 502;
            if (isset($r['http_code'])) {
                http_response_code($code === 428 ? 428 : 502);
            } else {
                http_response_code(502);
            }
            $resp = ['success' => false, 'message' => $r['error'] ?? 'Fallo start'];
            if (isset($r['data']) && is_array($r['data'])) {
                $resp['detail'] = $r['data'];
            }

            echo json_encode($resp);

            exit;
        }

        echo json_encode([
            'success' => true,
            'message' => "Simulación iniciada: {$users} usuarios · {$duration}s · {$profile}",
            'detail'  => $r['data'] ?? [],
        ]);

        exit;

    case 'stop':
        $r = simulator_ui_control_request('POST', '/stop', [], $controlBase, $token);
        echo json_encode([
            'success' => $r['ok'],
            'message' => $r['ok'] ? ($r['data']['message'] ?? 'Parado') : ($r['error'] ?? 'Error stop'),
            'detail'  => $r['data'] ?? null,
        ]);

        exit;

    case 'reset':
        $chk = simulator_ui_running_cached($controlBase, $token);
        if (($chk['running'] ?? false) === true) {
            echo json_encode(['success' => false, 'message' => 'Detén la simulación antes de resetear']);

            exit;
        }

        file_put_contents($metricsLog, '');
        file_put_contents($responseTimeLog, '');

        echo json_encode(['success' => true, 'message' => 'Logs reiniciados']);

        exit;

    default:
        http_response_code(400);
        echo json_encode(['error' => 'Unknown action']);

        exit;
}
