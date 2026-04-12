// ===============================
// 0. 志布志国家備蓄基地 43基
// ===============================
var tanks = [
  ee.Geometry.Point([131.02403931993155,31.37539899202453]).buffer(40),
  ee.Geometry.Point([131.02579884904532,31.375545552003405]).buffer(40),
  ee.Geometry.Point([131.02755837815909,31.375673791797407]).buffer(40),
  ee.Geometry.Point([131.02927499192862,31.375783711481507]).buffer(40),
  ee.Geometry.Point([131.0310345210424,31.37594859076655]).buffer(40),
  ee.Geometry.Point([131.02418952363638,31.373896739059987]).buffer(40),
  ee.Geometry.Point([131.02594905275015,31.37404330138215]).buffer(40),
  ee.Geometry.Point([131.0276871241918,31.374153222973746]).buffer(40),
  ee.Geometry.Point([131.02944665330557,31.37431810512004]).buffer(40),
  ee.Geometry.Point([131.03120618241934,31.374446346589323]).buffer(40),
  ee.Geometry.Point([131.03298716920523,31.374592908054186]).buffer(40),
  ee.Geometry.Point([131.02438264268545,31.372412782672836]).buffer(40),
  ee.Geometry.Point([131.0261207141271,31.372559347309647]).buffer(40),
  ee.Geometry.Point([131.02788024324087,31.372687591179314]).buffer(40),
  ee.Geometry.Point([131.02961831468252,31.372815834873972]).buffer(40),
  ee.Geometry.Point([131.0313778437963,31.372925757901523]).buffer(40),
  ee.Geometry.Point([131.03313737291006,31.373090642201714]).buffer(40),
  ee.Geometry.Point([131.02451138871817,31.370873840184558]).buffer(40),
  ee.Geometry.Point([131.02624946015982,31.371075369801655]).buffer(40),
  ee.Geometry.Point([131.0280089892736,31.371166974030174]).buffer(40),
  ee.Geometry.Point([131.02978997605948,31.371331861416525]).buffer(40),
  ee.Geometry.Point([131.03152804750113,31.371405144606477]).buffer(40),
  ee.Geometry.Point([131.03326611894278,31.3715700315749]).buffer(40),
  ee.Geometry.Point([131.023760370194,31.369463120763676]).buffer(40),
  ee.Geometry.Point([131.02551989930777,31.369591368858845]).buffer(40),
  ee.Geometry.Point([131.02730088609366,31.369774580119746]).buffer(40),
  ee.Geometry.Point([131.0290389575353,31.36988450670486]).buffer(40),
  ee.Geometry.Point([131.03079848664908,31.370031075285006]).buffer(40),
  ee.Geometry.Point([131.02395348924307,31.367979094361466]).buffer(40),
  ee.Geometry.Point([131.02571301835684,31.368125665913265]).buffer(40),
  ee.Geometry.Point([131.0274510897985,31.36825391583357]).buffer(40),
  ee.Geometry.Point([131.02921061891226,31.368400486956755]).buffer(40),
  ee.Geometry.Point([131.03097014802603,31.368492093792675]).buffer(40),
  ee.Geometry.Point([131.0241036929479,31.366440079266983]).buffer(40),
  ee.Geometry.Point([131.0258846797338,31.36662329667114]).buffer(40),
  ee.Geometry.Point([131.02760129350332,31.36673322694221]).buffer(40),
  ee.Geometry.Point([131.0293608226171,31.366898122107735]).buffer(40),
  ee.Geometry.Point([131.03114180940298,31.367008052057344]).buffer(40),
  ee.Geometry.Point([131.02427535432486,31.36497432717624]).buffer(40),
  ee.Geometry.Point([131.02603488343863,31.365120903413885]).buffer(40),
  ee.Geometry.Point([131.02775149720816,31.36523083544215]).buffer(40),
  ee.Geometry.Point([131.02953248399405,31.365377411279812]).buffer(40),
  ee.Geometry.Point([131.0312705554357,31.36550566495024]).buffer(40)
];

// 全タンク領域
var allGeom = ee.FeatureCollection(tanks.map(function(g){ return ee.Feature(g); })).geometry();

// ===============================
// 1. Sentinel-1 GRD 読み込み
// ===============================
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(allGeom)
  .filterDate('2016-01-01', '2025-12-31')
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
  .select(['VV', 'VH']);

// ===============================
// 2. タンクごとの時系列（VV-VH）
// ===============================
function tankTimeSeries(tankGeom) {
  return s1.map(function(img){
    var stats = img.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: tankGeom,
      scale: 20,
      maxPixels: 1e6
    });

    var vv = stats.get('VV');
    var vh = stats.get('VH');

    var ratio = ee.Algorithms.If(
      vv,
      ee.Algorithms.If(
        vh,
        ee.Number(vv).subtract(ee.Number(vh)),
        null
      ),
      null
    );

    return ee.Feature(null, {
      'date': img.date().format('YYYY-MM-dd'),
      'ratio': ratio,
      'system:time_start': img.get('system:time_start')   // ★ これが絶対に必要
    });
  }).filter(ee.Filter.notNull(['ratio']));
}

