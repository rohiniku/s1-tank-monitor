import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
from datetime import datetime

def load_tank_data(csv_path):
    """CSVファイルを読み込んでDataFrameを返す"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df['tank_id'] = df['tank_id'].astype(str)

    # CSV形式に応じて変化点カラムを処理
    if 'is_change_point' in df.columns:
        df['is_change_point'] = df['is_change_point'].astype(bool)
    elif 'ratio_cp' in df.columns:
        # ratio_cpがある場合、それを変化点として扱う
        df['is_change_point'] = df['ratio_cp'].notna()
    else:
        # 変化点カラムがない場合、全てFalse
        df['is_change_point'] = False

    df = df.sort_values(['tank_id', 'date'])
    return df

def plot_all_tanks(df, output_path=None):
    """全タンクの時系列推移をプロット"""
    tank_ids = df['tank_id'].unique()

    # サブプロットのレイアウトを決定（例: 6x8グリッドで48タンクまで対応）
    n_tanks = len(tank_ids)
    cols = 8
    rows = (n_tanks + cols - 1) // cols  # 切り上げ除算

    fig, axes = plt.subplots(rows, cols, figsize=(20, 3*rows), sharex=True)
    if rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle('All Tank Time Series (VV-VH Ratio)', fontsize=16, y=0.98)

    for i, tank_id in enumerate(tank_ids):
        row = i // cols
        col = i % cols

        tank_data = df[df['tank_id'] == tank_id].copy()
        tank_data = tank_data.sort_values('date')

        ax = axes[row, col]
        ax.plot(tank_data['date'], tank_data['ratio'], 'b-', linewidth=1, alpha=0.7)

        # 変化点を赤い点でマーク
        change_points = tank_data[tank_data['is_change_point'] == True]
        if not change_points.empty:
            ax.scatter(change_points['date'], change_points['ratio'],
                      color='red', s=20, zorder=5, label='Change Point')

        ax.set_title(f'{tank_id}', fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=6)

        # Y軸の範囲を統一（オプション）
        if not tank_data.empty:
            y_min, y_max = tank_data['ratio'].min(), tank_data['ratio'].max()
            margin = (y_max - y_min) * 0.1 if y_max != y_min else 1
            ax.set_ylim(y_min - margin, y_max + margin)

    # 余ったサブプロットを非表示
    for i in range(n_tanks, rows * cols):
        row = i // cols
        col = i % cols
        axes[row, col].set_visible(False)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved all tanks plot to {output_path}")
    else:
        plt.show()

def plot_shibushi_average(df, output_path=None):
    """志布志地区の平均時系列をプロット"""
    # shibushiのタンクのみ抽出
    shibushi_data = df[df['tank_id'].astype(str).str.startswith('shibushi_')].copy()

    if shibushi_data.empty:
        print("No shibushi tank data found")
        return

    # 日付ごとに平均を計算
    daily_avg = shibushi_data.groupby('date').agg({
        'ratio': 'mean',
        'is_change_point': lambda x: x.any()  # いずれかのタンクで変化点があればTrue
    }).reset_index()

    daily_avg = daily_avg.sort_values('date')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

    # 上のグラフ: 平均時系列
    ax1.plot(daily_avg['date'], daily_avg['ratio'], 'b-', linewidth=2, label='Average Ratio')

    # 変化点を赤い点でマーク
    change_points = daily_avg[daily_avg['is_change_point'] == True]
    if not change_points.empty:
        ax1.scatter(change_points['date'], change_points['ratio'],
                   color='red', s=50, zorder=5, label='Change Point Detected')

    ax1.set_title('Shibushi Tanks Average Time Series (VV-VH Ratio)', fontsize=14)
    ax1.set_ylabel('Average Ratio')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 下のグラフ: 個別タンクの推移（薄い線）
    tank_ids = shibushi_data['tank_id'].unique()
    colors = plt.cm.tab20.colors  # 20色のパレット

    for i, tank_id in enumerate(tank_ids):
        tank_data = shibushi_data[shibushi_data['tank_id'] == tank_id].sort_values('date')
        color = colors[i % len(colors)]
        ax2.plot(tank_data['date'], tank_data['ratio'],
                color=color, linewidth=1, alpha=0.6, label=tank_id)

    # 平均線を太く重ねる
    ax2.plot(daily_avg['date'], daily_avg['ratio'], 'k-', linewidth=3, label='Average')

    ax2.set_title('Individual Tank Time Series (Shibushi)', fontsize=14)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Ratio')
    ax2.grid(True, alpha=0.3)
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Saved shibushi average plot to {output_path}")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='Plot tank monitoring data')
    parser.add_argument('--csv', default='tank_timeseries.csv', help='Input CSV file path')
    parser.add_argument('--all-tanks-output', help='Output path for all tanks plot (PNG)')
    parser.add_argument('--shibushi-output', help='Output path for shibushi average plot (PNG)')
    parser.add_argument('--show-plots', action='store_true', help='Show plots interactively')

    args = parser.parse_args()

    try:
        df = load_tank_data(args.csv)
        print(f"Loaded {len(df)} records from {args.csv}")
        print(f"Tanks found: {df['tank_id'].nunique()}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")

        requested = False
        if args.all_tanks_output:
            print("Generating all tanks plot...")
            plot_all_tanks(df, args.all_tanks_output)
            requested = True

        if args.shibushi_output:
            print("Generating shibushi average plot...")
            plot_shibushi_average(df, args.shibushi_output)
            requested = True

        if not requested:
            print("No explicit output path specified, generating both default plots...")
            plot_all_tanks(df, 'all_tanks.png')
            plot_shibushi_average(df, 'shibushi_average.png')

        if args.show_plots:
            plt.show()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())