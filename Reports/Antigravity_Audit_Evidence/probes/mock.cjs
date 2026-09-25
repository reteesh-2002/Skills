const {test}=require('node:test');
const assert=require('node:assert/strict');
function productionLookup(){throw new Error('real database unavailable')}
function service(lookup=productionLookup){return lookup()}
test('mock-only boundary',()=>assert.equal(service(()=>42),42));
