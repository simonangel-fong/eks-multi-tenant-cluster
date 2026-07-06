import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'https://voting.arguswatcher.net';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '3m', target: 20 },
    { duration: '2m', target: 20 },
    { duration: '1m', target: 0 },
  ],
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
  const r = Math.random();

  if (r < 0.7) {
    const opt = data.options[Math.floor(Math.random() * data.options.length)];
    const vote = http.post(
      `${BASE_URL}/polls/${data.pollId}/vote`,
      JSON.stringify({ option_id: opt.id }),
      {
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': `load-${__VU}-${__ITER}-${Date.now()}`,
        },
      },
    );
    check(vote, { 'vote ok': (res) => res.status === 200 || res.status === 201 });
  } else if (r < 0.9) {
    const results = http.get(`${BASE_URL}/polls/${data.pollId}/results`);
    check(results, { 'results ok': (res) => res.status === 200 });
  } else {
    const list = http.get(`${BASE_URL}/polls`);
    check(list, { 'list ok': (res) => res.status === 200 });
  }

  sleep(0.5);
}
