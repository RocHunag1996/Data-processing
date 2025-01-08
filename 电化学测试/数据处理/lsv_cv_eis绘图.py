import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tkinter import Tk, filedialog

# 使用 Tkinter 选择文件夹
def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="选择文件夹")
    return folder_path

# 从文件名中提取扫描速率（单位为mV/s）
def extract_scan_rate(file_name):
    try:
        scan_rate = int(file_name.split('CV-')[1].split('.')[0])
    except (IndexError, ValueError):
        scan_rate = None
    return scan_rate

# 读取 CV 文件数据
def read_cv_data(file_path):
    with open(file_path, 'r') as file:
        for i, line in enumerate(file):
            if line.startswith('Potential') or line.startswith('#'):
                skip_rows = i + 1
                break
        else:
            skip_rows = 0
    data = pd.read_csv(file_path, skiprows=skip_rows, header=None, names=['Potential', 'Current'])
    return data.dropna()

b_values = []

# 获取溶液电阻，即 EIS 文件中 data["Z'"] 的第一个数据
def get_resistance_value(eis_file_path):
    try:
        eis_data = pd.read_csv(eis_file_path, skiprows=21, header=None, names=['Freq', "Z'", "Z''", 'Z', 'Phase'])
        resistance = eis_data["Z'"].iloc[0]  # 取出第一个 Z' 数据
        return resistance
    except (FileNotFoundError, IndexError, ValueError) as e:
        print(f"读取 EIS 文件 {eis_file_path} 失败: {e}")
        return None

# 计算过电位
def calculate_overpotential(voltage, current_density):
    calibrated_voltage = voltage + 0.652 - 1.23
    return calibrated_voltage

# 处理每个子文件夹的 EIS 文件，并在同一张图上绘制多个 Nyquist 图
def process_eis_files(ax, main_folder):
    color_cycle = plt.cm.tab20.colors  # 使用颜色循环
    color_index = 0  # 颜色索引

    max_z_prime = 0
    max_z_double_prime = 0

    # 第一遍，确定所有文件的最大 Z' 和 Z'' 值
    for subdir, _, files in os.walk(main_folder):
        for file in files:
            if file.lower() == 'eis.txt':
                file_path = os.path.join(subdir, file)
                
                # 读取 EIS.txt 数据
                data = pd.read_csv(file_path, skiprows=21, header=None, names=['Freq', "Z'", "Z''", 'Z', 'Phase'])
                
                # 提取第二列和第三列数据
                x = data["Z'"]
                y = data["Z''"]

                # 更新最大值
                max_z_prime = max(max_z_prime, max(x))
                max_z_double_prime = max(max_z_double_prime, abs(min(y)))

    # 设置轴范围
    max_abs = max(max_z_prime, max_z_double_prime)
    ax.set_xlim(0, max_abs)  # Z' axis from 0 to max_abs
    ax.set_ylim(-max_abs, 0)  # Z'' axis from -max_abs to 0

    # 第二遍，绘制图形
    for subdir, _, files in os.walk(main_folder):
        subfolder_name = os.path.basename(subdir)
        
        for file in files:
            if file.lower() == 'eis.txt':
                file_path = os.path.join(subdir, file)
                
                # 读取 EIS.txt 数据
                data = pd.read_csv(file_path, skiprows=21, header=None, names=['Freq', "Z'", "Z''", 'Z', 'Phase'])
                
                # 提取第二列和第三列数据
                x = data["Z'"]
                y = data["Z''"]

                # Plot configuration for each subfolder with different color
                ax.plot(x, y, marker='o', label=subfolder_name, color=color_cycle[color_index % len(color_cycle)])
                color_index += 1

    # Invert y-axis to keep Z'' negative values downward
    ax.invert_yaxis()

    # Set labels and grid
    ax.set_xlabel("Z' (Ω·cm²)")
    ax.set_ylabel("Z'' (Ω·cm²)")
    #ax.grid(True)
    ax.legend(loc='best')  # 显示图例

