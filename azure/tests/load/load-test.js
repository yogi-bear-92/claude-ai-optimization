// K6 load test script placeholder
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 10,
  duration: '30s',
};

export default function() {
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  
  let response = http.get(`${baseUrl}/health`);
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
  
  sleep(1);
}