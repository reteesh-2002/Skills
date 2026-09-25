test('actually awaits the operation', { timeout: 100 }, async () => {
  await operationUnderTest();
  assert.equal(observedEffect(), expectedEffect);
});