# 处理每个子文件夹的 LSV 文件并绘制对比图
def process_lsv_files(ax, main_folder):
    overpotential_data = []

    for subdir, _, files in os.walk(main_folder):
        subfolder_name = os.path.basename(subdir)
        eis_file_path = os.path.join(subdir, 'EIS.txt')
        resistance = get_resistance_value(eis_file_path)  # 获取电阻值

        # 跳过没有电阻值的子文件夹
        if resistance is None:
            print(f"子文件夹 {subfolder_name} 没有有效的电阻值，跳过该文件夹。")
            continue

        for file in files:
            if file.lower() == 'lsv.txt':
                file_path = os.path.join(subdir, file)

                # 读取 lsv.txt 数据，从第 20 行开始，跳过文件头部信息
                try:
                    data = pd.read_csv(file_path, skiprows=20, header=None, names=['Potential', 'Current'])
                    if data.empty:
                        print(f"文件 {file_path} 没有数据")
                        continue
                except ValueError as e:
                    print(f"文件 {file_path} 读取失败: {e}")
                    continue

                # 确保 'Potential' 和 'Current' 列为数值类型
                data["Potential"] = pd.to_numeric(data["Potential"], errors='coerce')
                data["Current"] = pd.to_numeric(data["Current"], errors='coerce')
                data = data.dropna()  # 删除无法转换为数值的行

                # 确保 resistance 为数值
                if resistance is not None:
                    resistance = float(resistance)

                # 校准电位和计算电流密度
                x = data["Potential"] - data["Current"] * resistance
                current_density = data["Current"] * 1000 / 0.196  # 计算电流密度 (mA/cm^2)

                # 绘制每个文件的 LSV 曲线在同一个图中
                ax.plot(x, current_density, label=subfolder_name)

                # 计算 10 和 100 mA/cm² 时的过电位
                overpotential_10 = calculate_overpotential(x[current_density >= 10].iloc[0], 10) if (current_density >= 10).any() else None
                overpotential_100 = calculate_overpotential(x[current_density >= 100].iloc[0], 100) if (current_density >= 100).any() else None

                # 收集每个子文件夹的溶液电阻和过电位数据
                overpotential_data.append({
                    "Folder": subfolder_name,
                    "Resistance (Ω)": resistance,
                    "Overpotential at 10 mA/cm² (V)": overpotential_10,
                    "Overpotential at 100 mA/cm² (V)": overpotential_100
                })

    # 绘制 LSV 对比图
    ax.set_xlabel("Calibrated Potential (V)")
    ax.set_ylabel("Current Density (mA/cm²)")
    ax.set_title("LSV Curves Comparison")
    ax.legend()
    #ax.grid(True)

    resistance = resistance if resistance is not None else 0.0
    overpotential_10 = overpotential_10 if overpotential_10 is not None else 0.0
    overpotential_100 = overpotential_100 if overpotential_100 is not None else 0.0

    info_text = f"Solution Resistance: {resistance:.3f} Ω\n" \
                f"Overpotential at 10 mA/cm²: {overpotential_10:.3f} V\n" \
                f"Overpotential at 100 mA/cm²: {overpotential_100:.3f} V"

    ax.text(0.05, 0.95, info_text, transform=ax.transAxes, fontsize=9, verticalalignment='top')

    return overpotential_data

