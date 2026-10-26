const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');

for (const file of ['index.html', 'badge-preview.html']) {
  const source = fs.readFileSync(file, 'utf8').match(/<script>([\s\S]*?)<\/script>/)[1];
  const elements = Object.fromEntries(['hall', 'meal', 'status', 'menu'].map(id => [id, {
    value: id === 'hall' ? 'stokely' : '', addEventListener() {}, replaceChildren() {}
  }]));
  const context = vm.createContext({Intl, Date, document: {getElementById: id => elements[id]},
    fetch: () => new Promise(() => {})});
  vm.runInContext(source, context);
  const evaluate = expression => vm.runInContext(expression, context);
  for (const [time, expected] of [
    ['2026-10-26T04:00:00Z','Breakfast'],
    ['2026-10-26T14:29:59Z','Breakfast'],
    ['2026-10-26T14:30:00Z','Lunch'],
    ['2026-10-26T20:29:59Z','Lunch'],
    ['2026-10-26T20:30:00Z','Dinner'],
    ['2026-10-27T03:59:59Z','Dinner'],
    ['2026-12-01T15:30:00Z','Lunch'],
    ['2026-12-01T21:30:00Z','Dinner']
  ]) assert.equal(evaluate(`defaultMeal(new Date('${time}'))`), expected);

  for (const hall of ['stokely','rocky-top','southern-kitchen']) {
    const data = JSON.parse(fs.readFileSync(`data/${hall}.json`, 'utf8')).stations;
    context.testStations = data;
    const result = JSON.parse(evaluate(`JSON.stringify(orderedStations('${hall}', testStations))`));
    assert.equal(result.length, Object.keys(data).length);
    if (hall === 'southern-kitchen') assert.deepEqual(result, Object.values(data));
    else {
      const names = result.map(station => station.name);
      assert.equal(names[0], hall === 'stokely' ? 'Traditions' : 'Entree');
      assert(names.indexOf('Bakery') > names.findIndex(name => name.trim() === 'Grill'));
      assert(names.findIndex(name => name.includes('Toppings')) > names.findIndex(name => name.trim() === 'Grill'));
      const ranks = JSON.parse(evaluate(`JSON.stringify(orderedStations('${hall}', testStations).map(s => {
        const rank = stationOrders['${hall}'].indexOf(stationName(s.name, '${hall}'));
        return rank < 0 ? stationOrders['${hall}'].length : rank;
      }))`));
      assert.deepEqual(ranks, [...ranks].sort((a,b) => a-b));
    }
  }
  assert(['Breakfast','Lunch','Dinner'].includes(elements.meal.value));
  console.log(`PASS ${file}: time boundaries, daylight saving, initial selection, station order, unknown stations, Southern Kitchen`);
}
