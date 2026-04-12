import csv
import os
import sys
import argparse
from datetime import datetime, timedelta

import ee

# 石油備蓄基地タンク座標データ
TANK_DATA = [
    # 志布志国家備蓄基地 (shibushi)
    {"id": "shibushi_01", "lon": 131.02403931993155, "lat": 31.37539899202453},
    {"id": "shibushi_02", "lon": 131.02579884904532, "lat": 31.375545552003405},
    {"id": "shibushi_03", "lon": 131.02755837815909, "lat": 31.375673791797407},
    {"id": "shibushi_04", "lon": 131.02927499192862, "lat": 31.375783711481507},
    {"id": "shibushi_05", "lon": 131.0310345210424, "lat": 31.37594859076655},
    {"id": "shibushi_06", "lon": 131.02418952363638, "lat": 31.373896739059987},
    {"id": "shibushi_07", "lon": 131.02594905275015, "lat": 31.37404330138215},
    {"id": "shibushi_08", "lon": 131.0276871241918, "lat": 31.374153222973746},
    {"id": "shibushi_09", "lon": 131.02944665330557, "lat": 31.37431810512004},
    {"id": "shibushi_10", "lon": 131.03120618241934, "lat": 31.374446346589323},
    {"id": "shibushi_11", "lon": 131.03298716920523, "lat": 31.374592908054186},
    {"id": "shibushi_12", "lon": 131.02438264268545, "lat": 31.372412782672836},
    {"id": "shibushi_13", "lon": 131.0261207141271, "lat": 31.372559347309647},
    {"id": "shibushi_14", "lon": 131.02788024324087, "lat": 31.372687591179314},
    {"id": "shibushi_15", "lon": 131.02961831468252, "lat": 31.372815834873972},
    {"id": "shibushi_16", "lon": 131.0313778437963, "lat": 31.372925757901523},
    {"id": "shibushi_17", "lon": 131.03313737291006, "lat": 31.373090642201714},
    {"id": "shibushi_18", "lon": 131.02451138871817, "lat": 31.370873840184558},
    {"id": "shibushi_19", "lon": 131.02624946015982, "lat": 31.371075369801655},
    {"id": "shibushi_20", "lon": 131.0280089892736, "lat": 31.371166974030174},
    {"id": "shibushi_21", "lon": 131.02978997605948, "lat": 31.371331861416525},
    {"id": "shibushi_22", "lon": 131.03152804750113, "lat": 31.371405144606477},
    {"id": "shibushi_23", "lon": 131.03326611894278, "lat": 31.3715700315749},
    {"id": "shibushi_24", "lon": 131.023760370194, "lat": 31.369463120763676},
    {"id": "shibushi_25", "lon": 131.02551989930777, "lat": 31.369591368858845},
    {"id": "shibushi_26", "lon": 131.02730088609366, "lat": 31.369774580119746},
    {"id": "shibushi_27", "lon": 131.0290389575353, "lat": 31.36988450670486},
    {"id": "shibushi_28", "lon": 131.03079848664908, "lat": 31.370031075285006},
    {"id": "shibushi_29", "lon": 131.02395348924307, "lat": 31.367979094361466},
    {"id": "shibushi_30", "lon": 131.02571301835684, "lat": 31.368125665913265},
    {"id": "shibushi_31", "lon": 131.0274510897985, "lat": 31.36825391583357},
    {"id": "shibushi_32", "lon": 131.02921061891226, "lat": 31.368400486956755},
    {"id": "shibushi_33", "lon": 131.03097014802603, "lat": 31.368492093792675},
    {"id": "shibushi_34", "lon": 131.0241036929479, "lat": 31.366440079266983},
    {"id": "shibushi_35", "lon": 131.0258846797338, "lat": 31.36662329667114},
    {"id": "shibushi_36", "lon": 131.02760129350332, "lat": 31.36673322694221},
    {"id": "shibushi_37", "lon": 131.0293608226171, "lat": 31.366898122107735},
    {"id": "shibushi_38", "lon": 131.03114180940298, "lat": 31.367008052057344},
    {"id": "shibushi_39", "lon": 131.02427535432486, "lat": 31.36497432717624},
    {"id": "shibushi_40", "lon": 131.02603488343863, "lat": 31.365120903413885},
    {"id": "shibushi_41", "lon": 131.02775149720816, "lat": 31.36523083544215},
    {"id": "shibushi_42", "lon": 131.02953248399405, "lat": 31.365377411279812},
    {"id": "shibushi_43", "lon": 131.0312705554357, "lat": 31.36550566495024},
    # 他の基地のタンクはここに追加可能
    # 例: 苫小牧国家備蓄基地 (tomakomai)
    # {"id": "tomakomai_01", "lon": 141.123456, "lat": 42.654321},
    # {"id": "tomakomai_02", "lon": 141.123457, "lat": 42.654322},
    # 例: 仙台国家備蓄基地 (sendai)
    # {"id": "sendai_01", "lon": 140.987654, "lat": 38.123456},
    # {"id": "sendai_02", "lon": 140.987655, "lat": 38.123457},
    # 他の179個のタンクを同様に追加可能
]