def plot_cv_data_and_save(file_paths, output_folder, area_cm2=0.196):
    # 创建 1x2 的组图
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))  # 设置宽高比

    max_min_values = []
    scan_rates = []
    max_current_densities = []
    min_current_densities = []
    

    # 绘制第一个图：电位-电流曲线
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        scan_rate = extract_scan_rate(file_name)

        data = read_cv_data(file_path)
        if not data.empty and 'Potential' in data.columns and 'Current' in data.columns:
            data['Current Density'] = (data['Current'] * 1000) / area_cm2

            max_current = data['Current Density'].max()
            min_current = data['Current Density'].min()
            max_min_values.append({
                'File': file_name,
                'Max Current Density (mA/cm²)': max_current,
                'Min Current Density (mA/cm²)': min_current
            })

            axes[0, 0].plot(data['Potential'], data['Current Density'], label=file_name.split('.')[0])

            if scan_rate is not None:
                scan_rates.append(scan_rate)
                max_current_densities.append(max_current)
                min_current_densities.append(min_current)
        else:
            print(f"{file_name} 数据有问题，无法处理。")

    # 设置第一个图的样式
    axes[0, 0].set_xlabel('Potential (V)')
    axes[0, 0].set_ylabel('Current Density (mA/cm²)')
    axes[0, 0].set_title('Cyclic Voltammetry Data')
    axes[0, 0].legend()
    #axes[0].grid(True)

   # 绘制第二个图：扫描速率与电流密度关系
    if scan_rates and max_current_densities:
        # 绘制点图
        axes[0, 1].scatter(scan_rates, max_current_densities, marker='o', color='blue', label='Max Current Density')
        axes[0, 1].scatter(scan_rates, min_current_densities, marker='o', color='orange', label='Min Current Density')

        # 初始化 b 值变量
        b_value_max = None
        b_value_min = None

        # 线性拟合最大值
        if len(scan_rates) > 1:
            slope_max, intercept_max = np.polyfit(scan_rates, max_current_densities, 1)
            axes[0, 1].plot(scan_rates, slope_max * np.array(scan_rates) + intercept_max, color='blue', linestyle='--', label='Max Fit')
            b_value_max = slope_max * 1000  # 转换单位为 mF/cm²

        # 线性拟合最小值
        if len(scan_rates) > 1:
            slope_min, intercept_min = np.polyfit(scan_rates, min_current_densities, 1)
            axes[0, 1].plot(scan_rates, slope_min * np.array(scan_rates) + intercept_min, color='orange', linestyle='--', label='Min Fit')
            b_value_min = abs(slope_min) * 1000  # 转换单位为 mF/cm²

        # 在第二个图中添加 b 值
        if b_value_max is not None:
            axes[0, 1].text(
                0.05, 0.95, 
                f"b (Max): {b_value_max:.2f} mF/cm²",
                transform=axes[0, 1].transAxes, 
                fontsize=12, 
                color='blue', 
                verticalalignment='top'
            )
        if b_value_min is not None:
            axes[0, 1].text(
                0.05, 0.90, 
                f"b (Min): {b_value_min:.2f} mF/cm²",
                transform=axes[0, 1].transAxes, 
                fontsize=12, 
                color='orange', 
                verticalalignment='top'
            )

        # 设置第二个图的样式
        axes[0, 1].set_xlabel('Scan Rate (mV/s)')
        axes[0, 1].set_ylabel('Current Density (mA/cm²)')
        axes[0, 1].set_title('Scan Rate vs. Current Density')
       # axes[1].grid(True)
        axes[0, 1].legend()

        # 计算 b 值
        b_value_max = slope_max * 1000 if len(scan_rates) > 1 else None
        b_value_min = abs(slope_min) * 1000 if len(scan_rates) > 1 else None

        # 在这里替换 file_path 为文件夹名称
        folder_name = os.path.basename(os.path.dirname(file_path))
        b_values.append((folder_name, b_value_max, b_value_min))

        # 创建子图
    ax1 = fig.add_subplot(axes[1, 0])  # 第一行第一个子图
    ax2 = fig.add_subplot(axes[1, 1])  # 第一行第二个子图

    # 处理并合并 EIS 文件的 Nyquist 图
    process_eis_files(ax1, subdir)

    # 处理 LSV 文件并获取过电位数据
    overpotential_data = process_lsv_files(ax2, subdir)

    # 保存组图
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    combined_plot_path = os.path.join(output_folder, 'combined_cv_and_scan_rate_plot.png')
    plt.tight_layout()
    plt.savefig(combined_plot_path)
    print(f"组图已保存到：{combined_plot_path}")
    plt.show()

    # 保存最大最小值为 CSV
    max_min_df = pd.DataFrame(max_min_values)
    csv_output = os.path.join(output_folder, 'max_min_values.csv')
    max_min_df.to_csv(csv_output, index=False)
    print(f"最大最小值已保存到：{csv_output}")

    
# 主程序
if __name__ == "__main__":
    root_folder = select_folder()
    
    if root_folder:
        # 遍历选定文件夹及其子文件夹
        for subdir, _, files in os.walk(root_folder):
            cv_files = [os.path.join(subdir, f) for f in files if f.startswith('CV-') and f.endswith('.txt')]
            if cv_files:
                plot_cv_data_and_save(cv_files, subdir)
    else:
        print("未选择文件夹。")

        # 排序 b 值并绘制柱状图
    if b_values:
        b_df = pd.DataFrame(b_values, columns=['File', 'b_max', 'b_min']).dropna()
        b_df = b_df.sort_values(by=['b_max', 'b_min'], ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))
        indices = np.arange(len(b_df))
        ax.bar(indices - 0.2, b_df['b_max'], width=0.4, label='b (Max)', color='blue')
        ax.bar(indices + 0.2, b_df['b_min'], width=0.4, label='b (Min)', color='orange')

        ax.set_xlabel('Sample')
        ax.set_ylabel('b Value (mF/cm²)')
        ax.set_title('Comparison of b(max) and b(min) Values')
        ax.set_xticks(indices)
        ax.set_xticklabels(b_df['File'], rotation=45, ha='right')
        ax.legend()
        #ax.grid(True)

        sorted_plot_path = os.path.join(subdir, 'sorted_b_values_plot.png')
        plt.tight_layout()
        plt.savefig(sorted_plot_path)
        print(f"排序后的 b 值柱状图已保存到：{sorted_plot_path}")
        plt.show()
        
sorted_plot_path = os.path.join(subdir, 'sorted_b_values_plot.png')
plt.tight_layout()
plt.savefig(sorted_plot_path)
print(f"排序后的 b 值柱状图已保存到：{sorted_plot_path}")
plt.show()
