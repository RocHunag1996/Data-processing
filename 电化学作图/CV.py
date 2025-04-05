# Roc_Huang
#
# 2025.04.06
#
# 程序功能：
# 本程序是一个循环伏安法（CV）数据分析工具，旨在通过读取实验数据，提取并分析电流-电压关系。
# 主要功能包括：
# 1. 从CV数据文件中提取电位、电流数据。
# 2. 支持电流密度（mA/mg）的计算，取决于用户输入的活性物质质量。
# 3. 提供绘制CV图像的功能，可以选择电流或电流密度进行可视化。
# 4. 拟合扫速与电流（或电流密度）极值的关系，生成拟合曲线并显示。
# 5. 自动将数据和生成的图像保存到文件中。
#
# 操作方法：
# 1. 用户输入活性物质质量（单位：mg），如需计算电流密度。
# 2. 选择是否使用电流密度（mA/mg）而非电流（mA）进行分析。
# 3. 点击“选择文件”按钮选择一个或多个CV数据文件进行处理。
# 4. 程序自动提取每个文件的最后一个完整周期数据，并生成相关图像。
# 5. 所有结果（图像和数据）将保存在原文件所在文件夹中。


import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# 全局变量，用于存储活性物质质量
active_material_mass = 0.0

# 提取数据的函数
def extract_scan_rate_and_data(file_path, active_mass):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # 提取扫速
    scan_rate = None
    for line in lines:
        if "Scan Rate (V/s)" in line:
            scan_rate = float(line.split('=')[1].strip())
            scan_rate_mV_s = scan_rate * 1000  # 转换为mV/s
            break
    
    # 提取数据部分
    data = []
    for line in lines:
        if line.strip() and line[0].isdigit():
            potential, current = line.split(',')
            data.append([float(potential), float(current)])
    
    df = pd.DataFrame(data, columns=['Potential/V', 'Current/A'])
    
    # 单位转换：电流(A) -> 电流(mA)
    df['Current/A'] = df['Current/A'] * 1e3  # 转换为mA
    
    # 如果提供了活性物质质量，计算电流密度(mA/mg)
    if active_mass > 0:
        df['Current_Density'] = df['Current/A'] / active_mass  # mA/mg
    else:
        df['Current_Density'] = df['Current/A']  # 如果质量为0，则不进行转换
    
    # 寻找完整的最后一个周期
    # 在CV数据中，电位通常是从高到低再回到高，或从低到高再回到低
    
    # 首先判断数据的大致趋势，确定是高-低-高还是低-高-低模式
    potential_first = df['Potential/V'].iloc[0]
    potential_middle = df['Potential/V'].iloc[len(df)//2]
    potential_last = df['Potential/V'].iloc[-1]
    
    print(f"首点电位: {potential_first:.3f}V, 中点电位: {potential_middle:.3f}V, 末点电位: {potential_last:.3f}V")
    
    # 确定数据点是否足够构成一个完整周期
    if len(df) < 100:
        print(f"警告：数据点数量少于100 ({len(df)}点)，可能不构成完整周期")
    
    # 探测电位的变化方向
    # 计算电位的一阶差分
    df['potential_diff'] = df['Potential/V'].diff()
    
    # 查找方向变化点 (正->负 或 负->正)
    direction_changes = []
    
    for i in range(1, len(df)-1):
        if (df['potential_diff'].iloc[i] * df['potential_diff'].iloc[i+1]) < 0:
            direction_changes.append(i)
    
    print(f"检测到的方向变化点数量: {len(direction_changes)}")
    
    if len(direction_changes) >= 2:
        # 至少有两个变化点，取最后两个变化点之间的数据作为最后一个周期
        # 但需要稍微扩展一下范围，确保包含完整的周期
        start_idx = direction_changes[-2]
        end_idx = len(df) - 1  # 使用所有剩余数据，确保包含完整周期
        
        print(f"提取周期范围: 点{start_idx} 到 点{end_idx}")
        last_cycle_data = df.iloc[start_idx:end_idx + 1].copy()
    else:
        # 如果找不到足够的变化点，回退到使用整个数据集
        print("未检测到足够的方向变化点，使用全部数据")
        last_cycle_data = df.copy()
    
    # 打印提取周期的电位范围，验证是否合理
    print(f"提取的周期电位范围: {last_cycle_data['Potential/V'].min():.3f}V 到 {last_cycle_data['Potential/V'].max():.3f}V")
    
    return scan_rate_mV_s, last_cycle_data

# 绘制CV数据的函数 - 支持电流和电流密度
def plot_cv_data(scan_rates, all_last_cycle_data, save_path, use_density=False):
    plt.figure(figsize=(10, 7))
    
    # 使用不同颜色和线条样式
    colors = ['blue', 'orange', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    
    # 将不同扫速的CV曲线绘制在同一张图上
    for i, (scan_rate, last_cycle_data) in enumerate(zip(scan_rates, all_last_cycle_data)):
        color_idx = i % len(colors)
        if use_density and 'Current_Density' in last_cycle_data.columns:
            plt.plot(last_cycle_data['Potential/V'], last_cycle_data['Current_Density'], 
                    color=colors[color_idx], label=f"Scan Rate: {scan_rate} mV/s")
        else:
            plt.plot(last_cycle_data['Potential/V'], last_cycle_data['Current/A'], 
                    color=colors[color_idx], label=f"Scan Rate: {scan_rate} mV/s")
    
    plt.xlabel('Potential (V)', fontsize=12)
    
    if use_density and 'Current_Density' in all_last_cycle_data[0].columns:
        plt.ylabel('Current Density (mA/mg)', fontsize=12)
        plt.title('Cyclic Voltammetry - Last Cycle (Current Density)', fontsize=14)
    else:
        plt.ylabel('Current (mA)', fontsize=12)
        plt.title('Cyclic Voltammetry - Last Cycle', fontsize=14)
    
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)  # 保存高分辨率图像
    plt.close()

# 扫速与极值拟合函数 - 支持电流和电流密度
def fit_scan_rate(scan_rates, max_values, min_values, save_path, use_density=False):
    # 将数据排序以确保正确拟合
    sorted_data = sorted(zip(scan_rates, max_values, min_values))
    scan_rates = [x[0] for x in sorted_data]
    max_values = [x[1] for x in sorted_data]
    min_values = [x[2] for x in sorted_data]
    
    # 转换为numpy数组以便于计算
    scan_rates_np = np.array(scan_rates)
    max_values_np = np.array(max_values)
    min_values_np = np.array(min_values)
    
    # 线性拟合
    slope_max, intercept_max, r_value_max, p_value_max, std_err_max = stats.linregress(scan_rates_np, max_values_np)
    slope_min, intercept_min, r_value_min, p_value_min, std_err_min = stats.linregress(scan_rates_np, min_values_np)

    if use_density:
        print(f"Max current density fit: y = {slope_max:.4e} * x + {intercept_max:.4e}, R² = {r_value_max**2:.4f}")
        print(f"Min current density fit: y = {slope_min:.4e} * x + {intercept_min:.4e}, R² = {r_value_min**2:.4f}")
    else:
        print(f"Max current fit: y = {slope_max:.4e} * x + {intercept_max:.4e}, R² = {r_value_max**2:.4f}")
        print(f"Min current fit: y = {slope_min:.4e} * x + {intercept_min:.4e}, R² = {r_value_min**2:.4f}")

    plt.figure(figsize=(10, 8))
    
    # 创建一个更宽的范围用于拟合线的展示
    scan_rate_range = np.linspace(min(scan_rates) * 0.9, max(scan_rates) * 1.1, 100)
    
    # 绘制散点图
    plt.scatter(scan_rates, max_values, label='Max Values', color='red', s=50)
    plt.scatter(scan_rates, min_values, label='Min Values', color='blue', s=50)
    
    # 绘制拟合线
    max_fit_line = slope_max * scan_rate_range + intercept_max
    min_fit_line = slope_min * scan_rate_range + intercept_min
    
    plt.plot(scan_rate_range, max_fit_line, 
             label=f'Max: y = {slope_max:.4f}x + {intercept_max:.4f}, R² = {r_value_max**2:.4f}', 
             linestyle='--', color='darkred')
    plt.plot(scan_rate_range, min_fit_line, 
             label=f'Min: y = {slope_min:.4f}x + {intercept_min:.4f}, R² = {r_value_min**2:.4f}', 
             linestyle='--', color='darkblue')
    
    plt.xlabel('Scan Rate (mV/s)', fontsize=12)
    
    if use_density:
        plt.ylabel('Current Density (mA/mg)', fontsize=12)
        plt.title('Current Density vs Scan Rate', fontsize=14)
    else:
        plt.ylabel('Current (mA)', fontsize=12)
        plt.title('Current vs Scan Rate', fontsize=14)
    
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()

# 选择文件并处理
def select_files_and_process():
    # 获取活性物质质量
    global active_material_mass
    try:
        active_material_mass = float(mass_entry.get())
        if active_material_mass < 0:
            messagebox.showerror("输入错误", "活性物质质量不能为负数")
            return
    except ValueError:
        if mass_entry.get().strip() == "":
            active_material_mass = 0.0  # 如果为空，设为0
        else:
            messagebox.showerror("输入错误", "请输入有效的数字")
            return
    
    # 获取是否使用电流密度
    use_current_density = current_density_var.get()
    
    file_paths = filedialog.askopenfilenames(title="选择CV数据文件", filetypes=[("Text Files", "*.txt")])
    
    if not file_paths:
        print("没有选择文件")
        return

    scan_rates = []
    all_last_cycle_data = []
    max_values = []
    min_values = []
    save_folder = None

    # 处理选定的文件
    for file_path in file_paths:
        print(f"\n处理文件: {os.path.basename(file_path)}")
        scan_rate, last_cycle_data = extract_scan_rate_and_data(file_path, active_material_mass)

        # 获取文件所在的文件夹路径
        save_folder = os.path.dirname(file_path)

        # 单个文件CV图像
        image_name = f"{os.path.basename(file_path).split('.')[0]}_Last_Cycle"
        if use_current_density and active_material_mass > 0:
            image_name += "_Density"
        image_path = os.path.join(save_folder, f"{image_name}.png")
        
        plt.figure(figsize=(8, 6))
        if use_current_density and active_material_mass > 0:
            plt.plot(last_cycle_data['Potential/V'], last_cycle_data['Current_Density'])
            plt.ylabel('Current Density (mA/mg)')
        else:
            plt.plot(last_cycle_data['Potential/V'], last_cycle_data['Current/A'])
            plt.ylabel('Current (mA)')
            
        plt.xlabel('Potential (V)')
        plt.title(f'Cyclic Voltammetry - {os.path.basename(file_path)} - {scan_rate} mV/s')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig(image_path)
        plt.close()
        
        all_last_cycle_data.append(last_cycle_data)
        scan_rates.append(scan_rate)
        
        # 提取极大值和极小值
        if use_current_density and active_material_mass > 0:
            max_value = last_cycle_data['Current_Density'].max()
            min_value = last_cycle_data['Current_Density'].min()
            print(f"最大电流密度: {max_value:.4f} mA/mg")
            print(f"最小电流密度: {min_value:.4f} mA/mg")
        else:
            max_value = last_cycle_data['Current/A'].max()
            min_value = last_cycle_data['Current/A'].min()
            print(f"最大电流: {max_value:.4f} mA")
            print(f"最小电流: {min_value:.4f} mA")
            
        print("-" * 40)
        
        max_values.append(max_value)
        min_values.append(min_value)

    # 将所有扫速的CV曲线绘制在同一张图中
    if save_folder and len(all_last_cycle_data) > 0:
        cv_image_name = "All_Scan_Rates_Last_Cycle"
        if use_current_density and active_material_mass > 0:
            cv_image_name += "_Density"
        cv_image_path = os.path.join(save_folder, f"{cv_image_name}.png")
        plot_cv_data(scan_rates, all_last_cycle_data, cv_image_path, use_current_density and active_material_mass > 0)

        # 扫速与电流极值拟合图像
        fit_image_name = "ScanRate_vs_Current"
        if use_current_density and active_material_mass > 0:
            fit_image_name += "_Density"
        fit_image_path = os.path.join(save_folder, f"{fit_image_name}_Fit.png")
        fit_scan_rate(scan_rates, max_values, min_values, fit_image_path, use_current_density and active_material_mass > 0)
        
        print(f"所有图像已保存到: {save_folder}")
    else:
        print("没有有效数据可以处理")

# 创建主界面
def create_main_window():
    window = tk.Tk()
    window.title("循环伏安法(CV)数据分析工具")
    window.geometry("550x400")

    # 创建一个框架来容纳说明和输入区域
    main_frame = ttk.Frame(window, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 添加说明标签
    instructions = (
        "使用说明:\n"
        "1. 输入活性物质质量(mg)，如需计算电流密度\n"
        "2. 选择是否使用电流密度(mA/mg)而非电流(mA)\n"
        "3. 点击'选择文件'按钮选择一个或多个CV数据文件\n"
        "4. 程序将自动提取每个文件的最后一个完整周期\n"
        "5. 生成CV图像并拟合扫速与电流(密度)极值关系\n"
        "6. 所有图像保存在原文件所在文件夹"
    )
    
    instructions_label = ttk.Label(main_frame, text=instructions, justify=tk.LEFT)
    instructions_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

    # 创建输入区域框架
    input_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
    input_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=5, pady=5)

    # 活性物质质量输入
    mass_label = ttk.Label(input_frame, text="活性物质质量 (mg):")
    mass_label.grid(row=0, column=0, sticky=tk.W, pady=5)
    
    global mass_entry
    mass_entry = ttk.Entry(input_frame, width=15)
    mass_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
    mass_entry.insert(0, "0.0")  # 默认值

    # 选择使用电流还是电流密度
    global current_density_var
    current_density_var = tk.BooleanVar(value=False)
    current_density_check = ttk.Checkbutton(input_frame, text="使用电流密度(mA/mg)", variable=current_density_var)
    current_density_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)

    # 按钮区域框架
    button_frame = ttk.Frame(main_frame, padding="10")
    button_frame.grid(row=2, column=0, sticky=tk.EW, pady=10)

    # 按钮：选择文件
    select_button = ttk.Button(button_frame, text="选择文件并开始处理", command=select_files_and_process)
    select_button.pack(pady=10)

    # 状态区域
    status_frame = ttk.LabelFrame(main_frame, text="状态信息", padding="10")
    status_frame.grid(row=3, column=0, sticky=tk.NSEW, padx=5, pady=5)
    
    status_label = ttk.Label(status_frame, text="就绪，等待操作...")
    status_label.pack(fill=tk.X)

    # 设置网格权重，使组件在窗口调整大小时正确扩展
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(3, weight=1)

    # 运行主界面
    window.mainloop()

# 启动程序
if __name__ == "__main__":
    create_main_window()