def initialize_earth_engine(project_id=None):
    """Initialize the Earth Engine Python client."""
    try:
        if project_id:
            ee.Initialize(project=project_id)
        else:
            ee.Initialize()
    except Exception as e:
        print(f"Initialization failed: {e}")
        print("Please authenticate first: python -c 'import ee; ee.Authenticate()'")
        print("And provide a project ID: python gee.py --project YOUR_PROJECT_ID")
        raise


def create_tank_geometries():
    # Earth Engine Geometryオブジェクトのリストを返す
    return [ee.Geometry.Point([tank["lon"], tank["lat"]]).buffer(40) for tank in TANK_DATA]


def load_sentinel1_collection(all_geom, start_date=None, end_date=None):
    if start_date is None:
        start_date = '2016-01-01'
    if end_date is None:
        end_date = '2025-12-31'

    return (
        ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(all_geom)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        .filter(ee.Filter.eq('orbitProperties_pass', 'DESCENDING'))
        .select(['VV', 'VH'])
    )


def tank_time_series(tank_geom, s1_collection):
    def create_feature(img):
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=tank_geom,
            scale=20,
            maxPixels=1e6,
        )
        vv = stats.get('VV')
        vh = stats.get('VH')
        ratio = ee.Algorithms.If(
            vv,
            ee.Algorithms.If(vh, ee.Number(vv).subtract(ee.Number(vh)), None),
            None,
        )
        return ee.Feature(
            None,
            {
                'date': img.date().format('YYYY-MM-dd'),
                'ratio': ratio,
                'system:time_start': img.get('system:time_start'),
            },
        )

    return s1_collection.map(create_feature).filter(ee.Filter.notNull(['ratio']))


def detect_change_points(ts, k):
    ts = ts.sort('t')
    n = ts.size()
    items = ts.toList(n)

    def diff_feature(i):
        i = ee.Number(i)
        prev = ee.Feature(items.get(i.subtract(1)))
        curr = ee.Feature(items.get(i))
        diff = curr.getNumber('ratio').subtract(prev.getNumber('ratio')).abs()
        return curr.set('diff', diff)

    diff_items = ee.List.sequence(1, n.subtract(1)).map(diff_feature)
    diffs = ee.FeatureCollection(diff_items)
    mean = diffs.aggregate_mean('diff')
    std = diffs.aggregate_total_sd('diff')
    threshold = ee.Number(mean).add(ee.Number(std).multiply(ee.Number(k)))
    return diffs.filter(ee.Filter.gt('diff', threshold))


def get_tank_series_info(tank_geom, tank_id, s1_collection):
    ts = (
        tank_time_series(tank_geom, s1_collection)
        .map(lambda f: f.set('t', f.get('system:time_start')))
        .filter(ee.Filter.notNull(['t']))
        .sort('t')
    )

    # データが存在しない場合、空の結果を返す
    size = ts.size()
    empty_result = ee.Dictionary({
        'tank_id': tank_id,
        'dates': [],
        'ratios': [],
        'is_change_points': [],
        'times': [],
    })

    def process_data():
        # 変化点検出をサーバーサイドで実行
        cp = detect_change_points(ts, 3)

        # 変化点の日付リストを取得
        cp_dates = ee.List(cp.reduceColumns(ee.Reducer.toList(), ['date']).get('list'))

        # 時系列データをサーバーサイドで注釈付け
        annotated = ts.map(lambda f: f.set({
            'is_change_point': cp_dates.contains(f.get('date')),
        }))

        # 必要な統計量だけを取得
        dates = annotated.aggregate_array('date')
        ratios = annotated.aggregate_array('ratio')
        is_change_points = annotated.aggregate_array('is_change_point')
        times = annotated.aggregate_array('t')

        return ee.Dictionary({
            'tank_id': tank_id,
            'dates': dates,
            'ratios': ratios,
            'is_change_points': is_change_points,
            'times': times,
        })

    return ee.Algorithms.If(size.gt(0), process_data(), empty_result)


