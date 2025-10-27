// ============================================================================
// K6 Performance Test for SDR-O-RAN Platform
// ============================================================================
// Version: 1.0.0
// Date: 2025-10-27
// Author: thc1006@ieee.org
//
// Test Scenarios:
// 1. API Gateway load test (HTTP)
// 2. gRPC service performance test
// 3. PQC cryptography overhead benchmark
// 4. DRL model inference latency test
//
// Usage:
//   k6 run k6-performance-test.js
//   k6 run --vus 100 --duration 5m k6-performance-test.js
// ============================================================================

import http from 'k6/http';
import grpc from 'k6/net/grpc';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ============================================================================
// Configuration
// ============================================================================

const BASE_URL = __ENV.SDR_API_URL || 'https://sdr-staging.example.com';
const GRPC_URL = __ENV.SDR_GRPC_URL || 'sdr-grpc-staging.example.com:50051';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const grpcLatency = new Trend('grpc_latency');
const pqcLatency = new Trend('pqc_latency');
const requestCount = new Counter('request_count');

// ============================================================================
// Test Options
// ============================================================================

export const options = {
  scenarios: {
    // Scenario 1: API Gateway load test
    api_load_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up to 50 users
        { duration: '5m', target: 50 },   // Stay at 50 users
        { duration: '2m', target: 100 },  // Ramp up to 100 users
        { duration: '5m', target: 100 },  // Stay at 100 users
        { duration: '2m', target: 0 },    // Ramp down to 0 users
      ],
      gracefulRampDown: '30s',
      exec: 'apiLoadTest',
    },

    // Scenario 2: gRPC performance test
    grpc_test: {
      executor: 'constant-vus',
      vus: 20,
      duration: '5m',
      exec: 'grpcTest',
      startTime: '1m',  // Start after API test begins
    },

    // Scenario 3: Spike test
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 300 },  // Sudden spike
        { duration: '1m', target: 300 },   // Sustain spike
        { duration: '30s', target: 0 },    // Drop to zero
      ],
      exec: 'spikeTest',
      startTime: '10m',  // Start after other tests
    },
  },

  // Thresholds (SLOs)
  thresholds: {
    'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // 95th percentile < 500ms
    'http_req_failed': ['rate<0.01'],                   // Error rate < 1%
    'grpc_latency': ['p(95)<200'],                      // gRPC 95th < 200ms
    'errors': ['rate<0.05'],                            // Total error rate < 5%
  },

  // Output results to InfluxDB (optional)
  // ext: {
  //   loadimpact: {
  //     projectID: 3xxxxxx,
  //     name: 'SDR Platform Performance Test'
  //   }
  // }
};

// ============================================================================
// Test Setup
// ============================================================================

export function setup() {
  console.log('🚀 Starting SDR Platform performance tests...');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`gRPC URL: ${GRPC_URL}`);

  // Health check before starting tests
  const healthRes = http.get(`${BASE_URL}/healthz`);
  check(healthRes, {
    'Health check passed': (r) => r.status === 200,
  });

  return {
    timestamp: new Date().toISOString(),
  };
}

// ============================================================================
// Scenario 1: API Gateway Load Test
// ============================================================================

export function apiLoadTest() {
  const endpoints = [
    { path: '/healthz', method: 'GET', name: 'Health Check' },
    { path: '/api/v1/sdr/status', method: 'GET', name: 'SDR Status' },
    { path: '/api/v1/usrp/config', method: 'GET', name: 'USRP Config' },
    { path: '/api/v1/pqc/public-key', method: 'GET', name: 'PQC Public Key' },
    { path: '/metrics', method: 'GET', name: 'Prometheus Metrics' },
  ];

  // Pick random endpoint
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const url = `${BASE_URL}${endpoint.path}`;

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test/1.0',
    },
    tags: {
      endpoint: endpoint.name,
    },
  };

  const startTime = Date.now();
  const res = http.get(url, params);
  const duration = Date.now() - startTime;

  // Record metrics
  apiLatency.add(duration);
  requestCount.add(1);

  // Assertions
  const checkResult = check(res, {
    [`${endpoint.name}: status is 200`]: (r) => r.status === 200,
    [`${endpoint.name}: response time < 500ms`]: (r) => r.timings.duration < 500,
  });

  if (!checkResult) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }

  sleep(1);  // 1 second think time
}

// ============================================================================
// Scenario 2: gRPC Performance Test
// ============================================================================

export function grpcTest() {
  const client = new grpc.Client();
  client.load(['../../../03-Implementation/integration/sdr-oran-connector/proto'], 'sdr_service.proto');

  try {
    client.connect(GRPC_URL, {
      plaintext: true,
      timeout: '10s',
    });

    const startTime = Date.now();
    const response = client.invoke('sdr.SDRService/GetSDRStatus', {
      sdr_id: 'usrp-001',
    });
    const duration = Date.now() - startTime;

    grpcLatency.add(duration);

    check(response, {
      'gRPC status is OK': (r) => r && r.status === grpc.StatusOK,
      'gRPC latency < 200ms': (r) => duration < 200,
    });

  } catch (error) {
    console.error(`gRPC error: ${error}`);
    errorRate.add(1);
  } finally {
    client.close();
  }

  sleep(2);
}

