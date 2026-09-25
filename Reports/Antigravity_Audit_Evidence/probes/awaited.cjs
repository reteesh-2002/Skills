const {test}=require('node:test');
const assert=require('node:assert/strict');
test('actually awaits work',{timeout:100},async()=>{
 await new Promise(()=>{});
 assert.equal(1,2);
});
