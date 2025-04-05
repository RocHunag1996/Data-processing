import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def classify_files(folder_path, log_widget):
    # 创建目标文件夹
    double_dash_folder = os.path.join(folder_path, "double_dash_files")
    single_dash_folder = os.path.join(folder_path, "single_dash_files")
    
    os.makedirs(double_dash_folder, exist_ok=True)
    os.makedirs(single_dash_folder, exist_ok=True)
    
    # 遍历文件夹中的文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # 只处理文件，忽略文件夹
        if os.path.isfile(file_path):
            # 判断文件名中是否包含两个--
            if '--' in filename:
                shutil.move(file_path, os.path.join(double_dash_folder, filename))
                log_msg = f"文件 {filename} 已移动到 double_dash_files 文件夹。\n"
                log_widget.insert(tk.END, log_msg)
            elif '-' in filename:
                shutil.move(file_path, os.path.join(single_dash_folder, filename))
                log_msg = f"文件 {filename} 已移动到 single_dash_files 文件夹。\n"
                log_widget.insert(tk.END, log_msg)

    log_msg = f"\n文件夹 {folder_path} 中的文件已分类完成！\n"
    log_widget.insert(tk.END, log_msg)

def browse_folder(entry):
    """Allow user to select a folder."""
    folder_path = filedialog.askdirectory(title="请选择要处理的文件夹")
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def start_processing(folder_path_entry, root, log_widget):
    """Start the file classification based on the selected folder."""
    folder_path = folder_path_entry.get()
    if not folder_path:
        messagebox.showerror("错误", "请选择一个文件夹。")
        return
    
    # 开始分类
    try:
        classify_files(folder_path, log_widget)
        messagebox.showinfo("完成", f"文件夹 {folder_path} 中的文件已分类完成！")
    except Exception as e:
        messagebox.showerror("错误", f"发生错误：{str(e)}")

def create_main_window():
    # 创建主窗口
    root = tk.Tk()
    root.title("文件分类工具")

    # 文件夹选择部分
    tk.Label(root, text="选择要处理的文件夹:").grid(row=0, column=0, sticky="w")
    folder_path_entry = tk.Entry(root, width=50)
    folder_path_entry.grid(row=0, column=1)

    browse_button = tk.Button(root, text="浏览", command=lambda: browse_folder(folder_path_entry))
    browse_button.grid(row=0, column=2)

    # 日志框
    log_label = tk.Label(root, text="处理日志:")
    log_label.grid(row=1, column=0, sticky="w")
    
    log_widget = tk.Text(root, width=80, height=20, wrap=tk.WORD)
    log_widget.grid(row=2, column=0, columnspan=3)
    log_widget.insert(tk.END, "日志将在此显示...\n")

    # 开始处理按钮
    process_button = tk.Button(root, text="开始分类", 
                               command=lambda: start_processing(folder_path_entry, root, log_widget))
    process_button.grid(row=3, column=0, columnspan=3)

    # 退出按钮
    exit_button = tk.Button(root, text="退出", command=root.quit)
    exit_button.grid(row=4, column=0, columnspan=3)

    root.mainloop()

if __name__ == "__main__":
    create_main_window()
