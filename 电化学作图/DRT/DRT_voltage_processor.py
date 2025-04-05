import os
import re
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import filedialog, simpledialog
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
    
    # 询问tau值范围
    tau_min = simpledialog.askfloat("输入", "请输入tau的最小值 (输入-1表示不设限)", initialvalue=-1)
    tau_max = simpledialog.askfloat("输入", "请输入tau的最大值 (输入-1表示不设限)", initialvalue=-1)
    
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
                    
                    # 根据tau范围过滤极值点
                    if tau_min != -1 or tau_max != -1:
                        max_points = filter_points_by_tau(max_points, tau_min, tau_max)
                        min_points = filter_points_by_tau(min_points, tau_min, tau_max)
                    
                    # 为每个文件绘制单独的图
                    plot_single_file(output_dir, filename, voltage, tau, gamma, max_points, min_points)
                    
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
    sorted_indices = np.argsort(all_voltage_values)
    all_voltage_values = np.array(all_voltage_values)[sorted_indices]
    
    # 绘制极值随电压变化的图
    plot_extrema_vs_voltage(output_dir, all_max_points, all_min_points)
    
    print(f"处理完成！结果保存在: {output_dir}")

def filter_points_by_tau(points, tau_min, tau_max):
    """根据tau值范围过滤点"""
    filtered_points = []
    for tau, gamma in points:
        if tau_min != -1 and tau < tau_min:
            continue
        if tau_max != -1 and tau > tau_max:
            continue
        filtered_points.append((tau, gamma))
    return filtered_points

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

def plot_single_file(output_dir, filename, voltage, tau, gamma, max_points, min_points):
    """为单个文件绘制图形"""
    base_name = os.path.splitext(filename)[0]
    plt.figure(figsize=(12, 8))
    
    # 绘制原始曲线
    plt.plot(tau, gamma, 'k-', linewidth=1, alpha=0.7)
    
    # 绘制极值点
    if max_points:
        max_tau = [point[0] for point in max_points]
        max_gamma = [point[1] for point in max_points]
        plt.scatter(max_tau, max_gamma, color='red', s=50, label='极大值')
    
    if min_points:
        min_tau = [point[0] for point in min_points]
        min_gamma = [point[1] for point in min_points]
        plt.scatter(min_tau, min_gamma, color='blue', s=50, label='极小值')
        
    plt.xscale('log')  # 设置x轴为对数坐标
    plt.xlabel('tau')
    plt.ylabel('gamma(tau)')
    plt.title(f'文件 {filename} (电压值: {voltage}V) 的 gamma(tau) 曲线及极值点')
    plt.legend()
    plt.grid(True)
    
    # 保存图片
    plt.savefig(os.path.join(output_dir, f'{base_name}_curve.png'), dpi=300)
    plt.close()

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
    plt.close()

if __name__ == "__main__":
    main()