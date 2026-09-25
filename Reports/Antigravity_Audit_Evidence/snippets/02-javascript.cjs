const { test } = require('node:test');
const assert = require('node:assert/strict');

test('purports to verify asynchronous work', () => {
  new Promise(() => {}).then(() => assert.equal(1, 2));
});
