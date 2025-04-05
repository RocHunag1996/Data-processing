import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from scipy.signal import argrelextrema
import matplotlib.cm as cm
import matplotlib


# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def main():
    # 创建一个隐藏的根窗口
    root = tk.Tk()
    root.withdraw()
    
    # 弹出文件夹选择对话框
    folder_path = filedialog.askdirectory(title="请选择包含数据文件的文件夹")
    if not folder_path:
        print("未选择文件夹，程序退出")
        return
    
    # 创建输出子文件夹
    output_dir = os.path.join(folder_path, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 存储所有文件的电压值和极值点
    all_voltage_values = []
    all_max_points = []
    all_min_points = []
    
    # 处理文件夹中的所有.txt文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            # 从文件名中提取电压值
            voltage_match = re.search(r'(\d+\.\d+)', filename)
            if voltage_match:
                voltage = float(voltage_match.group(1))
                print(f"处理文件: {filename}, 电压值: {voltage}V")
                
                # 读取数据文件
                file_path = os.path.join(folder_path, filename)
                tau, gamma = read_data_file(file_path)
                
                if tau is not None and gamma is not None:
                    # 找出极大值和极小值点
                    max_indices = find_extrema(gamma, max=True)
                    min_indices = find_extrema(gamma, max=False)
                    
                    # 提取对应的点
                    max_points = [(tau[i], gamma[i]) for i in max_indices]
                    min_points = [(tau[i], gamma[i]) for i in min_indices]
                    
                    # 保存极值点到新文件
                    save_extrema_points(output_dir, filename, voltage, max_points, min_points)
                    
                    # 添加到汇总列表
                    all_voltage_values.append(voltage)
                    
                    # 为每个极值点添加对应的电压信息
                    max_with_voltage = [(voltage, x, y) for x, y in max_points]
                    min_with_voltage = [(voltage, x, y) for x, y in min_points]
                    
                    all_max_points.extend(max_with_voltage)
                    all_min_points.extend(min_with_voltage)
    
    # 按电压值排序
    all_voltage_values = np.array(all_voltage_values)
    sorted_indices = np.argsort(all_voltage_values)
    all_voltage_values = all_voltage_values[sorted_indices]
    
    # 获取用户选择的电压区间
    voltage_ranges = get_voltage_ranges(root, all_voltage_values)
    
    if voltage_ranges:
        # 绘制极值随电压变化的图
        plot_extrema_by_voltage_ranges(output_dir, all_max_points, all_min_points, voltage_ranges)
        
        # 绘制全部数据的图
        plot_extrema_vs_voltage(output_dir, all_max_points, all_min_points)
    
    print(f"处理完成！结果保存在: {output_dir}")

def get_voltage_ranges(root, all_voltage_values):
    """获取用户选择的电压区间"""
    voltage_ranges = []
    
    if len(all_voltage_values) == 0:
        messagebox.showinfo("提示", "没有找到有效的电压数据")
        return voltage_ranges
    
    # 创建一个新窗口
    range_window = tk.Toplevel(root)
    range_window.title("选择电压区间")
    range_window.geometry("600x400")
    
    # 显示可用的电压范围
    min_voltage = min(all_voltage_values)
    max_voltage = max(all_voltage_values)
    
    tk.Label(range_window, text=f"可用的电压范围: {min_voltage} V - {max_voltage} V").pack(pady=10)
    tk.Label(range_window, text="请输入要分析的电压区间（可以添加多个区间）").pack(pady=5)
    
    # 创建框架来存放区间输入
    ranges_frame = tk.Frame(range_window)
    ranges_frame.pack(pady=10, fill=tk.X, padx=20)
    
    ranges_list = []
    
    def add_range_row():
        range_row = tk.Frame(ranges_frame)
        range_row.pack(fill=tk.X, pady=5)
        
        tk.Label(range_row, text="从").pack(side=tk.LEFT)
        min_entry = tk.Entry(range_row, width=10)
        min_entry.pack(side=tk.LEFT, padx=5)
        min_entry.insert(0, str(min_voltage))
        
        tk.Label(range_row, text="V 到").pack(side=tk.LEFT)
        max_entry = tk.Entry(range_row, width=10)
        max_entry.pack(side=tk.LEFT, padx=5)
        max_entry.insert(0, str(max_voltage))
        
        tk.Label(range_row, text="V").pack(side=tk.LEFT)
        
        def remove_row():
            range_row.destroy()
            ranges_list.remove((min_entry, max_entry))
        
        remove_btn = tk.Button(range_row, text="删除", command=remove_row)
        remove_btn.pack(side=tk.LEFT, padx=10)
        
        ranges_list.append((min_entry, max_entry))
    
    # 添加第一个区间行
    add_range_row()
    
    # 添加更多区间的按钮
    tk.Button(range_window, text="添加另一个区间", command=add_range_row).pack(pady=10)
    
    result = []
    
    def confirm():
        nonlocal result
        for min_entry, max_entry in ranges_list:
            try:
                min_val = float(min_entry.get())
                max_val = float(max_entry.get())
                if min_val > max_val:
                    min_val, max_val = max_val, min_val
                result.append((min_val, max_val))
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数值")
                return
        
        range_window.destroy()
    
    tk.Button(range_window, text="确认", command=confirm).pack(pady=10)
    
    # 等待窗口关闭
    root.wait_window(range_window)
    
    return result

def read_data_file(file_path):
    """读取数据文件，跳过头部信息，提取tau和gamma值"""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            
            # 找到"tau, gamma(tau)"所在行
            data_start = 0
            for i, line in enumerate(lines):
                if "tau, gamma(tau)" in line:
                    data_start = i + 1
                    break
            
            # 提取数据
            tau = []
            gamma = []
            for line in lines[data_start:]:
                if line.strip():  # 跳过空行
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        try:
                            tau.append(float(parts[0]))
                            gamma.append(float(parts[1]))
                        except ValueError:
                            continue
            
            return np.array(tau), np.array(gamma)
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None, None

def find_extrema(data, max=True, order=3):
    """找出数据的极大值或极小值点的索引"""
    if max:
        return argrelextrema(data, np.greater, order=order)[0]
    else:
        return argrelextrema(data, np.less, order=order)[0]

def save_extrema_points(output_dir, original_filename, voltage, max_points, min_points):
    """保存极值点到新文件"""
    base_name = os.path.splitext(original_filename)[0]
    output_file = os.path.join(output_dir, f"{base_name}_extrema.txt")
    
    with open(output_file, 'w') as file:
        file.write(f"电压值: {voltage}V\n")
        file.write(f"原始文件: {original_filename}\n\n")
        
        file.write("极大值点:\n")
        file.write("tau, gamma(tau)\n")
        for tau, gamma in max_points:
            file.write(f"{tau:.15e}, {gamma:.15e}\n")
        
        file.write("\n极小值点:\n")
        file.write("tau, gamma(tau)\n")
        for tau, gamma in min_points:
            file.write(f"{tau:.15e}, {gamma:.15e}\n")

def plot_extrema_by_voltage_ranges(output_dir, max_points, min_points, voltage_ranges):
    """按照电压区间绘制极值点图"""
    
    # 转换为NumPy数组以便更好地处理
    max_data = np.array(max_points) if max_points else np.empty((0, 3))
    min_data = np.array(min_points) if min_points else np.empty((0, 3))
    
    # 绘制gamma值对应的图
    plt.figure(figsize=(12, 8))
    
    # 为不同的电压区间使用不同的颜色
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    for i, (min_voltage, max_voltage) in enumerate(voltage_ranges):
        # 选择电压区间内的数据点
        max_in_range = max_data[(max_data[:, 0] >= min_voltage) & (max_data[:, 0] <= max_voltage)] if len(max_data) > 0 else []
        min_in_range = min_data[(min_data[:, 0] >= min_voltage) & (min_data[:, 0] <= max_voltage)] if len(min_data) > 0 else []
        
        # 使用不同颜色绘制不同电压区间的数据点
        color_index = i % len(colors)
        
        # 绘制极大值点
        if len(max_in_range) > 0:
            plt.scatter(max_in_range[:, 0], max_in_range[:, 2], 
                        color=colors[color_index], marker='o',
                        label=f'极大值 [{min_voltage}-{max_voltage}V]')
        
        # 绘制极小值点
        if len(min_in_range) > 0:
            plt.scatter(min_in_range[:, 0], min_in_range[:, 2], 
                        color=colors[color_index], marker='x',
                        label=f'极小值 [{min_voltage}-{max_voltage}V]')
    
    plt.xlabel('电压值 (V)')
    plt.ylabel('gamma值')
    plt.title('不同电压区间的极值点(gamma)')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    plt.savefig(os.path.join(output_dir, 'extrema_gamma_by_ranges.png'), dpi=300)
    
    # 绘制tau值对应的图
    plt.figure(figsize=(12, 8))
    
    for i, (min_voltage, max_voltage) in enumerate(voltage_ranges):
        # 选择电压区间内的数据点
        max_in_range = max_data[(max_data[:, 0] >= min_voltage) & (max_data[:, 0] <= max_voltage)] if len(max_data) > 0 else []
        min_in_range = min_data[(min_data[:, 0] >= min_voltage) & (min_data[:, 0] <= max_voltage)] if len(min_data) > 0 else []
        
        # 使用不同颜色绘制不同电压区间的数据点
        color_index = i % len(colors)
        
        # 绘制极大值点
        if len(max_in_range) > 0:
            plt.scatter(max_in_range[:, 0], max_in_range[:, 1], 
                        color=colors[color_index], marker='o',
                        label=f'极大值 [{min_voltage}-{max_voltage}V]')
        
        # 绘制极小值点
        if len(min_in_range) > 0:
            plt.scatter(min_in_range[:, 0], min_in_range[:, 1], 
                        color=colors[color_index], marker='x',
                        label=f'极小值 [{min_voltage}-{max_voltage}V]')
    
    plt.xlabel('电压值 (V)')
    plt.ylabel('tau值')
    plt.title('不同电压区间的极值点(tau)')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    plt.savefig(os.path.join(output_dir, 'extrema_tau_by_ranges.png'), dpi=300)

def plot_extrema_vs_voltage(output_dir, max_points, min_points):
    """绘制极值点随电压变化的图"""
    plt.figure(figsize=(12, 8))
    
    # 将数据点转换为电压、tau和gamma数组
    if max_points:
        max_data = np.array(max_points)
        voltages_max = max_data[:, 0]
        tau_max = max_data[:, 1]
        gamma_max = max_data[:, 2]
        plt.scatter(voltages_max, gamma_max, color='red', label='极大值')
    
    if min_points:
        min_data = np.array(min_points)
        voltages_min = min_data[:, 0]
        tau_min = min_data[:, 1]
        gamma_min = min_data[:, 2]
        plt.scatter(voltages_min, gamma_min, color='blue', label='极小值')
    
    plt.xlabel('电压值 (V)')
    plt.ylabel('gamma值')
    plt.title('极值点随电压变化关系')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    plt.savefig(os.path.join(output_dir, 'extrema_vs_voltage.png'), dpi=300)
    
    # 额外生成tau随电压变化的图
    plt.figure(figsize=(12, 8))
    
    if max_points:
        plt.scatter(voltages_max, tau_max, color='red', label='极大值(tau)')
    
    if min_points:
        plt.scatter(voltages_min, tau_min, color='blue', label='极小值(tau)')
    
    plt.xlabel('电压值 (V)')
    plt.ylabel('tau值')
    plt.title('极值点tau随电压变化关系')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    plt.savefig(os.path.join(output_dir, 'tau_vs_voltage.png'), dpi=300)

if __name__ == "__main__":
    main()