const {test}=require('node:test');
function productionLookup(){throw new Error('real database unavailable')}
function service(lookup=productionLookup){return lookup()}
test('unmocked boundary',()=>service());
