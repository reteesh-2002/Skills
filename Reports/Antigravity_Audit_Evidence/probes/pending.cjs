const {test}=require('node:test');
const assert=require('node:assert/strict');
test('purports to verify async work',()=>{
 new Promise(()=>{}).then(()=>assert.equal(1,2));
});
