<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Simulador de tráfico</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        :root {
            --sim-bg: #f1f5f9;
            --sim-card: #ffffff;
            --sim-accent: #0d6efd;
            --sim-border: #e2e8f0;
        }
        body { background: var(--sim-bg) !important; }
        .sim-section {
            border: 1px solid var(--sim-border);
            border-radius: 12px;
            background: var(--sim-card);
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        .sim-section > .sim-section-head {
            background: #fafbfc;
            border-bottom: 1px solid var(--sim-border);
            padding: 0.85rem 1.25rem;
            font-weight: 600;
        }
        .sim-section > .sim-section-body { padding: 1.25rem; }
        .sim-section h2 { font-size: 1.1rem; margin: 0; scroll-margin-top: 1rem; }
        .sim-status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
        .sim-status-dot.running { background: #22c55e; animation: pulse 1.2s infinite; }
        .sim-status-dot.stopped { background: #94a3b8; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
        @media (prefers-reduced-motion: reduce) {
            .sim-status-dot.running { animation: none; }
        }
        .log-preview {
            font-family: ui-monospace, 'Cascadia Code', 'Courier New', monospace;
            font-size: 0.82rem;
            background: #0f172a;
            color: #a3e635;
            border-radius: 8px;
            padding: 1rem;
            max-height: 220px;
            overflow-y: auto;
        }
        .profile-card {
            cursor: pointer;
            border: 2px solid transparent;
            border-radius: 10px;
            transition: border-color 0.15s, box-shadow 0.15s;
            background: #f8fafc;
        }
        .profile-card:hover, .profile-card.selected {
            border-color: #0d6efd;
            background: #e8f0fe;
        }
        .profile-card:focus-visible {
            outline: 2px solid #0d6efd;
            outline-offset: 2px;
        }
        .profile-hint { font-size: 0.75rem; color: #64748b; margin-top: 0.25rem; }
        .planned-urls {
            font-size: 0.8rem;
            max-height: 160px;
            overflow-y: auto;
        }
        .planned-urls li { word-break: break-all; }
        .preset-btn.active { font-weight: 600; }
        #toastRegion { position: fixed; bottom: 0; right: 0; z-index: 9999; max-width: min(420px, 92vw); }
    </style>
</head>
<body>
<a class="visually-hidden-focusable btn btn-sm btn-primary position-absolute top-0 start-0 m-2" href="#main">Saltar al contenido</a>

<div class="container py-4 pb-5" id="main">
    <header class="mb-4">
        <h1 class="h3 mb-2">
            <i class="bi bi-activity text-primary" aria-hidden="true"></i>
            Simulador de tráfico JMeter
        </h1>
        <p class="text-secondary mb-0">
            Genera peticiones HTTP de prueba contra la <strong>URL base</strong> que indiques.
            Los resultados de esta pantalla cuentan solo líneas con <code>source=simulator</code> en <code>metrics.log</code>.
        </p>
    </header>

    <div id="configError" class="alert alert-warning py-2 d-none small mb-3" role="alert"></div>
    <div id="pathHint" class="alert alert-danger py-2 d-none small mb-3" role="alert"></div>

    <!-- Bloque 1: Destino y plan -->
    <section class="sim-section" aria-labelledby="sec-destino">
        <div class="sim-section-head">
            <h2 id="sec-destino">1. Destino y plan de peticiones</h2>
        </div>
        <div class="sim-section-body">
            <p class="small text-muted mb-3">
                JMeter ejecuta rutas del taller (inicio, noticias, citaciones, etc.) <em>relativas</em> a la URL base.
                No confundir con la URL de esta interfaz (puerto 8890).
            </p>

            <div class="mb-3">
                <span class="form-label fw-semibold d-block mb-2">Destino rápido</span>
                <div class="btn-group flex-wrap" role="group" aria-label="Presets de URL base">
                    <button type="button" class="btn btn-outline-primary btn-sm preset-btn active" id="presetDocker" data-preset="docker">
                        Docker interno (<code>http://web</code>)
                    </button>
                    <button type="button" class="btn btn-outline-secondary btn-sm preset-btn" id="presetPublic" data-preset="public" disabled>
                        App pública
                    </button>
                </div>
                <p class="small text-muted mt-2 mb-0" id="presetHint">
                    En Compose usa <code>http://web</code> (servicio de la app en la red Docker).
                    No uses <code>localhost</code> desde el contenedor del simulador.
                </p>
            </div>

            <label class="form-label fw-semibold" for="baseUrlInput">URL base de la prueba</label>
            <input type="url" class="form-control mb-2" id="baseUrlInput" name="base_url" inputmode="url"
                   autocomplete="url" spellcheck="false" placeholder="http://web">

            <div class="form-check mb-3">
                <input class="form-check-input" type="checkbox" id="confirmExternal" name="confirm_external">
                <label class="form-check-label small" for="confirmExternal">
                    Confirmo carga autorizada si el host no está en <code>SIM_INTERNAL_HOSTS</code>
                </label>
            </div>

            <div id="flowStatus" class="alert alert-light border small py-2 mb-3" role="status">
                Indica la URL base y pulsa <strong>Comprobar destino</strong> o <strong>Iniciar prueba</strong>.
            </div>

            <h3 class="h6 fw-semibold mb-2">Rutas que JMeter solicitará</h3>
            <p class="small text-muted mb-2">Muestra del plan por defecto (peso relativo). Algunas peticiones sintéticas a <code>/does-not-exist</code> pueden aparecer en el log según el perfil.</p>
            <ul class="list-unstyled planned-urls mb-0" id="plannedList">
                <li class="text-muted">Cargando plan…</li>
            </ul>
        </div>
    </section>

    <!-- Bloque 2: Intensidad y controles -->
    <section class="sim-section" aria-labelledby="sec-carga">
        <div class="sim-section-head">
            <h2 id="sec-carga">2. Intensidad y ejecución</h2>
        </div>
        <div class="sim-section-body">
            <p class="small text-muted mb-3">
                El perfil ajusta pausas entre peticiones (no sustituye a los usuarios concurrentes).
            </p>
            <div class="mb-3">
                <div class="small fw-semibold text-secondary mb-2">Perfil de ritmo</div>
                <div class="row g-2" id="profileCards">
                    <div class="col-md-4">
                        <div class="profile-card text-center p-3 selected" tabindex="0" role="button"
                             data-profile="normal" aria-pressed="true"
                             onclick="selectProfile(this)" onkeydown="profileKey(event, this)">
                            <i class="bi bi-speedometer2 fs-4 text-primary" aria-hidden="true"></i>
                            <div class="small fw-semibold">Normal</div>
                            <div class="profile-hint">Pausas medias · ~3% errores sintéticos</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="profile-card text-center p-3" tabindex="0" role="button"
                             data-profile="burst" aria-pressed="false"
                             onclick="selectProfile(this)" onkeydown="profileKey(event, this)">
                            <i class="bi bi-lightning-charge fs-4 text-warning" aria-hidden="true"></i>
                            <div class="small fw-semibold">Burst</div>
                            <div class="profile-hint">Pausas cortas · más peticiones por segundo</div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="profile-card text-center p-3" tabindex="0" role="button"
                             data-profile="idle" aria-pressed="false"
                             onclick="selectProfile(this)" onkeydown="profileKey(event, this)">
                            <i class="bi bi-hourglass-split fs-4 text-secondary" aria-hidden="true"></i>
                            <div class="small fw-semibold">Idle</div>
                            <div class="profile-hint">Pausas largas · carga ligera</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label d-flex justify-content-between" for="usersSlider">
                    <span>Usuarios concurrentes</span>
                    <strong id="usersVal" class="font-variant-numeric">3</strong>
                </label>
                <input type="range" class="form-range" id="usersSlider" name="users" min="1" max="20" value="3"
                       oninput="document.getElementById('usersVal').textContent=this.value">
            </div>
            <div class="mb-4">
                <label class="form-label d-flex justify-content-between" for="durationSlider">
                    <span>Duración</span>
                    <strong id="durVal">60s</strong>
                </label>
                <input type="range" class="form-range" id="durationSlider" name="duration" min="5" max="300" step="5" value="60"
                       oninput="document.getElementById('durVal').textContent=this.value+'s'">
            </div>

            <details class="mb-4 border rounded p-3 bg-light">
                <summary class="fw-semibold small" style="cursor:pointer">Avanzado: rutas JSON en el worker</summary>
                <p class="small text-muted mt-2 mb-2">Ruta dentro del contenedor <code>traffic-simulator</code>. Vacío = plan por defecto.</p>
                <label class="form-label small mb-1" for="routesFile">Fichero JSON de rutas</label>
                <input type="text" class="form-control form-control-sm" id="routesFile" name="routes_file"
                       placeholder="/opt/traffic-simulator/conf/routes.json" spellcheck="false" autocomplete="off">
            </details>

            <div class="d-flex flex-wrap gap-2">
                <button class="btn btn-outline-primary" id="btnProbe" type="button" onclick="probeOnly()">
                    <i class="bi bi-check2-circle" aria-hidden="true"></i> Comprobar destino
                </button>
                <button class="btn btn-primary" id="btnStart" type="button" onclick="startSim()">
                    <i class="bi bi-play-fill" aria-hidden="true"></i> Iniciar prueba
                </button>
                <button class="btn btn-danger" id="btnStop" type="button" onclick="stopSim()" disabled>
                    <i class="bi bi-stop-fill" aria-hidden="true"></i> Detener
                </button>
                <button class="btn btn-outline-secondary" id="btnReset" type="button" onclick="resetLogs()"
                        title="Vacía metrics.log y response_time.log compartidos con la app">
                    <i class="bi bi-arrow-counterclockwise" aria-hidden="true"></i> Limpiar logs de métricas
                </button>
            </div>
        </div>
    </section>

    <!-- Bloque 3: Resultados y monitorización -->
    <section class="sim-section" aria-labelledby="sec-resultados">
        <div class="sim-section-head">
            <h2 id="sec-resultados">3. Resultados y monitorización</h2>
        </div>
        <div class="sim-section-body">
            <div class="card border mb-3">
                <div class="card-body d-flex align-items-center justify-content-between flex-wrap gap-2">
                    <div class="d-flex align-items-center gap-3">
                        <span id="statusDot" class="sim-status-dot stopped" aria-hidden="true"></span>
                        <div>
                            <div class="fw-semibold" id="statusLabel">Detenido</div>
                            <small class="text-muted" id="statusSub"></small>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold fs-4 text-primary font-variant-numeric" id="totalRequests">0</div>
                        <small class="text-muted">peticiones simuladas</small>
                    </div>
                </div>
            </div>

            <div class="form-check mb-2">
                <input class="form-check-input" type="checkbox" id="runScopeCurrent" checked>
                <label class="form-check-label small" for="runScopeCurrent">
                    Solo esta ejecución (<code>run_id</code> del worker; excluye líneas antiguas sin etiqueta)
                </label>
            </div>
            <p class="small text-muted mb-1" id="logFilterHint">Filtro: host según URL base del formulario.</p>
            <p class="small text-muted mb-3" id="appTrafficNote">
                Tráfico real de la app (<code>source=app</code>) no se incluye en estos contadores.
            </p>

            <div class="card border mb-3">
                <div class="card-header bg-white fw-semibold small">Estadísticas del simulador</div>
                <div class="card-body">
                    <div class="row text-center g-2">
                        <div class="col-6">
                            <div class="p-3 bg-success bg-opacity-10 rounded">
                                <span class="fs-4 fw-bold text-success font-variant-numeric" id="statOk">0</span>
                                <div class="small text-muted">Éxitos (2xx–3xx)</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-3 bg-danger bg-opacity-10 rounded">
                                <span class="fs-4 fw-bold text-danger font-variant-numeric" id="statErr">0</span>
                                <div class="small text-muted">Errores (4xx–5xx)</div>
                            </div>
                        </div>
                    </div>
                    <div class="small text-muted mt-2" id="statRecentHint"></div>
                    <div class="d-flex justify-content-between mt-3 small">
                        <span>Media respuesta</span>
                        <span id="statAvg" class="font-variant-numeric">&mdash;</span>
                    </div>
                    <div class="d-flex justify-content-between small">
                        <span>Máximo</span>
                        <span id="statMax" class="font-variant-numeric">&mdash;</span>
                    </div>
                    <p class="small text-muted mt-2 mb-0">
                        Las latencias leen <code>response_time.log</code> (compartido con la app); pueden incluir otras fuentes.
                    </p>
                </div>
            </div>

            <div class="card border mb-4">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span class="fw-semibold small">Últimas líneas (<code>source=simulator</code>)</span>
                    <span class="badge bg-secondary font-variant-numeric" id="logLines">0</span>
                </div>
                <div class="card-body p-2">
                    <pre class="log-preview mb-0" id="logPreview" aria-label="Vista previa de metrics.log">—</pre>
                </div>
            </div>

            <h3 class="h6 fw-semibold mb-2" id="sec-monitor">Enlaces externos</h3>
            <p class="small text-muted mb-3">
                <strong>Grafana</strong> (fila Simulador) refleja el mismo <code>metrics.log</code>.
                <strong>Dashboard JMeter</strong> aparece cuando el informe HTML esté listo (unos segundos tras finalizar).
            </p>
            <div class="d-grid gap-2" id="monitorLinks"></div>
        </div>
    </section>
</div>

<div id="toastRegion" aria-live="polite" aria-atomic="true"></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
let selectedProfile = 'normal';
let polling = null;
let prevRunning = null;
let suppressFinishToast = false;
let defaultBaseUrl = 'http://web';
let publicAppUrl = '';
let planRefreshTimer = null;

function profileKey(event, el) {
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        selectProfile(el);
    }
}

function selectProfile(el) {
    document.querySelectorAll('.profile-card').forEach(c => {
        c.classList.remove('selected');
        c.setAttribute('aria-pressed', 'false');
    });
    el.classList.add('selected');
    el.setAttribute('aria-pressed', 'true');
    selectedProfile = el.dataset.profile;
}

function toast(msg, type = 'success', ms = 5000) {
    const region = document.getElementById('toastRegion');
    const el = document.createElement('div');
    el.className = 'alert alert-' + type + ' shadow m-4 mb-2';
    el.innerHTML = msg;
    region.appendChild(el);
    setTimeout(() => el.remove(), ms);
}

function setFlowStatus(html, kind = 'light') {
    const el = document.getElementById('flowStatus');
    el.className = 'alert alert-' + kind + ' border small py-2 mb-3';
    el.innerHTML = html;
}

function apiStatusUrl() {
    const base = document.getElementById('baseUrlInput').value.trim() || defaultBaseUrl;
    const rf = document.getElementById('routesFile').value.trim();
    const runScope = document.getElementById('runScopeCurrent').checked ? 'current' : 'all';
    let q = 'base_url=' + encodeURIComponent(base) + '&run_scope=' + encodeURIComponent(runScope);
    if (rf) q += '&routes_file=' + encodeURIComponent(rf);
    return 'api.php?' + q;
}

function renderPlanned(requests) {
    const ul = document.getElementById('plannedList');
    if (!requests || !requests.length) {
        ul.innerHTML = '<li class="text-muted">No hay rutas válidas para esta URL base.</li>';
        return;
    }
    ul.innerHTML = requests.map(r =>
        '<li class="mb-1"><span class="badge bg-light text-dark border me-1">' + escapeHtml(r.method) +
        '</span> <code>' + escapeHtml(r.url) + '</code> <span class="text-muted">(peso ' + (r.weight || 1) + ')</span></li>'
    ).join('');
}

function escapeHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function schedulePlanRefresh() {
    clearTimeout(planRefreshTimer);
    planRefreshTimer = setTimeout(() => poll(), 400);
}

function applyPresets(data) {
    defaultBaseUrl = data.default_base_url || 'http://web';
    publicAppUrl = data.public_app_url || '';
    const pubBtn = document.getElementById('presetPublic');
    if (publicAppUrl) {
        pubBtn.disabled = false;
        pubBtn.title = publicAppUrl;
    }
    if (!document.getElementById('baseUrlInput').dataset.touched) {
        document.getElementById('baseUrlInput').value = defaultBaseUrl;
        setActivePreset('docker');
    }
}

function setActivePreset(which) {
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active', 'btn-primary'));
    document.querySelectorAll('.preset-btn').forEach(b => b.classList.add('btn-outline-secondary'));
    const btn = which === 'public' ? document.getElementById('presetPublic') : document.getElementById('presetDocker');
    btn.classList.add('active', 'btn-primary');
    btn.classList.remove('btn-outline-secondary');
    if (which === 'docker') {
        document.getElementById('presetDocker').classList.remove('btn-outline-secondary');
        document.getElementById('presetDocker').classList.add('btn-outline-primary');
    }
}

document.getElementById('presetDocker').addEventListener('click', () => {
    document.getElementById('baseUrlInput').value = defaultBaseUrl;
    document.getElementById('baseUrlInput').dataset.touched = '1';
    setActivePreset('docker');
    schedulePlanRefresh();
});

document.getElementById('presetPublic').addEventListener('click', () => {
    if (!publicAppUrl) return;
    document.getElementById('baseUrlInput').value = publicAppUrl;
    document.getElementById('baseUrlInput').dataset.touched = '1';
    setActivePreset('public');
    document.getElementById('presetHint').textContent =
        'URL pública: el worker debe poder alcanzarla desde la red Docker. Evita localhost.';
    schedulePlanRefresh();
});

document.getElementById('baseUrlInput').addEventListener('input', () => {
    document.getElementById('baseUrlInput').dataset.touched = '1';
    schedulePlanRefresh();
});
document.getElementById('runScopeCurrent').addEventListener('change', () => schedulePlanRefresh());
document.getElementById('routesFile').addEventListener('input', schedulePlanRefresh);

async function runProbe(showToastOnOk) {
    const body = {
        action: 'probe',
        base_url: document.getElementById('baseUrlInput').value.trim(),
        confirm_external: document.getElementById('confirmExternal').checked
    };
    const rf = document.getElementById('routesFile').value.trim();
    if (rf) body.routes_file = rf;

    const res = await fetch('api.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    let j = {};
    try { j = await res.json(); } catch (_) {}

    if (j.planned_requests) renderPlanned(j.planned_requests);

    if (res.status === 503) {
        const t = j.message || 'Servicio no configurado (token o API)';
        setFlowStatus(t, 'warning');
        if (showToastOnOk !== false) toast(t, 'warning');
        return null;
    }
    if (res.status === 428 || j.code === 'NEED_CONFIRM_EXTERNAL') {
        setFlowStatus('Marca la casilla de confirmación para comprobar URLs externas.', 'warning');
        toast('Marca la casilla de confirmación para URLs externas.', 'warning');
        return null;
    }
    if (j.success !== true) {
        const t = j.message || 'No se pudo comprobar el destino';
        setFlowStatus('<strong>Sin respuesta o URL inválida:</strong> ' + escapeHtml(t), 'danger');
        if (showToastOnOk !== false) toast(t, 'danger', 7000);
        return null;
    }

    const code = j.http_code != null ? j.http_code : '—';
    const msg = j.message || 'OK';
    const warn = j.http_ok === false && j.reachable
        ? ' <span class="text-warning">(HTTP no exitoso en /; la simulación puede registrar errores)</span>'
        : '';
    setFlowStatus(
        '<strong>Destino comprobado</strong> · HTTP <code>' + code + '</code> · ' + escapeHtml(msg) + warn +
        ' <span class="text-muted">(' + new Date().toLocaleString('es') + ')</span>',
        j.http_ok === false ? 'warning' : 'success'
    );
    if (showToastOnOk !== false) {
        toast('<strong>Destino OK</strong> · HTTP ' + code + ' — ' + msg, j.http_ok === false ? 'warning' : 'success');
    }
    return j;
}

async function poll() {
    try {
        const r = await fetch(apiStatusUrl());
        const data = await r.json();

        applyPresets(data);
        if (data.planned_requests) renderPlanned(data.planned_requests);

        if (data.error) {
            document.getElementById('configError').classList.remove('d-none');
            document.getElementById('configError').textContent = data.error;
            document.getElementById('btnStart').disabled = true;
            document.getElementById('btnProbe').disabled = true;
        } else {
            document.getElementById('configError').classList.add('d-none');
            document.getElementById('configError').textContent = '';
            document.getElementById('btnStart').disabled = !!data.running;
            document.getElementById('btnProbe').disabled = !!data.running;
        }
        document.getElementById('btnStop').disabled = !data.running;

        const st = data.stats || {};
        document.getElementById('totalRequests').textContent = st.total_requests || 0;
        document.getElementById('statOk').textContent = st.success_requests ?? 0;
        document.getElementById('statErr').textContent = st.error_requests ?? 0;

        const rw = st.recent_window || 20;
        const lf = data.log_filters || {};
        let filterNote = 'Host: ' + (lf.target_host || '—');
        if (lf.run_scope === 'current' && lf.run_id) {
            filterNote += ' · run: ' + lf.run_id;
        } else if (lf.run_scope === 'current') {
            filterNote += ' · sin run_id activo (histórico del host)';
        } else {
            filterNote += ' · todas las ejecuciones del host';
        }
        document.getElementById('logFilterHint').textContent = filterNote;
        if (typeof st.recent_success === 'number') {
            document.getElementById('statRecentHint').textContent =
                'Últimas ' + rw + ' líneas (filtro aplicado): ' + st.recent_success + ' éxito, ' + (st.recent_errors || 0) + ' error';
        } else {
            document.getElementById('statRecentHint').textContent = '';
        }

        document.getElementById('statAvg').textContent =
            st.avg_response_time ? st.avg_response_time + ' s' : '—';
        document.getElementById('statMax').textContent =
            st.max_response_time ? st.max_response_time + ' s' : '—';

        const appTotal = data.stats_app && data.stats_app.total_requests;
        if (typeof appTotal === 'number' && appTotal > 0) {
            document.getElementById('appTrafficNote').textContent =
                'Hay ' + appTotal + ' líneas de tráfico real (source=app) en el log; no se incluyen arriba.';
        }

        const dot = document.getElementById('statusDot');
        if (data.running) {
            dot.className = 'sim-status-dot running';
            document.getElementById('statusLabel').textContent = 'En marcha';
            const wd = data.worker_detail;
            let sub = 'JMeter activo';
            if (wd && wd.logs) {
                sub = 'JMeter · ' + (wd.jmeter && wd.jmeter.imported_samples != null
                    ? wd.jmeter.imported_samples + ' muestras importadas'
                    : 'importando muestras');
            }
            document.getElementById('statusSub').textContent = sub;
        } else {
            dot.className = 'sim-status-dot stopped';
            document.getElementById('statusLabel').textContent = 'Detenido';
            const jm = data.jmeter || {};
            document.getElementById('statusSub').textContent = jm.imported_samples
                ? ('Última ejecución · ' + jm.imported_samples + ' muestras')
                : 'Sin simulación en curso';
        }

        const ph = document.getElementById('pathHint');
        const hints = [];
        if (data.diagnostics) {
            const d = data.diagnostics;
            if (!d.logs_dir_exists) hints.push('No existe carpeta logs: ' + d.logs_dir);
            if (!d.logs_dir_writable) hints.push('Carpeta logs no escribible desde la UI');
        }
        if (data.running && st.total_requests === 0) {
            hints.push('Simulación en marcha sin líneas simulator aún; revisa la URL base (p. ej. http://web).');
        }
        if (hints.length) {
            ph.classList.remove('d-none');
            ph.textContent = hints.join(' · ');
        } else {
            ph.classList.add('d-none');
        }

        if (prevRunning === true && data.running === false && !suppressFinishToast) {
            toast('<strong>Simulación finalizada</strong> a las ' + new Date().toLocaleTimeString('es'), 'info', 7000);
        }
        if (suppressFinishToast) suppressFinishToast = false;
        prevRunning = data.running;

        const preview = data.log_preview || {};
        document.getElementById('logLines').textContent =
            (preview.total != null ? preview.total : 0) + ' sim';
        document.getElementById('logPreview').textContent =
            (preview.lines && preview.lines.length) ? preview.lines.join('\n') : '(vacío)';

        const links = document.getElementById('monitorLinks');
        links.innerHTML = '';
        function addLink(href, label, icon, extraClass, disabled, hint) {
            if (!href && !disabled) return;
            if (disabled) {
                const span = document.createElement('span');
                span.className = 'btn btn-sm btn-outline-secondary disabled';
                span.innerHTML = '<i class="bi ' + icon + '" aria-hidden="true"></i> ' + label + (hint ? ' — ' + hint : '');
                links.appendChild(span);
                return;
            }
            const a = document.createElement('a');
            a.href = href;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';
            a.className = 'btn btn-sm ' + (extraClass || 'btn-outline-secondary');
            a.innerHTML = '<i class="bi ' + icon + '" aria-hidden="true"></i> ' + label;
            links.appendChild(a);
        }
        if (data.monitoring) {
            addLink(data.monitoring.prometheus, 'Prometheus', 'bi-graph-up');
            addLink(data.monitoring.grafana, 'Grafana (dashboard)', 'bi-display', 'btn-outline-primary');
        }
        if (data.jmeter && data.jmeter.enabled) {
            if (data.jmeter.report_url && data.jmeter.report_ready) {
                addLink(data.jmeter.report_url, 'Dashboard JMeter', 'bi-speedometer2', 'btn-outline-primary');
            } else if (data.running) {
                addLink(null, 'Dashboard JMeter', 'bi-speedometer2', '', true, 'disponible al finalizar');
            }
            addLink(data.jmeter.results_jtl_url, 'Descargar JTL', 'bi-filetype-csv');
            addLink(data.jmeter.jmeter_log_url, 'jmeter.log', 'bi-file-text');
        }
    } catch (e) {
        console.error(e);
    }
}

async function probeOnly() {
    const b = document.getElementById('btnProbe');
    b.disabled = true;
    const prev = b.innerHTML;
    b.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Comprobando…';
    setFlowStatus('Comprobando destino…', 'secondary');
    try {
        await runProbe(true);
    } finally {
        b.disabled = false;
        b.innerHTML = prev;
    }
}

async function startSim() {
    const btn = document.getElementById('btnStart');
    const btnProbe = document.getElementById('btnProbe');
    const prevStart = btn.innerHTML;
    btn.disabled = true;
    btnProbe.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Iniciando…';
    setFlowStatus('Paso 1/2: comprobando que el destino responde…', 'secondary');
    const pr = await runProbe(false);
    if (pr == null) {
        btn.disabled = false;
        btnProbe.disabled = false;
        btn.innerHTML = prevStart;
        return;
    }

    setFlowStatus('Paso 2/2: enviando orden de inicio al worker…', 'primary');
    toast('Destino verificado. <strong>Iniciando simulación</strong>…', 'success', 3500);

    const body = {
        action: 'start',
        users: +document.getElementById('usersSlider').value,
        duration: +document.getElementById('durationSlider').value,
        profile: selectedProfile,
        base_url: document.getElementById('baseUrlInput').value.trim(),
        confirm_external: document.getElementById('confirmExternal').checked
    };
    const rf = document.getElementById('routesFile').value.trim();
    if (rf) body.routes_file = rf;

    const res = await fetch('api.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    let j = {};
    try { j = await res.json(); } catch (_) {}

    if (res.status === 428 || j.code === 'NEED_CONFIRM_EXTERNAL') {
        toast('Marca la casilla de confirmación para URLs externas.', 'warning');
        btn.disabled = false;
        btnProbe.disabled = false;
        btn.innerHTML = prevStart;
        return;
    }
    if (!j.success) {
        toast(j.message || 'Error', 'danger', 7000);
        setFlowStatus('<strong>No se pudo iniciar:</strong> ' + escapeHtml(j.message || 'Error'), 'danger');
        btn.disabled = false;
        btnProbe.disabled = false;
        btn.innerHTML = prevStart;
        return;
    }

    setFlowStatus(
        '<strong>Simulación en curso</strong> · Orden aceptada a las ' + new Date().toLocaleString('es') + '.',
        'success'
    );
    toast('<strong>Simulación iniciada</strong> a las ' + new Date().toLocaleTimeString('es'), 'success', 6500);
    poll();
    btn.innerHTML = prevStart;
    btnProbe.disabled = false;
}

async function stopSim() {
    const res = await fetch('api.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'stop' })
    });
    let j = {};
    try { j = await res.json(); } catch (_) {}
    if (j.success !== false && res.ok) suppressFinishToast = true;
    setFlowStatus('Simulación detenida. Puedes comprobar el destino o iniciar otra prueba.', 'secondary');
    toast(j.message || ('HTTP ' + res.status), (j.success !== undefined ? j.success : res.ok) ? 'success' : 'danger', 6000);
    poll();
}

async function resetLogs() {
    if (!confirm('¿Vaciar metrics.log y response_time.log? Afecta a la app y a Grafana hasta que vuelva a haber tráfico.')) {
        return;
    }
    const res = await fetch('api.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'reset' })
    });
    const j = await res.json().catch(() => ({}));
    toast(j.message || '', j.success ? 'success' : 'warning');
    poll();
}

polling = setInterval(poll, 2000);
poll();
</script>
</body>
</html>
