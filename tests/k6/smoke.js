import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'https://voting.arguswatcher.net';

export const options = {
  vus: 1,
  duration: '30s',
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/polls`,
    JSON.stringify({
      title: 'best pet',
      options: ['cat', 'dog', 'polly'],
    }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  check(res, { 'poll created': (r) => r.status === 201 || r.status === 200 });
  const body = res.json();
  return { pollId: body.id, options: body.options };
}

export default function (data) {
  const list = http.get(`${BASE_URL}/polls`);
  check(list, { 'list 200': (r) => r.status === 200 });

  const results = http.get(`${BASE_URL}/polls/${data.pollId}/results`);
  check(results, { 'results 200': (r) => r.status === 200 });

  const opt = data.options[Math.floor(Math.random() * data.options.length)];
  const vote = http.post(
    `${BASE_URL}/polls/${data.pollId}/vote`,
    JSON.stringify({ option_id: opt.id }),
    {
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': `smoke-${__VU}-${__ITER}`,
      },
    },
  );
  check(vote, { 'vote accepted': (r) => r.status === 200 || r.status === 201 });

  sleep(1);
}
