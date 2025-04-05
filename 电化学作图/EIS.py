# Roc_Huang
#
# 2025.04.06
#
# 程序功能：
# 本程序是一个EIS（电化学阻抗谱）数据分析工具，旨在通过读取EIS实验数据，提取并分析阻抗数据。
# 主要功能包括：
# 1. 选择多个EIS数据文件（.txt格式），自动提取电压值及阻抗数据。
# 2. 支持生成多种数据可视化图表，包括：
#    - Nyquist图
#    - Mountain图
#    - Heatmap图
#    - 3D表面图
# 3. 提供数据处理和图像保存功能，生成的数据和图像会自动保存为文件。
# 4. 提供结果保存功能，将所有图表和数据保存为Excel文件及PNG图像。

# 操作方法：
# 1. 点击“Select Files”按钮选择一个或多个EIS数据文件。
# 2. 点击“Process Data”按钮，程序会自动处理选中的文件，提取数据。
# 3. 处理完成后，选择不同类型的图表生成，包括Nyquist图、Mountain图、Heatmap图和3D表面图。
# 4. 点击“Save Results”按钮，保存数据分析结果和所有生成的图像。

# 作者：Roc_Huang

import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import LinearSegmentedColormap
import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D

class EISAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("EIS Data Analyzer")
        self.root.geometry("1000x800")
        
        self.files = []
        self.data_frames = []
        self.voltage_values = []
        
        # Create main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create button frame
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        # Add buttons
        self.select_files_btn = tk.Button(self.button_frame, text="Select Files", command=self.select_files)
        self.select_files_btn.pack(side=tk.LEFT, padx=5)
        
        self.process_btn = tk.Button(self.button_frame, text="Process Data", command=self.process_data, state=tk.DISABLED)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.nyquist_btn = tk.Button(self.button_frame, text="Nyquist Plot", command=self.create_nyquist_plot, state=tk.DISABLED)
        self.nyquist_btn.pack(side=tk.LEFT, padx=5)
        
        self.mountain_btn = tk.Button(self.button_frame, text="Mountain Plot", command=self.create_mountain_plot, state=tk.DISABLED)
        self.mountain_btn.pack(side=tk.LEFT, padx=5)
        
        self.heatmap_btn = tk.Button(self.button_frame, text="Heatmap", command=self.create_heatmap, state=tk.DISABLED)
        self.heatmap_btn.pack(side=tk.LEFT, padx=5)
        
        self.surface_btn = tk.Button(self.button_frame, text="3D Surface", command=self.create_3d_surface, state=tk.DISABLED)
        self.surface_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(self.button_frame, text="Save Results", command=self.save_results, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Create status frame
        self.status_frame = tk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="Select files to start")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Create plot frame
        self.plot_frame = tk.Frame(self.main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Initialize plot figure
        self.fig = Figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        
        # Data storage
        self.combined_df = None
        self.output_dir = None
        
    def select_files(self):
        filetypes = [("Text files", "*.txt"), ("All files", "*.*")]
        self.files = filedialog.askopenfilenames(title="Select EIS data files", filetypes=filetypes)
        
        if self.files:
            self.status_label.config(text=f"Selected {len(self.files)} files")
            self.process_btn.config(state=tk.NORMAL)
            self.output_dir = os.path.dirname(self.files[0])
        else:
            self.status_label.config(text="No files selected")
    
    def extract_voltage(self, file_content):
        voltage_match = re.search(r"Init E \(V\) = ([-+]?\d*\.\d+|\d+)", file_content)
        if voltage_match:
            return float(voltage_match.group(1))
        return None
    
    def extract_impedance_data(self, file_content):
        # Skip header lines and extract impedance data
        lines = file_content.split("\n")
        data = []
        data_started = False
        
        for line in lines:
            line = line.strip()
            if line.startswith("Freq/Hz"):
                data_started = True
                continue
            
            if data_started and line:
                parts = line.split(",")
                if len(parts) >= 4:
                    try:
                        freq = float(parts[0].strip())
                        z_real = float(parts[1].strip())
                        z_imag = float(parts[2].strip())
                        z_abs = float(parts[3].strip())
                        phase = float(parts[4].strip()) if len(parts) > 4 else 0.0
                        data.append([freq, z_real, z_imag, z_abs, phase])
                    except ValueError:
                        continue
        
        return pd.DataFrame(data, columns=["Frequency", "Z_real", "Z_imag", "Z_abs", "Phase"])
    
    def process_data(self):
        self.data_frames = []
        self.voltage_values = []
        
        for file_path in self.files:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                
                voltage = self.extract_voltage(content)
                if voltage is None:
                    messagebox.showwarning("Warning", f"Could not extract voltage from {os.path.basename(file_path)}")
                    continue
                
                df = self.extract_impedance_data(content)
                if df.empty:
                    messagebox.showwarning("Warning", f"Could not extract impedance data from {os.path.basename(file_path)}")
                    continue
                
                df["Voltage"] = voltage
                df["Filename"] = os.path.basename(file_path)
                
                self.data_frames.append(df)
                self.voltage_values.append(voltage)
            
            except Exception as e:
                messagebox.showerror("Error", f"Error processing {os.path.basename(file_path)}: {str(e)}")
        
        if self.data_frames:
            self.combined_df = pd.concat(self.data_frames, ignore_index=True)
            self.status_label.config(text=f"Processed {len(self.data_frames)} files. Voltages: {sorted(self.voltage_values)}")
            
            # Enable plotting buttons
            self.nyquist_btn.config(state=tk.NORMAL)
            self.mountain_btn.config(state=tk.NORMAL)
            self.heatmap_btn.config(state=tk.NORMAL)
            self.surface_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            
            # Show the Nyquist plot by default
            self.create_nyquist_plot()
        else:
            self.status_label.config(text="No valid data found in selected files")
    
    def create_nyquist_plot(self):
        if not self.data_frames:
            return
        
        # Clear previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Sort data frames by voltage
        sorted_indices = np.argsort(self.voltage_values)
        sorted_data_frames = [self.data_frames[i] for i in sorted_indices]
        sorted_voltages = [self.voltage_values[i] for i in sorted_indices]
        
        # Create colormap
        cmap = cm.get_cmap('viridis', len(sorted_data_frames))
        
        # Plot each dataset with a different color
        for i, (df, voltage) in enumerate(zip(sorted_data_frames, sorted_voltages)):
            ax.plot(df["Z_real"], -df["Z_imag"], 'o-', color=cmap(i), label=f"{voltage:.3f} V", markersize=4)
        
        # Set plot properties
        ax.set_xlabel("Z' / Ω")
        ax.set_ylabel("-Z'' / Ω")
        ax.set_title("Nyquist Plot")
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(sorted_voltages), vmax=max(sorted_voltages)))
        sm.set_array([])
        cbar = self.fig.colorbar(sm, ax=ax)
        cbar.set_label('Voltage (V)')
        
        # Adjust layout and display
        self.fig.tight_layout()
        self.canvas.draw()
    
    def create_mountain_plot(self):
        if not self.data_frames:
            return
        
        # Clear previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Sort data frames by voltage
        sorted_indices = np.argsort(self.voltage_values)
        sorted_data_frames = [self.data_frames[i] for i in sorted_indices]
        sorted_voltages = [self.voltage_values[i] for i in sorted_indices]
        
        # Create colormap
        cmap = cm.get_cmap('viridis', len(sorted_data_frames))
        
        # Plot each dataset with vertical offset
        offset = 0
        offsets = []
        
        for i, (df, voltage) in enumerate(zip(sorted_data_frames, sorted_voltages)):
            # Compute offset based on max -Z_imag value
            offset += max(-df["Z_imag"]) * 0.2 if i > 0 else 0
            offsets.append(offset)
            
            # Plot with color based on voltage but without label
            ax.plot(df["Z_real"], -df["Z_imag"] + offset, 'o-', color=cmap(i), markersize=4)
        
        # Set plot properties
        ax.set_xlabel("Z' / Ω")
        ax.set_ylabel("-Z'' / Ω (offset)")
        ax.set_title("Mountain Plot of EIS Data")
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Add colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(sorted_voltages), vmax=max(sorted_voltages)))
        sm.set_array([])
        cbar = self.fig.colorbar(sm, ax=ax)
        cbar.set_label('Voltage (V)')
        
        # Adjust layout and display
        self.fig.tight_layout()
        self.canvas.draw()
    
    def create_heatmap(self):
        if not self.data_frames:
            return
        
        # Clear previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Sort data frames by voltage
        sorted_indices = np.argsort(self.voltage_values)
        sorted_data_frames = [self.data_frames[i] for i in sorted_indices]
        sorted_voltages = [self.voltage_values[i] for i in sorted_indices]
        
        # Create interpolated grid for Z_real vs Voltage
        z_real_values = set()
        
        for df in self.data_frames:
            z_real_values.update(df["Z_real"].values)
        
        z_real_values = sorted(z_real_values)
        voltage_values = sorted(self.voltage_values)
        
        # Filter z_real values to avoid too many points
        if len(z_real_values) > 100:
            z_real_values = np.linspace(min(z_real_values), max(z_real_values), 100)
            
        # Create a grid of Z_imag values
        grid_data = np.zeros((len(voltage_values), len(z_real_values)))
        
        # Fill the grid with -Z_imag values
        for v_idx, (df, voltage) in enumerate(zip(sorted_data_frames, sorted_voltages)):
            for _, row in df.iterrows():
                try:
                    z_real_idx = np.abs(np.array(z_real_values) - row["Z_real"]).argmin()
                    grid_data[v_idx, z_real_idx] = -row["Z_imag"]
                except:
                    continue
        
        # Create heatmap
        im = ax.pcolormesh(z_real_values, voltage_values, grid_data, shading='auto', cmap='viridis')
        
        # Set plot properties
        ax.set_xlabel("Z' / Ω")
        ax.set_ylabel("Voltage (V)")
        ax.set_title("Heatmap of -Z'' vs Z' and Voltage")
        
        # Add colorbar
        cbar = self.fig.colorbar(im, ax=ax)
        cbar.set_label('-Z" / Ω')
        
        # Adjust layout and display
        self.fig.tight_layout()
        self.canvas.draw()
    
    def create_3d_surface(self):
        if not self.data_frames:
            return
        
        # Clear previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111, projection='3d')
        
        # Sort data frames by voltage
        sorted_indices = np.argsort(self.voltage_values)
        sorted_data_frames = [self.data_frames[i] for i in sorted_indices]
        sorted_voltages = [self.voltage_values[i] for i in sorted_indices]
        
        # Create colormap based on voltage
        cmap = cm.get_cmap('viridis', len(sorted_data_frames))
        
        # Plot each dataset
        for i, (df, voltage) in enumerate(zip(sorted_data_frames, sorted_voltages)):
            # Filter data to avoid too many points
            if len(df) > 50:
                step = len(df) // 50
                filtered_df = df.iloc[::step]
            else:
                filtered_df = df
            
            # For 3D plot, use Z_real as X, Voltage as Y, and -Z_imag as Z
            x = filtered_df["Z_real"].values
            y = np.full(len(filtered_df), voltage)  # Use voltage for Y-axis
            z = -filtered_df["Z_imag"].values
            
            # Use scatter plot for better visualization with larger marker size
            ax.scatter(x, y, z, s=20, c=[cmap(i)]*len(x), depthshade=True)
            
            # Connect points with lines
            ax.plot(x, y, z, '-', color=cmap(i), alpha=0.7, linewidth=1)
        
        # Set plot properties
        ax.set_xlabel("Z' / Ω")
        ax.set_ylabel("Voltage (V)")
        ax.set_zlabel("-Z'' / Ω")
        ax.set_title("3D Surface Plot of EIS Data")
        
        # Add colorbar for voltage
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(sorted_voltages), vmax=max(sorted_voltages)))
        sm.set_array([])
        cbar = self.fig.colorbar(sm, ax=ax)
        cbar.set_label('Voltage (V)')
        
        # Create a view angle similar to the reference image
        ax.view_init(elev=30, azim=-60)
        
        # Adjust layout and display
        self.fig.tight_layout()
        self.canvas.draw()
    
    def save_results(self):
        if self.combined_df is None or not self.output_dir:
            messagebox.showwarning("Warning", "No data to save")
            return
        
        try:
            # Save data to Excel
            excel_path = os.path.join(self.output_dir, "EIS_Data_Analysis.xlsx")
            self.combined_df.to_excel(excel_path, index=False)
            
            # Save current plot
            plot_path = os.path.join(self.output_dir, "EIS_Plot.png")
            self.fig.savefig(plot_path, dpi=300, bbox_inches='tight')
            
            # Save all types of plots
            self.create_nyquist_plot()
            nyquist_path = os.path.join(self.output_dir, "EIS_Nyquist_Plot.png")
            self.fig.savefig(nyquist_path, dpi=300, bbox_inches='tight')
            
            self.create_mountain_plot()
            mountain_path = os.path.join(self.output_dir, "EIS_Mountain_Plot.png")
            self.fig.savefig(mountain_path, dpi=300, bbox_inches='tight')
            
            self.create_heatmap()
            heatmap_path = os.path.join(self.output_dir, "EIS_Heatmap.png")
            self.fig.savefig(heatmap_path, dpi=300, bbox_inches='tight')
            
            self.create_3d_surface()
            surface_path = os.path.join(self.output_dir, "EIS_3D_Surface.png")
            self.fig.savefig(surface_path, dpi=300, bbox_inches='tight')
            
            messagebox.showinfo("Success", f"Results saved to {self.output_dir}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error saving results: {str(e)}")

def main():
    root = tk.Tk()
    app = EISAnalyzer(root)
    root.mainloop()

if __name__ == "__main__":
    main()