def get_last_date_from_csv(csv_path):
    """Get the latest date from existing CSV file."""
    if not os.path.exists(csv_path):
        return None

    latest_date = None
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date_str = row.get('date')
            if date_str:
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    if latest_date is None or date > latest_date:
                        latest_date = date
                except ValueError:
                    continue
    return latest_date


def write_csv(file_path, rows, append=False):
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    mode = 'a' if append else 'w'
    with open(file_path, mode=mode, newline='', encoding='utf-8') as csvfile:
        fieldnames = ['tank_id', 'date', 'ratio', 'is_change_point']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        writer.writerows(rows)


def parse_args():
    parser = argparse.ArgumentParser(description='Convert GEE JavaScript logic to Python Earth Engine API')
    parser.add_argument('--output-csv', default='tank_timeseries.csv', help='Output CSV path')
    parser.add_argument('--max-tanks', type=int, default=len(TANK_DATA), help='Number of tanks to process')
    parser.add_argument('--tanks', nargs='+', help='Specific tank IDs to process (e.g., shibushi_01 shibushi_02)')
    parser.add_argument('--verbose', action='store_true', help='Print progress and summary')
    parser.add_argument('--project', help='Google Cloud project ID for Earth Engine')
    parser.add_argument('--update', action='store_true', help='Update mode: append new data to existing CSV')
    return parser.parse_args()


def main():
    args = parse_args()
    initialize_earth_engine(args.project)

    # 差分更新の場合、最終日付を取得
    start_date = None
    append_mode = False
    if args.update and os.path.exists(args.output_csv):
        last_date = get_last_date_from_csv(args.output_csv)
        if last_date:
            # 最終日付の翌日から取得
            start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
            append_mode = True
            print(f'Update mode: appending data from {start_date}')
        else:
            print('Warning: Could not determine last date, falling back to full mode')

    # 処理するタンクを決定
    if args.tanks:
        # 指定されたタンクIDのみ処理
        tank_indices = []
        for tank_id in args.tanks:
            for idx, tank in enumerate(TANK_DATA):
                if tank["id"] == tank_id:
                    tank_indices.append(idx)
                    break
        if not tank_indices:
            print(f"Error: No valid tank IDs found in {args.tanks}")
            return
    else:
        # デフォルト: max_tanks個まで処理
        tank_indices = list(range(min(args.max_tanks, len(TANK_DATA))))

    tanks = create_tank_geometries()
    all_geom = ee.FeatureCollection([ee.Feature(t) for t in tanks]).geometry()
    s1_collection = load_sentinel1_collection(all_geom, start_date=start_date)

    # 各タンクの統計量をサーバーサイドで計算
    tank_stats = []
    for idx in tank_indices:
        tank_id = TANK_DATA[idx]["id"]
        tank_geom = tanks[idx]
        if args.verbose:
            print(f'Processing tank {tank_id}')
        stats = get_tank_series_info(tank_geom, tank_id, s1_collection)
        tank_stats.append(stats)

    # 全タンクの統計量を一度にクライアントに取得
    all_stats = [ee.Dictionary(stat).getInfo() for stat in tank_stats]

    all_rows = []
    for stats in all_stats:
        dates = stats['dates']
        ratios = stats['ratios']
        is_change_points = stats['is_change_points']

        for i in range(len(dates)):
            all_rows.append({
                'tank_id': stats['tank_id'],
                'date': dates[i],
                'ratio': ratios[i],
                'is_change_point': is_change_points[i],
            })

    if not all_rows:
        print('No new time series data found for the selected tanks.')
        return

    write_csv(args.output_csv, all_rows, append=append_mode)
    print(f'{"Appended" if append_mode else "Wrote"} {len(all_rows)} rows to {args.output_csv}')

    if args.verbose:
        for row in all_rows[: min(10, len(all_rows))]:
            print(row)


if __name__ == '__main__':
    main()
