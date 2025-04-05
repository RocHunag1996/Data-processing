import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np

def process_eis_files(folder_path, output_folder, log_widget):
    # Process each file in the folder
    processed_count = 0
    log_file = open("eis_processing_log.txt", "w")  # Open log file for writing

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        # Skip directories and non-text files
        if os.path.isdir(file_path) or not (filename.endswith('.txt') or filename.endswith('.bin')):
            continue
            
        try:
            # Read the file content
            with open(file_path, 'r') as file:
                content = file.readlines()
                
            # Extract Init E value for renaming
            init_e_value = None
            for line in content:
                if "Init E (V) =" in line:
                    match = re.search(r'Init E \(V\) = ([-+]?\d*\.\d+|\d+)', line)
                    if match:
                        init_e_value = match.group(1)
                    break
            
            if not init_e_value:
                log_msg = f"Could not find Init E value in {filename}, skipping...\n"
                log_widget.insert(tk.END, log_msg)
                log_file.write(log_msg)
                continue
                
            # Find where data begins (typically after headers)
            data_lines = []
            
            # For EIS-1--1.txt format
            if "Freq/Hz, Z'/ohm, Z\"/ohm" in ''.join(content):
                for line in content:
                    # Skip empty lines
                    if line.strip() == "":
                        continue
                    
                    # Check if this line contains numeric data
                    parts = line.strip().split(',')
                    if len(parts) >= 3 and is_numeric(parts[0].strip()):
                        freq = float(parts[0].strip())
                        z_real = float(parts[1].strip())
                        z_imag = float(parts[2].strip())
                        data_lines.append(f"{freq:15.6f} {z_real:15.6f} {z_imag:15.6f}\n")
            
            # For demo.txt format which is already close to desired format
            else:
                for line in content:
                    # Skip empty lines
                    if line.strip() == "":
                        continue
                    
                    # Check if this line looks like data (3 space-separated numbers)
                    parts = line.strip().split()
                    if len(parts) >= 3 and all(is_numeric(part) for part in parts[:3]):
                        freq = float(parts[0])
                        z_real = float(parts[1])
                        z_imag = float(parts[2])
                        data_lines.append(f"{freq:15.6f} {z_real:15.6f} {z_imag:15.6f}\n")
            
            if not data_lines:
                log_msg = f"No valid data found in {filename}, skipping...\n"
                log_widget.insert(tk.END, log_msg)
                log_file.write(log_msg)
                continue
                
            # Create output filename based on Init E value
            output_filename = f"{init_e_value}.txt"
            output_path = os.path.join(output_folder, output_filename)
            
            # Write processed data to new file
            with open(output_path, 'w') as outfile:
                outfile.writelines(data_lines)
                
            processed_count += 1
            log_msg = f"Processed: {filename} → {output_filename}\n"
            log_widget.insert(tk.END, log_msg)
            log_file.write(log_msg)
            
        except Exception as e:
            log_msg = f"Error processing {filename}: {str(e)}\n"
            log_widget.insert(tk.END, log_msg)
            log_file.write(log_msg)
    
    log_msg = f"\nProcessing complete! {processed_count} files processed.\nProcessed files saved to: {output_folder}\n"
    log_widget.insert(tk.END, log_msg)
    log_file.write(log_msg)
    log_file.close()

    return processed_count

def is_numeric(value):
    """Check if a string can be converted to a float."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def browse_folder(entry):
    """Allow user to select a folder."""
    folder_path = filedialog.askdirectory(title="Select folder containing EIS files")
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def start_processing(folder_path_entry, root, log_widget):
    """Start the file processing based on the selected folder."""
    folder_path = folder_path_entry.get()
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder.")
        return
    
    output_folder = os.path.join(folder_path, "processed_data")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Start processing
    try:
        processed_count = process_eis_files(folder_path, output_folder, log_widget)
        messagebox.showinfo("Processing Complete", f"{processed_count} files processed successfully.\nProcessed files saved to: {output_folder}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def create_main_window():
    # Create main window
    root = tk.Tk()
    root.title("EIS File Processing")

    # Folder selection
    tk.Label(root, text="Select folder containing EIS files:").grid(row=0, column=0, sticky="w")
    folder_path_entry = tk.Entry(root, width=50)
    folder_path_entry.grid(row=0, column=1)

    browse_button = tk.Button(root, text="Browse", command=lambda: browse_folder(folder_path_entry))
    browse_button.grid(row=0, column=2)

    # Log display (text widget)
    log_label = tk.Label(root, text="Processing Log:")
    log_label.grid(row=1, column=0, sticky="w")
    
    log_widget = tk.Text(root, width=80, height=20, wrap=tk.WORD)
    log_widget.grid(row=2, column=0, columnspan=3)
    log_widget.insert(tk.END, "Logs will appear here...\n")

    # Start processing button
    process_button = tk.Button(root, text="Start Processing", 
                               command=lambda: start_processing(folder_path_entry, root, log_widget))
    process_button.grid(row=3, column=0, columnspan=3)

    root.mainloop()

if __name__ == "__main__":
    create_main_window()
