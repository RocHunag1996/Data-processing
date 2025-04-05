
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import tkinter as tk
from tkinter import filedialog, simpledialog
import matplotlib

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os
from scipy.signal import find_peaks

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 定义固定的X轴范围
X_MIN = 1e-5
X_MAX = 10

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
    
    # 存储所有文件的数据
    all_data = []
    
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
                
                if tau is not None and gamma is not None and len(tau) > 0 and len(gamma) > 0:
                    # 过滤数据到指定X轴范围
                    mask = (tau >= X_MIN) & (tau <= X_MAX)
                    tau_filtered = tau[mask]
                    gamma_filtered = gamma[mask]
                    
                    if len(tau_filtered) > 0:
                        # 添加到数据列表
                        all_data.append((voltage, tau_filtered, gamma_filtered))
    
    # 按电压值排序
    all_data.sort(key=lambda x: x[0])
    
    # 如果没有找到数据，则退出
    if not all_data:
        print("没有找到有效的数据文件")
        return
    
    # 显示可用的电压值
    voltages = [data[0] for data in all_data]
    print(f"可用的电压值: {', '.join([f'{v}V' for v in voltages])}")
    
    # 通过对话框获取电压区间
    min_voltage = simpledialog.askfloat("输入最小电压", 
                                         f"请输入最小电压值 (可用范围: {min(voltages)}-{max(voltages)}V):", 
                                         minvalue=min(voltages), maxvalue=max(voltages))
    if min_voltage is None:
        min_voltage = min(voltages)
    
    max_voltage = simpledialog.askfloat("输入最大电压", 
                                         f"请输入最大电压值 (可用范围: {min_voltage}-{max(voltages)}V):", 
                                         minvalue=min_voltage, maxvalue=max(voltages))
    if max_voltage is None:
        max_voltage = max(voltages)
        
    
    # 筛选指定电压区间的数据
    filtered_data = [(v, t, g) for v, t, g in all_data if min_voltage <= v <= max_voltage]
    
    print(f"已选择电压区间: {min_voltage}V - {max_voltage}V")
    print(f"包含的数据文件数量: {len(filtered_data)}")
    
    # 绘制图表
    if filtered_data:
        # 绘制二维曲线图 - 带标记和不带标记的版本
        plot_2d_curves(filtered_data, output_dir, min_voltage, max_voltage, with_markers=True)
        plot_2d_curves(filtered_data, output_dir, min_voltage, max_voltage, with_markers=False)
        
        # 绘制热图 - 带标记和不带标记的版本
# 生成两个版本
        plot_heatmap_with_markers(filtered_data, output_dir, min_voltage, max_voltage)
        plot_heatmap_plain(filtered_data, output_dir, min_voltage, max_voltage)

        
        # 绘制山脉图 - 带标记和不带标记的版本
        plot_mountain_view(filtered_data, output_dir, min_voltage, max_voltage, with_markers=True)
        plot_mountain_view(filtered_data, output_dir, min_voltage, max_voltage, with_markers=False)

        # 绘制3D图 - 带标记和不带标记的版本
        plot_mountain_view_3d(filtered_data, output_dir, min_voltage, max_voltage, X_MIN, X_MAX, with_markers=True)
        # plot_heatmap_3d(filtered_data, output_dir, min_voltage, max_voltage, with_markers=False)

        
        print(f"绘图完成！结果保存在: {output_dir}")
    else:
        print("在选定的电压区间内没有有效的数据")

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

