# Deployment Guide

Step-by-step guide to deploy the VAST Ecosystem Capacity Dashboard in your environment.

## Prerequisites

| Requirement | Minimum Version | Notes |
|-------------|-----------------|-------|
| VAST Cluster | 5.3+ | Tenant Admin API token & Prometheus metrics support |
| Prometheus | 2.45+ | Scrapes VAST `/api/prometheusmetrics/views` |
| Grafana | 10.x | Tested on 10.4; schema version 39 |
| Docker (optional) | 20+ | Only if using the included docker-compose demo |

You also need:
- A **Tenant Admin** user on each tenant you want to monitor
- Each user must have permissions to query `/api/prometheusmetrics/views`
- Network access from Prometheus to your VAST VMS VIP(s) on port 443

---

## Step 1: Configure Prometheus

Open `prometheus.yml`. There is **one scrape job per (cluster, tenant) combination**.

### What to change per job

Each job block has 5 fields you must customize:

```yaml
  - job_name: 'cluster1-tenant-a'                    # 1. Unique job name
    # ...
    static_configs:
      - targets: ['CLUSTER1_VMS_HOST:443']            # 2. VMS VIP for this cluster
    http_headers:
      X-Tenant-Name:
        values:
          - "tenant-A"                                # 3. Tenant name as defined in VAST
    basic_auth:
      username: 'CLUSTER1_TENANT_A_USER'              # 4. Tenant Admin username
      password: 'CLUSTER1_TENANT_A_PASS'              # 5. Tenant Admin password
```

### Example: Your environment has 2 clusters

Suppose you have:
- **Cluster "prod-east"** (VMS VIP: `10.1.0.10`) with tenants `vfx` and `audio`
- **Cluster "prod-west"** (VMS VIP: `10.2.0.10`) with tenants `vfx` and `archive`

You need **4 scrape jobs**:

```yaml
scrape_configs:
  - job_name: 'prod-east-vfx'
    scheme: https
    scrape_interval: 120s
    scrape_timeout: 90s
    metrics_path: '/api/prometheusmetrics/views'
    static_configs:
      - targets: ['10.1.0.10:443']
    http_headers:
      X-Tenant-Name:
        values: ["vfx"]
    basic_auth:
      username: 'vfx-admin'
      password: 'secret1'
    tls_config:
      insecure_skip_verify: true

  - job_name: 'prod-east-audio'
    scheme: https
    scrape_interval: 120s
    scrape_timeout: 90s
    metrics_path: '/api/prometheusmetrics/views'
    static_configs:
      - targets: ['10.1.0.10:443']
    http_headers:
      X-Tenant-Name:
        values: ["audio"]
    basic_auth:
      username: 'audio-admin'
      password: 'secret2'
    tls_config:
      insecure_skip_verify: true

  - job_name: 'prod-west-vfx'
    scheme: https
    scrape_interval: 120s
    scrape_timeout: 90s
    metrics_path: '/api/prometheusmetrics/views'
    static_configs:
      - targets: ['10.2.0.10:443']
    http_headers:
      X-Tenant-Name:
        values: ["vfx"]
    basic_auth:
      username: 'vfx-admin-west'
      password: 'secret3'
    tls_config:
      insecure_skip_verify: true

  - job_name: 'prod-west-archive'
    scheme: https
    scrape_interval: 120s
    scrape_timeout: 90s
    metrics_path: '/api/prometheusmetrics/views'
    static_configs:
      - targets: ['10.2.0.10:443']
    http_headers:
      X-Tenant-Name:
        values: ["archive"]
    basic_auth:
      username: 'archive-admin'
      password: 'secret4'
    tls_config:
      insecure_skip_verify: true
```

### Adding more clusters or tenants later

Copy any existing job block and change the 5 fields. The `cluster` label in the VAST metrics output will automatically identify which cluster the data comes from — no relabeling needed.

### TLS certificates

The template uses `insecure_skip_verify: true` for self-signed certificates. If your VAST clusters use CA-signed certificates, set this to `false` and optionally provide the CA cert:

```yaml
    tls_config:
      insecure_skip_verify: false
      ca_file: /path/to/ca.crt
```

### Start Prometheus

```bash
prometheus --config.file=prometheus.yml
```

Verify all targets at `http://localhost:9090/targets` — every job should show **UP**.

---

## Step 2: Import the Grafana Dashboard

1. Open Grafana (default: `http://localhost:3000`)
2. Go to **Dashboards** > **New** > **Import**
3. Upload `vast-tenant-capacity-dashboard.json`
4. In the import dialog, select your **Prometheus** data source
5. Click **Import**

The dashboard appears in the **VAST** folder (or root, depending on your Grafana setup).

---

## Step 3: Verify the Dashboard

1. Open the imported dashboard
2. Check the **Cluster** dropdown — it should list your VAST cluster names
3. Check the **Tenant** dropdown — it should list the tenants you configured
4. Check the **View** dropdown — it should list the view paths visible to each tenant
5. With all set to "All", you see your full ecosystem capacity

If dropdowns are empty, check:
- Prometheus targets are UP
- The metrics `vast_view_logical_capacity` and `vast_view_physical_capacity` exist in Prometheus
- The Grafana datasource points to the correct Prometheus URL

---

## Step 4 (Optional): Run the Demo Stack

To try the dashboard with simulated data before connecting to your real VAST clusters:

```bash
docker compose up -d
```

This starts:
- **Mock exporter** (port 9101) — simulates 2 clusters, 4 tenants, 11 views
- **Prometheus** (port 9090) — scrapes the mock exporter
- **Grafana** (port 3000) — serves the dashboard

Open `http://localhost:3000/d/vast-ecosystem-capacity` (login: `admin`/`admin`).

To stop: `docker compose down`

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Prometheus target shows DOWN | Network or auth failure | Check VMS VIP reachability, verify username/password |
| Dropdowns empty | No metrics scraped yet | Wait 2-3 minutes, check Prometheus targets |
| "No data" in panels | Wrong datasource selected | Use the datasource dropdown to select Prometheus |
| Missing tenants | Missing scrape job | Add a job block for the missing (cluster, tenant) pair |
| Wrong cluster name | VAST sets `cluster` label | The label comes from VAST, not from Prometheus config |

---

## Security Notes

- Store Prometheus passwords in a secrets manager or use environment variable substitution in `prometheus.yml`
- The `X-Tenant-Name` header scopes all returned metrics to that tenant — no cross-tenant data leakage
- Grafana never connects to VAST directly — all data flows through Prometheus
- Consider enabling Grafana authentication and RBAC for production use