// ===============================
// 3. 変化点検出
// ===============================
// ts: ratio と t を持つ、null なし・ソート済みの FeatureCollection
// k: 何σをしきい値にするか（例: 2 or 3）
function detectChangePoints(ts, k) {

  // 念のためソート（ts1 がすでにソート済みでも安全のため）
  ts = ts.sort('t');

  var n = ts.size();
  var list = ts.toList(n);

  // 1. diff を計算
  var diffList = ee.List.sequence(1, n.subtract(1)).map(function(i) {
    i = ee.Number(i);
    var prev = ee.Feature(list.get(i.subtract(1)));
    var curr = ee.Feature(list.get(i));

    var prevRatio = prev.getNumber('ratio');
    var currRatio = curr.getNumber('ratio');

    var diff = currRatio.subtract(prevRatio).abs();

    return curr.set('diff', diff);
  });

  var diffs = ee.FeatureCollection(diffList);

  // 2. 統計量
  var mean = diffs.aggregate_mean('diff');
  var std  = diffs.aggregate_total_sd('diff');

  // ★ k が undefined だと multiply が壊れるので必ず Number(k) にする
  var th = ee.Number(mean).add(ee.Number(std).multiply(ee.Number(k)));

  // 3. 閾値を超えたものだけ返す
  return diffs.filter(ee.Filter.gt('diff', th));
}

// // ===============================
// // 4. Tank 0 のグラフ
// // ===============================
// // Tank 0 の時系列
// var ts1 = tankTimeSeries(tanks[0])
//   .map(function(f){
//     return f.set('t', f.get('system:time_start'));  // ★ 時系列キーを追加
//   })
//   .filter(ee.Filter.notNull(['ratio']))
//   .filter(ee.Filter.notNull(['t']))
//   .sort('t');  // ★ 文字列ではなく time_start でソート

// print('Cleaned TS size:', ts1.size());

// ts1.size().evaluate(function(n){
//   if (n < 2) {
//     print('Tank 0: 有効データが不足');
//   } else {
//     var cp1 = detectChangePoints(ts1, 3);  // ★ k=3σ
//     print('Detected Change Points (Tank 0)', cp1);

//     var chart = ui.Chart.feature.byFeature(ts1, 'date', 'ratio')
//       .setChartType('LineChart')
//       .setOptions({
//         title: 'Tank 0 VV-VH Time Series',
//         hAxis: {title: 'Date'},
//         vAxis: {title: 'VV-VH (dB)'},
//         pointSize: 3,
//         lineWidth: 1
//       });

//     print(chart);
//   }
// });

// スパークラインを作る関数
function makeSparkline(ts, cp, tankId) {

  // cp の t を ee.List として取得
  var cpSet = ee.List(cp.reduceColumns(ee.Reducer.toList(), ['t']).get('list'));

  var merged = ts.map(function(f){
    var t = f.get('t');
    var isCP = cpSet.contains(t);  // ★ これで OK
    return f.set({
      ratioLine: f.get('ratio'),
      ratioCP: ee.Algorithms.If(isCP, f.get('ratio'), null)
    });
  });

  var chart = ui.Chart.feature.byFeature(merged, 't', ['ratioLine', 'ratioCP'])
    .setChartType('LineChart')
    .setOptions({
      title: 'Tank ' + tankId,
      legend: 'none',
      hAxis: { ticks: [], textPosition: 'none' },
      vAxis: { ticks: [], textPosition: 'none' },
      lineWidth: 1,
      pointSize: 0,
      series: {
        0: { color: 'blue', lineWidth: 1 },
        1: { color: 'red', pointSize: 6, lineWidth: 0 }
      },
      chartArea: {left: 20, right: 5, top: 5, bottom: 5},
      height: 40,
      width: 250
    });

  return chart;
}

// 43 基分のスパークラインを作って並べる
var panel = ui.Panel({
  layout: ui.Panel.Layout.flow('vertical'),
  style: {width: '300px'}
});

ee.List.sequence(0, 42).getInfo().forEach(function(i){
  var ts = tankTimeSeries(tanks[i])
    .map(function(f){ return f.set('t', f.get('system:time_start')); })
    .filter(ee.Filter.notNull(['ratio']))
    .filter(ee.Filter.notNull(['t']))
    .sort('t');

  var cp = detectChangePoints(ts, 3);

  panel.add(makeSparkline(ts, cp, i));
});

print(panel);



// ===============================
// 5. 地図表示
// ===============================
Map.centerObject(tanks[0], 15);
tanks.forEach(function(t, i){
  Map.addLayer(t, {color: 'red'}, 'Tank ' + i);
});
