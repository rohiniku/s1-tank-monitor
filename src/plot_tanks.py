import argparse
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def load_tank_data(csv_path):
    """CSVファイルを読み込んでDataFrameを返す"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df['tank_id'] = df['tank_id'].astype(str)

    # RAWデータのみなので、is_change_pointはFalse
    df['is_change_point'] = False

    return df.sort_values(['tank_id', 'date'])


def remove_outliers_iqr(df, column, factor=1.5):
    """IQR法で外れ値を除去"""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - factor * IQR
    upper_bound = Q3 + factor * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]


def compute_indicators(df, indicators):
    """指定された指標を計算してDataFrameに追加"""
    df = df.copy()
    for indicator in indicators:
        if indicator == 'vv':
            df['vv'] = df['vv']
        elif indicator == 'vh':
            df['vh'] = df['vh']
        elif indicator == 'angle':
            df['angle'] = df['angle']
        elif indicator == 'vv_minus_vh':
            df['vv_minus_vh'] = df['vv'] - df['vh']
        elif indicator == 'vv_over_vh':
            df['vv_over_vh'] = df['vv'] / df['vh']
        elif indicator == 'vh_over_vv':
            df['vh_over_vv'] = df['vh'] / df['vv']
        elif indicator == 'vv_plus_vh':
            df['vv_plus_vh'] = df['vv'] + df['vh']
        elif indicator == 'polarization_ratio':
            df['polarization_ratio'] = (df['vv'] - df['vh']) / (df['vv'] + df['vh'])
        # 他の指標を追加可能
    return df


def load_region_csvs(data_dir, suffix='_tank_timeseries.csv'):
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    csv_files = sorted(
        [os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(suffix)]
    )
    if not csv_files:
        raise FileNotFoundError(f"No region CSV files found in {data_dir} matching '*{suffix}'")

    region_dfs = {}
    for csv_file in csv_files:
        region_name = os.path.basename(csv_file).split('_', 1)[0]
        df = load_tank_data(csv_file)
        df['region'] = region_name
        region_dfs[region_name] = df
    return region_dfs


def concat_region_dfs(region_dfs, exclude_regions=None):
    """地域のDataFrameを連結する"""
    if exclude_regions:
        dfs_to_concat = [df for region, df in region_dfs.items() if region not in exclude_regions]
    else:
        dfs_to_concat = list(region_dfs.values())
    if not dfs_to_concat:
        return pd.DataFrame()
    return pd.concat(dfs_to_concat, ignore_index=True)


def filter_by_date_range(df, start_date=None, end_date=None):
    """指定された期間でDataFrameをフィルタリングする"""
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    return df


def compute_daily_average(df, indicator):
    daily_avg = df.groupby('date').agg(
        **{indicator: (indicator, 'mean')},
        is_change_point=('is_change_point', 'any'),
    ).reset_index()
    return daily_avg.sort_values('date')


def compute_daily_averages(df, indicators):
    agg_dict = {indicator: (indicator, 'mean') for indicator in indicators}
    agg_dict['is_change_point'] = ('is_change_point', 'any')
    daily_avg = df.groupby('date').agg(**agg_dict).reset_index()
    return daily_avg.sort_values('date')


def plot_all_tanks(df, indicator, title, output_path=None, remove_outliers=False):
    tank_ids = sorted(df['tank_id'].unique())
    n_tanks = len(tank_ids)
    if n_tanks == 0:
        print('No tanks found for all-tanks plot')
        return

    cols = min(8, n_tanks)
    rows = (n_tanks + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(20, 3 * rows), sharex=True)
    if rows == 1:
        axes = axes.reshape(1, -1)
    elif cols == 1:
        axes = axes.reshape(-1, 1)

    fig.suptitle(title, fontsize=16, y=0.98)

    for i, tank_id in enumerate(tank_ids):
        row = i // cols
        col = i % cols
        ax = axes[row, col]

        tank_data = df[df['tank_id'] == tank_id].sort_values('date')
        if remove_outliers and len(tank_data) > 4:  # IQRには最低4点必要
            tank_data = remove_outliers_iqr(tank_data, indicator)
        ax.plot(tank_data['date'], tank_data[indicator], 'b-', linewidth=1, alpha=0.7)

        change_points = tank_data[tank_data['is_change_point']]
        if not change_points.empty:
            ax.scatter(change_points['date'], change_points[indicator], color='red', s=20, zorder=5)

        ax.set_title(tank_id, fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', which='major', labelsize=6)

        if not tank_data.empty:
            y_min, y_max = tank_data[indicator].min(), tank_data[indicator].max()
            margin = (y_max - y_min) * 0.1 if y_max != y_min else 0.5
            ax.set_ylim(y_min - margin, y_max + margin)

    for i in range(n_tanks, rows * cols):
        row = i // cols
        col = i % cols
        axes[row, col].set_visible(False)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved all tanks plot to {output_path}")
    else:
        plt.show()


def plot_region_average(df, region, indicator, output_path=None, remove_outliers=False):
    daily_avg = compute_daily_average(df, indicator)
    if daily_avg.empty:
        print(f"No data for region {region}")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    fig.suptitle(f'{region.capitalize()} Region Average and Individual Tanks ({indicator})', fontsize=16, y=0.98)

    if remove_outliers and len(daily_avg) > 4:
        daily_avg = remove_outliers_iqr(daily_avg, indicator)
    ax1.plot(daily_avg['date'], daily_avg[indicator], 'b-', linewidth=2, label=f'Average {indicator}')
    change_points = daily_avg[daily_avg['is_change_point']]
    if not change_points.empty:
        ax1.scatter(change_points['date'], change_points[indicator], color='red', s=50, zorder=5, label='Change Point Detected')

    ax1.set_title(f'{region.capitalize()} Average Time Series')
    ax1.set_ylabel(f'Average {indicator}')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    tank_ids = sorted(df['tank_id'].unique())
    colors = plt.cm.tab20.colors
    for i, tank_id in enumerate(tank_ids):
        tank_data = df[df['tank_id'] == tank_id].sort_values('date')
        if remove_outliers and len(tank_data) > 4:
            tank_data = remove_outliers_iqr(tank_data, indicator)
        ax2.plot(tank_data['date'], tank_data[indicator], color=colors[i % len(colors)], linewidth=1, alpha=0.6)

    ax2.plot(daily_avg['date'], daily_avg[indicator], 'k-', linewidth=3, label='Average')
    ax2.set_title(f'{region.capitalize()} Individual Tanks with Average')
    ax2.set_xlabel('Date')
    ax2.set_ylabel(indicator)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=8)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved region average plot to {output_path}")
    else:
        plt.show()


def plot_region_averages_comparison(region_dfs, indicator, output_path=None, remove_outliers=False):
    if not region_dfs:
        print('No region data available for comparison plot')
        return

    fig, ax = plt.subplots(figsize=(14, 8))
    colors = plt.cm.tab20.colors
    for i, (region, df) in enumerate(sorted(region_dfs.items())):
        daily_avg = compute_daily_average(df, indicator)
        if daily_avg.empty:
            continue
        if remove_outliers and len(daily_avg) > 4:
            daily_avg = remove_outliers_iqr(daily_avg, indicator)
        ax.plot(daily_avg['date'], daily_avg[indicator], label=region, color=colors[i % len(colors)], linewidth=2)

    ax.set_title(f'Region Average Comparison ({indicator}) - All Regions')
    ax.set_xlabel('Date')
    ax.set_ylabel(f'Average {indicator}')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', fontsize=8)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved region averages comparison plot to {output_path}")
    else:
        plt.show()


def plot_combined_average(df, indicator, title, output_path=None, remove_outliers=False):
    daily_avg = compute_daily_average(df, indicator)
    if daily_avg.empty:
        print('No data available for combined average plot')
        return

    tank_ids = sorted(df['tank_id'].unique())
    if not tank_ids:
        print('No tank IDs available for combined average plot')
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12), sharex=True)
    fig.suptitle(title, fontsize=16, y=0.98)

    if remove_outliers and len(daily_avg) > 4:
        daily_avg = remove_outliers_iqr(daily_avg, indicator)
    ax1.plot(daily_avg['date'], daily_avg[indicator], 'b-', linewidth=2, label=f'Average {indicator}')
    change_points = daily_avg[daily_avg['is_change_point']]
    if not change_points.empty:
        ax1.scatter(change_points['date'], change_points[indicator], color='red', s=50, zorder=5, label='Change Point')

    ax1.set_title('Average Time Series')
    ax1.set_ylabel(f'Average {indicator}')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    colors = plt.cm.tab20.colors
    for i, tank_id in enumerate(tank_ids):
        tank_data = df[df['tank_id'] == tank_id].sort_values('date')
        if remove_outliers and len(tank_data) > 4:
            tank_data = remove_outliers_iqr(tank_data, indicator)
        ax2.plot(tank_data['date'], tank_data[indicator], color=colors[i % len(colors)], linewidth=1, alpha=0.5)

    ax2.plot(daily_avg['date'], daily_avg[indicator], 'k-', linewidth=3, label='Average')
    ax2.set_title('Individual Tank Time Series with Average')
    ax2.set_xlabel('Date')
    ax2.set_ylabel(indicator)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper left', fontsize=8)

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved combined average plot to {output_path}")
    else:
        plt.show()


def plot_multi_indicators(df, indicators, title, output_path=None, remove_outliers=False):
    """複数の指標をプロット。2つなら左右Y軸、3つ以上なら複数行サブプロット"""
    df = df.sort_values('date')

    if len(indicators) == 2:
        fig, ax1 = plt.subplots(figsize=(15, 8))
        ax2 = ax1.twinx()

        color1, color2 = 'blue', 'red'
        data1 = df.copy()
        data2 = df.copy()
        if remove_outliers and len(df) > 4:
            data1 = remove_outliers_iqr(data1, indicators[0])
            data2 = remove_outliers_iqr(data2, indicators[1])
        ax1.plot(data1['date'], data1[indicators[0]], color=color1, linewidth=2, label=indicators[0])
        ax2.plot(data2['date'], data2[indicators[1]], color=color2, linewidth=2, label=indicators[1])

        ax1.set_xlabel('Date')
        ax1.set_ylabel(indicators[0], color=color1)
        ax2.set_ylabel(indicators[1], color=color2)

        ax1.tick_params(axis='y', labelcolor=color1)
        ax2.tick_params(axis='y', labelcolor=color2)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

        plt.title(title)

    elif len(indicators) > 2:
        n_indicators = len(indicators)
        fig, axes = plt.subplots(n_indicators, 1, figsize=(15, 4 * n_indicators), sharex=True)
        if n_indicators == 1:
            axes = [axes]

        colors = plt.cm.tab10.colors
        for i, indicator in enumerate(indicators):
            ax = axes[i]
            data = df.copy()
            if remove_outliers and len(df) > 4:
                data = remove_outliers_iqr(data, indicator)
            ax.plot(data['date'], data[indicator], color=colors[i % len(colors)], linewidth=2, label=indicator)
            ax.set_ylabel(indicator)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left')

        axes[-1].set_xlabel('Date')
        fig.suptitle(title, y=0.98)

    else:
        print("At least 2 indicators needed for multi-indicator plot")
        return

    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"Saved multi-indicators plot to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description='Plot tank monitoring data from region CSVs or a single CSV')
    parser.add_argument('--csv', help='Input single CSV file path')
    parser.add_argument('--data-dir', default='data', help='Directory containing region CSV files')
    parser.add_argument('--output-dir', default='plots', help='Directory to write PNG files')
    parser.add_argument('--region', help='Specific region to process (e.g. shibushi, tomakomai, hokkaido)')
    parser.add_argument('--indicators', nargs='+', default=['vv_minus_vh'], 
                        help='Indicators to plot (e.g., vv vh angle vv_minus_vh vv_over_vh)')
    parser.add_argument('--start-date', help='Plot start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='Plot end date (YYYY-MM-DD)')
    parser.add_argument('--remove-outliers', action='store_true', help='Remove outliers using IQR method before plotting')
    parser.add_argument('--plot-region-all-tanks', action='store_true', help='Generate per-region all tanks plots')
    parser.add_argument('--plot-region-average', action='store_true', help='Generate per-region average plots')
    parser.add_argument('--plot-region-averages-comparison', action='store_true', help='Generate one comparison plot with all region averages')
    parser.add_argument('--combined-average-output', help='Output PNG for combined average across all regions')
    parser.add_argument('--non-hokkaido-average-output', help='Output PNG for combined average excluding hokkaido')
    parser.add_argument('--multi-indicators-output', help='Output PNG for multi-indicators plot')
    parser.add_argument('--show-plots', action='store_true', help='Show plots interactively')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    region_dfs = {}
    single_df = None

    try:
        if args.csv:
            single_df = load_tank_data(args.csv)
            single_df = compute_indicators(single_df, args.indicators)
            if args.region:
                single_df = single_df[single_df['tank_id'].str.startswith(f'{args.region}_')]
                if single_df.empty:
                    raise ValueError(f"No data found for region {args.region} in {args.csv}")
        else:
            region_dfs = load_region_csvs(args.data_dir)
            for region, df in region_dfs.items():
                region_dfs[region] = compute_indicators(df, args.indicators)
            if args.region:
                if args.region not in region_dfs:
                    raise ValueError(f"Region {args.region} not found in {args.data_dir}")
                region_dfs = {args.region: region_dfs[args.region]}

        if args.start_date or args.end_date:
            if args.csv:
                single_df = filter_by_date_range(single_df, args.start_date, args.end_date)
                if single_df.empty:
                    raise ValueError(f"No data found in {args.csv} for the selected date range")
            else:
                region_dfs = {
                    region: filter_by_date_range(df, args.start_date, args.end_date)
                    for region, df in region_dfs.items()
                }
                region_dfs = {region: df for region, df in region_dfs.items() if not df.empty}
                if not region_dfs:
                    raise ValueError(f"No data found in {args.data_dir} for the selected date range")

        if args.csv:
            print(f"Loaded {len(single_df)} records from {args.csv}")
            print(f"Tanks found: {single_df['tank_id'].nunique()}")
            print(f"Date range: {single_df['date'].min()} to {single_df['date'].max()}")

            if args.plot_region_all_tanks or args.plot_region_average or args.combined_average_output or args.non_hokkaido_average_output:
                if args.plot_region_all_tanks:
                    output_path = os.path.join(args.output_dir, 'all_tanks.png')
                    plot_all_tanks(single_df, args.indicators[0], 'All Tanks Time Series', output_path, args.remove_outliers)
                if args.plot_region_average:
                    region_name = args.region or 'all'
                    output_path = os.path.join(args.output_dir, f'{region_name}_average.png')
                    plot_region_average(single_df, region_name, args.indicators[0], output_path, args.remove_outliers)
                if args.combined_average_output:
                    plot_combined_average(single_df, args.indicators[0], 'Combined Average Time Series', args.combined_average_output, args.remove_outliers)
                if args.non_hokkaido_average_output:
                    print('Warning: non-hokkaido average is not available when using a single CSV input')
            else:
                plot_all_tanks(single_df, args.indicators[0], 'All Tanks Time Series', os.path.join(args.output_dir, 'all_tanks.png'), args.remove_outliers)
                region_name = args.region or 'all'
                plot_region_average(single_df, region_name, args.indicators[0], os.path.join(args.output_dir, f'{region_name}_average.png'), args.remove_outliers)
        else:
            for region, df in region_dfs.items():
                print(f"Loaded {len(df)} records for region {region}")

            if not any([
                args.plot_region_all_tanks,
                args.plot_region_average,
                args.plot_region_averages_comparison,
                args.combined_average_output,
                args.non_hokkaido_average_output,
                args.multi_indicators_output,
            ]):
                args.plot_region_all_tanks = True
                args.plot_region_average = True
                args.plot_region_averages_comparison = True
                if not args.combined_average_output:
                    args.combined_average_output = os.path.join(args.output_dir, 'all_regions_combined_average.png')
                if not args.non_hokkaido_average_output:
                    args.non_hokkaido_average_output = os.path.join(args.output_dir, 'all_regions_non_hokkaido_average.png')
                if not args.multi_indicators_output and len(args.indicators) > 1:
                    args.multi_indicators_output = os.path.join(args.output_dir, 'multi_indicators.png')

            if args.plot_region_all_tanks:
                for region, df in region_dfs.items():
                    output_path = os.path.join(args.output_dir, f'{region}_all_tanks.png')
                    plot_all_tanks(df, args.indicators[0], f'{region.capitalize()} Region All Tanks', output_path, args.remove_outliers)

            if args.plot_region_average:
                for region, df in region_dfs.items():
                    output_path = os.path.join(args.output_dir, f'{region}_average.png')
                    plot_region_average(df, region, args.indicators[0], output_path, args.remove_outliers)

            if args.plot_region_averages_comparison:
                output_path = os.path.join(args.output_dir, 'region_averages_comparison.png')
                plot_region_averages_comparison(region_dfs, args.indicators[0], output_path, args.remove_outliers)

            if args.combined_average_output:
                all_df = concat_region_dfs(region_dfs)
                plot_combined_average(all_df, args.indicators[0], 'All Regions Combined Average', args.combined_average_output, args.remove_outliers)

            if args.non_hokkaido_average_output:
                no_hokkaido = concat_region_dfs(region_dfs, exclude_regions=['hokkaido'])
                plot_combined_average(no_hokkaido, args.indicators[0], 'All Regions Combined Average (Excluding Hokkaido)', args.non_hokkaido_average_output, args.remove_outliers)

            if args.multi_indicators_output:
                # 複数指標プロットは全データを使って日次平均を作成する
                all_df = concat_region_dfs(region_dfs)
                all_df = compute_daily_averages(all_df, args.indicators)
                plot_multi_indicators(all_df, args.indicators, 'Multi-Indicators Time Series', args.multi_indicators_output, args.remove_outliers)

        if args.show_plots:
            plt.show()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())