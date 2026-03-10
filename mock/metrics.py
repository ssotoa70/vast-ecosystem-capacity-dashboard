"""Fake VAST Prometheus exporter that serves sample multi-cluster/tenant/view metrics."""

import http.server
import time
import math
import random

PORT = 9101

# Simulated ecosystem: 2 clusters, multiple tenants, multiple views per tenant
VIEWS = [
    # cluster, tenant, path, base_logical (bytes), drr
    ("ProdCluster-East", "studio-vfx",   "/vfx/shots",        8.5e12,  3.2),
    ("ProdCluster-East", "studio-vfx",   "/vfx/plates",       3.1e12,  2.8),
    ("ProdCluster-East", "studio-vfx",   "/vfx/renders",     12.0e12,  4.1),
    ("ProdCluster-East", "studio-audio",  "/audio/masters",    1.2e12,  1.5),
    ("ProdCluster-East", "studio-audio",  "/audio/sessions",   0.8e12,  1.3),
    ("ProdCluster-East", "engineering",   "/eng/builds",       2.0e12,  2.0),
    ("ProdCluster-West", "studio-vfx",   "/vfx/dailies",      5.5e12,  3.5),
    ("ProdCluster-West", "studio-vfx",   "/vfx/conform",      2.2e12,  2.9),
    ("ProdCluster-West", "archive",       "/archive/2025",    20.0e12,  5.0),
    ("ProdCluster-West", "archive",       "/archive/2024",    15.0e12,  4.8),
    ("ProdCluster-West", "engineering",   "/eng/ci-artifacts", 1.5e12,  1.8),
]


def generate_metrics():
    t = time.time()
    lines = []
    lines.append("# HELP vast_view_logical_capacity View Logical Capacity")
    lines.append("# TYPE vast_view_logical_capacity gauge")
    for cluster, tenant, path, base_logical, drr in VIEWS:
        # Add some time-based variation (+/- 5%)
        noise = 1.0 + 0.05 * math.sin(t / 300 + hash(path) % 100)
        logical = base_logical * noise
        lines.append(
            f'vast_view_logical_capacity{{cluster="{cluster}",tenant_name="{tenant}",path="{path}"}} {logical:.0f}'
        )

    lines.append("")
    lines.append("# HELP vast_view_physical_capacity View Physical Capacity")
    lines.append("# TYPE vast_view_physical_capacity gauge")
    for cluster, tenant, path, base_logical, drr in VIEWS:
        noise = 1.0 + 0.05 * math.sin(t / 300 + hash(path) % 100)
        logical = base_logical * noise
        physical = logical / drr
        lines.append(
            f'vast_view_physical_capacity{{cluster="{cluster}",tenant_name="{tenant}",path="{path}"}} {physical:.0f}'
        )

    return "\n".join(lines) + "\n"


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            body = generate_metrics().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress logs


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Mock VAST exporter serving on :{PORT}/metrics")
    server.serve_forever()
