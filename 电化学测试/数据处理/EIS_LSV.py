import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'serif'  # 或者其他字体

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
from tkinter import Tk, filedialog

# 使用 Tkinter 选择主文件夹
def select_folder():
    root = Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="选择包含数据的主文件夹")
    return folder_path

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
    ax.grid(True)
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

                overpotential_10 = overpotential_10 if overpotential_10 is not None else 0.0
                overpotential_100 = overpotential_100 if overpotential_100 is not None else 0.0
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
    ax.grid(True)

    return overpotential_data

# 生成过电位柱状图
def plot_overpotential_bar_chart(ax, overpotential_data):
    # 对 overpotential_data 按 "Overpotential at 10 mA/cm² (V)" 从小到大排序
    overpotential_data = sorted(overpotential_data, key=lambda d: d["Overpotential at 10 mA/cm² (V)"] or float('inf'))

    # 提取排序后的数据
    labels = [d["Folder"] for d in overpotential_data]
    overpotential_10_values = [d["Overpotential at 10 mA/cm² (V)"] for d in overpotential_data]
    overpotential_100_values = [d["Overpotential at 100 mA/cm² (V)"] for d in overpotential_data]

    # 生成过电位柱状图
    x = range(len(labels))  # x轴的每个子文件夹的索引
    ax.bar([i + 0.2 for i in x], overpotential_10_values, width=0.2, label="Overpotential at 10 mA/cm² (V)")
    ax.bar([i + 0.4 for i in x], overpotential_100_values, width=0.2, label="Overpotential at 100 mA/cm² (V)")

    # 显示具体数值
    for i, v in enumerate(overpotential_10_values):
        if v is not None:
            ax.text(i + 0.2, v, f"{v:.3f}", rotation=90, ha='center', va='bottom')
    for i, v in enumerate(overpotential_100_values):
        if v is not None:
            ax.text(i + 0.4, v, f"{v:.3f}", rotation=90, ha='center', va='bottom')

    ax.set_xlabel("Folder")
    ax.set_ylabel("Over potential (V)")
    ax.set_title("Overpotential Comparison at 10 and 100 mA/cm²")
    ax.set_xticks([i + 0.3 for i in x])
    ax.set_xticklabels(labels, rotation=45, ha='right', va='top', fontsize=8)
    ax.legend()
    ax.grid(True)

# 主程序
if __name__ == "__main__":
    main_folder = select_folder()
    if main_folder:
        fig = plt.figure(figsize=(15, 12))  # 设置画布大小
        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1])  # 创建2行2列的网格布局

        # 创建子图
        ax1 = fig.add_subplot(gs[0, 0])  # 第一行第一个子图
        ax2 = fig.add_subplot(gs[0, 1])  # 第一行第二个子图
        ax3 = fig.add_subplot(gs[1, :])   # 第二行的柱状图，占据整行

        # 处理并合并 EIS 文件的 Nyquist 图
        process_eis_files(ax1, main_folder)

        # 处理 LSV 文件并获取过电位数据
        overpotential_data = process_lsv_files(ax2, main_folder)

        # 生成过电位柱状图
        plot_overpotential_bar_chart(ax3, overpotential_data)

        # 调整布局
        plt.tight_layout()

        # 保存合并图像
        save_path = os.path.join(main_folder, "Combined_Plots.png")
        plt.savefig(save_path, dpi=300)
        plt.show()  # 显示图像
        plt.close(fig)
        print(f"已保存合并图像：{save_path}")
    else:
        print("未选择文件夹。")