// ============================================================================
// Scenario 3: Spike Test (Stress Test)
// ============================================================================

export function spikeTest() {
  const res = http.get(`${BASE_URL}/api/v1/sdr/status`);

  check(res, {
    'Spike test: status is 200 or 503': (r) => r.status === 200 || r.status === 503,
  });

  if (res.status !== 200) {
    errorRate.add(1);
    console.warn(`Spike test: Got ${res.status} status`);
  }

  sleep(0.5);  // Shorter think time for spike
}

// ============================================================================
// PQC Cryptography Benchmark
// ============================================================================

export function pqcBenchmark() {
  const payload = {
    algorithm: 'kyber1024',
    operation: 'encapsulate',
    public_key: 'BASE64_ENCODED_PUBLIC_KEY',
  };

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const startTime = Date.now();
  const res = http.post(`${BASE_URL}/api/v1/pqc/encapsulate`, JSON.stringify(payload), params);
  const duration = Date.now() - startTime;

  pqcLatency.add(duration);

  check(res, {
    'PQC encapsulation: status is 200': (r) => r.status === 200,
    'PQC encapsulation: latency < 100ms': (r) => duration < 100,
  });

  sleep(1);
}

// ============================================================================
// Test Teardown
// ============================================================================

export function teardown(data) {
  console.log('✅ Performance tests completed');
  console.log(`Started at: ${data.timestamp}`);
  console.log(`Finished at: ${new Date().toISOString()}`);
}

// ============================================================================
// Summary Report
// ============================================================================

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'performance-report.json': JSON.stringify(data, null, 2),
    'performance-report.html': htmlReport(data),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;

  let summary = `\n${indent}================================================================================\n`;
  summary += `${indent}📊 SDR Platform Performance Test Summary\n`;
  summary += `${indent}================================================================================\n\n`;

  // Scenarios
  summary += `${indent}Scenarios:\n`;
  for (const [name, scenario] of Object.entries(data.metrics)) {
    if (name.startsWith('scenario_')) {
      summary += `${indent}  - ${name}: ${scenario.values.count} iterations\n`;
    }
  }

  // HTTP metrics
  summary += `\n${indent}HTTP Metrics:\n`;
  summary += `${indent}  - Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `${indent}  - Failed requests: ${data.metrics.http_req_failed.values.rate * 100}%\n`;
  summary += `${indent}  - Request duration (p95): ${data.metrics.http_req_duration.values['p(95)']}ms\n`;
  summary += `${indent}  - Request duration (p99): ${data.metrics.http_req_duration.values['p(99)']}ms\n`;

  // Custom metrics
  if (data.metrics.api_latency) {
    summary += `\n${indent}API Latency:\n`;
    summary += `${indent}  - Median: ${data.metrics.api_latency.values.med}ms\n`;
    summary += `${indent}  - p95: ${data.metrics.api_latency.values['p(95)']}ms\n`;
  }

  if (data.metrics.grpc_latency) {
    summary += `\n${indent}gRPC Latency:\n`;
    summary += `${indent}  - Median: ${data.metrics.grpc_latency.values.med}ms\n`;
    summary += `${indent}  - p95: ${data.metrics.grpc_latency.values['p(95)']}ms\n`;
  }

  // Thresholds
  summary += `\n${indent}Thresholds:\n`;
  for (const [name, threshold] of Object.entries(data.thresholds)) {
    const status = threshold.ok ? '✅' : '❌';
    summary += `${indent}  ${status} ${name}\n`;
  }

  summary += `\n${indent}================================================================================\n`;

  return summary;
}

function htmlReport(data) {
  return `
<!DOCTYPE html>
<html>
<head>
  <title>SDR Platform Performance Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #2c3e50; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
    th { background-color: #3498db; color: white; }
    .pass { color: green; font-weight: bold; }
    .fail { color: red; font-weight: bold; }
  </style>
</head>
<body>
  <h1>SDR Platform Performance Test Report</h1>
  <p><strong>Test Date:</strong> ${new Date().toISOString()}</p>

  <h2>Summary</h2>
  <table>
    <tr>
      <th>Metric</th>
      <th>Value</th>
    </tr>
    <tr>
      <td>Total Requests</td>
      <td>${data.metrics.http_reqs.values.count}</td>
    </tr>
    <tr>
      <td>Failed Requests</td>
      <td>${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%</td>
    </tr>
    <tr>
      <td>Request Duration (p95)</td>
      <td>${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms</td>
    </tr>
    <tr>
      <td>Request Duration (p99)</td>
      <td>${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms</td>
    </tr>
  </table>

  <h2>Thresholds</h2>
  <table>
    <tr>
      <th>Threshold</th>
      <th>Status</th>
    </tr>
    ${Object.entries(data.thresholds).map(([name, threshold]) => `
    <tr>
      <td>${name}</td>
      <td class="${threshold.ok ? 'pass' : 'fail'}">${threshold.ok ? 'PASS' : 'FAIL'}</td>
    </tr>
    `).join('')}
  </table>
</body>
</html>
  `;
}

// ============================================================================
// End of K6 Performance Test
// ============================================================================