def plot_2d_curves(data, output_dir, min_voltage, max_voltage, with_markers=True):
    """绘制二维曲线图，使用电压值决定线条颜色，根据参数决定是否标记极大值和极小值点"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 获取电压值范围
    voltages = [d[0] for d in data]
    vmin, vmax = min(voltages), max(voltages)
    
    # 创建颜色映射
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(vmin, vmax)
    
    # 找出y轴的范围
    all_gamma = []
    for _, _, gamma in data:
        all_gamma.extend(gamma)
    
    if all_gamma:
        y_min, y_max = min(all_gamma), max(all_gamma)
        y_padding = (y_max - y_min) * 0.1  # 添加10%的边距
        y_min = max(0, y_min - y_padding)  # y值不应为负
        y_max = y_max + y_padding
    else:
        y_min, y_max = 0, 1  # 默认值
    
    # 绘制每个数据集
    for voltage, tau, gamma in data:
        color = cmap(norm(voltage))
        ax.plot(tau, gamma, color=color, label=f"{voltage}V")
        
        if with_markers:
            # 找出所有极大值点
            peaks, _ = find_peaks(gamma)  # 找到所有的局部极大值点
            
            # 标记极大值点
            for peak in peaks:
                ax.scatter(tau[peak], gamma[peak], color='red', s=40, zorder=5)
            
            # 找出所有极小值点（通过对数据取负值然后找峰值）
            inv_gamma = -gamma
            valleys, _ = find_peaks(inv_gamma)  # 找到所有的局部极小值点
            
            # 标记极小值点
            for valley in valleys:
                ax.scatter(tau[valley], gamma[valley], color='blue', s=40, zorder=5)
    
    # 添加颜色条
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # 仅用来生成颜色条
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('电压值 (V)')
    
    ax.set_xlabel('tau')
    ax.set_ylabel('gamma(tau)')
    marker_status = "带标记" if with_markers else "无标记"
    ax.set_title(f'电压区间 {min_voltage}V - {max_voltage}V 的二维曲线图（{marker_status}）')
    ax.grid(True)
    ax.set_xscale('log')  # X轴使用对数坐标
    
    # 设置固定的X轴范围
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(y_min, y_max)
    
    # 保存图片
    plt.tight_layout()
    marker_suffix = "with_markers" if with_markers else "no_markers"
    plt.savefig(os.path.join(output_dir, f'2d_curves_{marker_suffix}_{min_voltage}V-{max_voltage}V.png'), dpi=300)
    plt.close(fig)
    
    # 添加一个含图例的版本
    fig, ax = plt.subplots(figsize=(14, 10))
    for voltage, tau, gamma in data:
        color = cmap(norm(voltage))
        ax.plot(tau, gamma, color=color, label=f"{voltage}V")
        
        if with_markers:
            peaks, _ = find_peaks(gamma)  # 找到所有的局部极大值点
            for peak in peaks:
                ax.scatter(tau[peak], gamma[peak], color='red', s=40, zorder=5)
            
            inv_gamma = -gamma
            valleys, _ = find_peaks(inv_gamma)  # 找到所有的局部极小值点
            for valley in valleys:
                ax.scatter(tau[valley], gamma[valley], color='blue', s=40, zorder=5)
    
    ax.set_xlabel('tau')
    ax.set_ylabel('gamma(tau)')
    ax.set_title(f'电压区间 {min_voltage}V - {max_voltage}V 的二维曲线图（含图例，{marker_status}）')
    ax.grid(True)
    ax.set_xscale('log')  # X轴使用对数坐标
    
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(y_min, y_max)
    
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'2d_curves_with_legend_{marker_suffix}_{min_voltage}V-{max_voltage}V.png'), dpi=300)
    plt.close(fig)
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
from scipy.signal import find_peaks

def plot_heatmap_common_setup(data, num_points=500):
    """公共数据准备函数"""
    # 创建对数均匀分布的tau网格
    tau_grid = np.logspace(np.log10(X_MIN), np.log10(X_MAX), num_points)
    
    # 准备电压数据和排序
    voltages = sorted({d[0] for d in data})
    gamma_matrix = np.zeros((len(voltages), len(tau_grid)))
    
    # 执行插值操作
    for i, voltage in enumerate(voltages):
        voltage_data = next((d for d in data if d[0] == voltage), None)
        if not voltage_data or len(voltage_data[1]) < 2:
            continue
            
        _, tau, gamma = voltage_data
        
        # 数据清洗
        valid_mask = (~np.isnan(tau)) & (~np.isnan(gamma)) & (tau > 0)
        log_tau = np.log10(tau[valid_mask])
        gamma_clean = gamma[valid_mask]
        
        if len(log_tau) < 2:
            continue
            
        # 三次样条插值
        interp_fn = interp1d(log_tau, gamma_clean, kind='cubic', 
                           bounds_error=False, fill_value=np.nan)
        gamma_matrix[i, :] = interp_fn(np.log10(tau_grid))
    
    return tau_grid, voltages, gamma_matrix

# 带标记版本
def plot_heatmap_with_markers(data, output_dir, min_voltage, max_voltage):
    """生成带极值点标记的热图"""
    # 公共数据准备
    tau_grid, voltages, gamma_matrix = plot_heatmap_common_setup(data)
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 8))
    X, Y = np.meshgrid(np.log10(tau_grid), voltages)
    
    # 绘制热图
    pm = ax.pcolormesh(X, Y, gamma_matrix,
                      cmap='viridis',
                      shading='gouraud',
                      vmin=np.nanpercentile(gamma_matrix, 5),
                      vmax=np.nanpercentile(gamma_matrix, 95))
    
    # 标记极值点
    marker_size = 25
    for voltage in voltages:
        voltage_data = next((d for d in data if d[0] == voltage), None)
        if not voltage_data:
            continue
            
        _, tau, gamma = voltage_data
        valid_gamma = gamma[~np.isnan(gamma)]
        if len(valid_gamma) < 10:
            continue
            
        # 寻找极值
        # peaks, _ = find_peaks(valid_gamma, prominence=0.5*np.std(valid_gamma))

        # 修改后（更全面的检测）
        peaks, _ = find_peaks(
            valid_gamma,
            height=np.percentile(valid_gamma, 10),  # 最低高度阈值
            prominence=0.3*np.std(valid_gamma),    # 降低显著性要求
            width=3,                               # 最小峰宽
            distance=5                             # 峰间最小间隔
        )
        valleys, _ = find_peaks(-valid_gamma, prominence=0.5*np.std(valid_gamma))
        
        # 绘制标记
        for idx in peaks:
            if idx < len(tau):
                ax.scatter(np.log10(tau[idx]), voltage, 
                          color='red', s=marker_size,
                          edgecolor='white', linewidth=0.7,
                          zorder=5)
                
        for idx in valleys:
            if idx < len(tau):
                ax.scatter(np.log10(tau[idx]), voltage, 
                          color='blue', s=marker_size,
                          edgecolor='white', linewidth=0.7,
                          zorder=5)
    
    # 坐标轴和样式设置
    _configure_axes(ax, min_voltage, max_voltage)
    
    # 添加颜色条
    cbar = fig.colorbar(pm, ax=ax, pad=0.02)
    cbar.set_label('Gamma值', rotation=270, labelpad=15)
    
    # 保存图像
    _save_figure(output_dir, min_voltage, max_voltage, "with_markers")

# 无标记版本
def plot_heatmap_plain(data, output_dir, min_voltage, max_voltage):
    """生成无标记的纯净热图"""
    # 公共数据准备
    tau_grid, voltages, gamma_matrix = plot_heatmap_common_setup(data)
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 8))
    X, Y = np.meshgrid(np.log10(tau_grid), voltages)
    
    # 绘制热图
    pm = ax.pcolormesh(X, Y, gamma_matrix,
                      cmap='viridis',
                      shading='gouraud',
                      vmin=np.nanpercentile(gamma_matrix, 5),
                      vmax=np.nanpercentile(gamma_matrix, 95))
    
    # 坐标轴和样式设置
    _configure_axes(ax, min_voltage, max_voltage)
    
    # 添加颜色条
    cbar = fig.colorbar(pm, ax=ax, pad=0.02)
    cbar.set_label('Gamma值', rotation=270, labelpad=15)
    
    # 保存图像
    _save_figure(output_dir, min_voltage, max_voltage, "plain")

# 公共配置函数
def _configure_axes(ax, min_voltage, max_voltage):
    """坐标轴统一配置"""
    ax.set_xlim(np.log10(X_MIN), np.log10(X_MAX))
    ax.set_xticks(np.linspace(np.log10(X_MIN), np.log10(X_MAX), 7))
    ax.set_xticklabels([f"10$^{{{int(x)}}}$" for x in 
                       np.linspace(np.log10(X_MIN), np.log10(X_MAX), 7)],
                      rotation=30, ha='right')
    ax.set_xlabel('Tau (对数刻度)')
    ax.set_ylabel('电压 (V)')
    ax.set_title(f'{min_voltage}V-{max_voltage}V 电压区间热图', pad=15)

# 公共保存函数
def _save_figure(output_dir, min_v, max_v, suffix):
    """统一保存逻辑"""
    os.makedirs(output_dir, exist_ok=True)
    filename = f"heatmap_{min_v}V-{max_v}V_{suffix}.png"
    plt.savefig(os.path.join(output_dir, filename), 
               dpi=300, bbox_inches='tight')
    plt.close()



def plot_mountain_view(data, output_dir, min_voltage, max_voltage, with_markers=True):
    """绘制山脉图，每个电压值对应一个曲线，并堆叠显示"""
    fig, ax = plt.subplots(figsize=(6, 8))
    
    # 获取电压值范围
    voltages = [d[0] for d in data]
    vmin, vmax = min(voltages), max(voltages)
    
    # 创建颜色映射
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(vmin, vmax)
    
    # 计算在X轴范围内的Y轴最大值
    filtered_gamma_values = []
    for voltage, tau, gamma in data:
        if len(gamma) > 0:
            filtered_gamma_values.append(np.max(gamma))
    
    max_y_in_range = max(filtered_gamma_values) if filtered_gamma_values else 0
    # y_spacing = max_y_in_range * 0.1  # 使用10%作为间距
    y_spacing = 200
    
    # 导入峰值检测函数
    from scipy.signal import find_peaks
    
    # 预计算所有曲线的Y轴范围
    y_max_values = []
    y_offset = 0
    for voltage, tau, gamma in data:
        y_max_values.append(np.max(gamma + y_offset))
        y_offset += y_spacing
    
    # 设置Y轴范围：从0到最大Y值 + 少量padding
    y_padding = max_y_in_range * 0.1  # 10%的额外空间
    y_max = max(y_max_values) + y_padding if y_max_values else y_padding
    
    # 重新绘制（因为前面只是预计算）...
    y_offset = 0
    for voltage, tau, gamma in data:
        color = cmap(norm(voltage))
        ax.plot(tau, gamma + y_offset, color=color, label=f"{voltage}V")
        ax.fill_between(tau, y_offset, gamma + y_offset, color=color, alpha=0.3)
        
        if with_markers:
            # 寻找极大值点
            peaks, _ = find_peaks(gamma)
            
            # 标记极大值点
            for peak in peaks:
                ax.scatter(tau[peak], gamma[peak] + y_offset, color='red', s=10, zorder=2)
            
            # # 寻找极小值点
            # inv_gamma = -gamma
            # valleys, _ = find_peaks(inv_gamma)
            
            # # 标记极小值点
            # for valley in valleys:
            #     ax.scatter(tau[valley], gamma[valley] + y_offset, color='blue', s=40, zorder=5)
        
        y_offset += y_spacing
    
    # 添加图例、标签等
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.set_xlabel('tau')
    ax.set_ylabel('gamma(tau) (带偏移)')
    marker_status = "带标记" if with_markers else "无标记"
    ax.set_title(f'电压区间 {min_voltage}V - {max_voltage}V 的山脉图（{marker_status}）')
    ax.grid(True)
    ax.set_xscale('log')
    
    # 设置固定的X轴范围
    # 设置固定的X轴范围
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(0, y_max)
    
    # 保存图片
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    marker_suffix = "with_markers" if with_markers else "no_markers"
    plt.savefig(os.path.join(output_dir, f'mountain_view_{marker_suffix}_{min_voltage}V-{max_voltage}V.png'), dpi=300)
    plt.close(fig)



def plot_mountain_view_3d(data, output_dir, min_voltage, max_voltage, X_MIN, X_MAX, with_markers=True):
    """3D版本的山脉图，X轴为tau（对数坐标），Y轴为电压，Z轴为gamma值"""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # 电压值和颜色映射
    voltages = [d[0] for d in data]
    cmap = plt.get_cmap('viridis')
    norm = plt.Normalize(min(voltages), max(voltages))

    # 核心绘图逻辑
    for voltage, tau, gamma in data:
        color = cmap(norm(voltage))
        
        # 直接绘制3D曲线（无需垂直偏移）
        ax.plot(np.log10(tau),        # X轴取对数
                [voltage]*len(tau),   # Y轴为电压值
                gamma,                # Z轴为gamma值
                color=color,
                label=f"{voltage}V",
                alpha=0.7)
        
        # 标记极值点
        if with_markers and len(gamma) > 0:
            peaks, _ = find_peaks(gamma, prominence=np.percentile(gamma, 75))
            for peak in peaks:
                ax.scatter(np.log10(tau[peak]), 
                          voltage, 
                          gamma[peak],
                          color='red', 
                          s=30,
                          edgecolor='white')

    # 坐标轴设置
    ax.set_xlabel('log10(tau)')
    ax.set_ylabel('Voltage (V)')
    ax.set_zlabel('gamma(tau)')
    
    # 手动设置刻度标签（将对数值转回实际值）
    x_ticks = np.logspace(np.log10(X_MIN), np.log10(X_MAX), 6)
    ax.set_xticks(np.log10(x_ticks))
    ax.set_xticklabels([f"{x:.1e}" for x in x_ticks])
    
    ax.set_title(f'3D电压谱 {min_voltage}V-{max_voltage}V')
    ax.grid(True)
    ax.view_init(elev=25, azim=-45)  # 设置视角
    
    # 色标说明
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, pad=0.15)  # 正确方式
    cbar.set_label('Voltage (V)')

    # 保存图像
    plt.tight_layout()
    os.makedirs(output_dir, exist_ok=True)
    marker_suffix = "_marked" if with_markers else ""
    plt.savefig(os.path.join(output_dir, f'3d_mountain_{min_voltage}V-{max_voltage}V{marker_suffix}.png'), 
               dpi=300, bbox_inches='tight')
    plt.close(fig)





if __name__ == "__main__":
    main()
