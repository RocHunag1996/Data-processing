import tkinter as tk
from tkinter import messagebox
import subprocess
import os

# Function to run process_charge_discharge.py
def run_process_charge_discharge(log_widget):
    try:
        # Adjust the path to the script based on your local setup
        script_path = r"E:\Matlab\DRTtools-master\import file samples\process_charge_discharge.py"
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        log_widget.insert(tk.END, result.stdout)
        log_widget.insert(tk.END, result.stderr)
        log_widget.insert(tk.END, "Process completed for charge discharge files.\n")
    except Exception as e:
        log_widget.insert(tk.END, f"Error: {str(e)}\n")

# Function to run process_eis_files.py
def run_process_eis_files(log_widget):
    try:
        # Adjust the path to the script based on your local setup
        script_path = r"E:\Matlab\DRTtools-master\import file samples\process_eis_files.py"
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        log_widget.insert(tk.END, result.stdout)
        log_widget.insert(tk.END, result.stderr)
        log_widget.insert(tk.END, "Process completed for EIS files.\n")
    except Exception as e:
        log_widget.insert(tk.END, f"Error: {str(e)}\n")

# Function to run voltage_visualizer.py
def run_voltage_visualizer(log_widget):
    try:
        # Adjust the path to the script based on your local setup
        script_path = r"E:\Matlab\DRTtools-master\import file samples\voltage_visualizer.py"
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        log_widget.insert(tk.END, result.stdout)
        log_widget.insert(tk.END, result.stderr)
        log_widget.insert(tk.END, "Process completed for voltage visualizer.\n")
    except Exception as e:
        log_widget.insert(tk.END, f"Error: {str(e)}\n")

# Function to create the main GUI window
def create_main_window():
    # Create main window
    root = tk.Tk()
    root.title("Main GUI for Scripts")

    # Create the log display (text widget)
    log_label = tk.Label(root, text="Processing Log:")
    log_label.grid(row=0, column=0, sticky="w")

    log_widget = tk.Text(root, width=80, height=20, wrap=tk.WORD)
    log_widget.grid(row=1, column=0, columnspan=3)
    log_widget.insert(tk.END, "Logs will appear here...\n")

    # Button to run process_charge_discharge.py
    process_charge_button = tk.Button(root, text="Run Charge Discharge Processing",
                                      command=lambda: run_process_charge_discharge(log_widget))
    process_charge_button.grid(row=2, column=0, pady=10)

    # Button to run process_eis_files.py
    process_eis_button = tk.Button(root, text="Run EIS Processing",
                                   command=lambda: run_process_eis_files(log_widget))
    process_eis_button.grid(row=2, column=1, pady=10)

    # Button to run voltage_visualizer.py
    voltage_visualizer_button = tk.Button(root, text="Run Voltage Visualizer",
                                          command=lambda: run_voltage_visualizer(log_widget))
    voltage_visualizer_button.grid(row=2, column=2, pady=10)

    # Exit button
    exit_button = tk.Button(root, text="Exit", command=root.quit)
    exit_button.grid(row=3, column=0, columnspan=3)

    root.mainloop()

# Run the main window function
if __name__ == "__main__":
    create_main_window()
