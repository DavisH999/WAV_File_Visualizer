import struct
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from pathlib import Path


def read_specific_bytes(file, startIndex, num_bytes):
    file.seek(startIndex)
    data = file.read(num_bytes)
    return data


def find_data_chunk(file):
    while True:
        chunk_id = file.read(4)
        if chunk_id == b'data':
            # return the initial position of the data chunk
            return file.tell() - 4
        chunk_size = struct.unpack('<I', file.read(4))[0]
        # skip the whole non-data chunk
        file.seek(chunk_size, 1)


def draw_lines(canvas, amplitude_list):
    canvas.delete("all")
    half_canvas_height = canvas.winfo_height() // 2
    canvas_width = canvas.winfo_width()

    canvas.create_line(0, half_canvas_height, canvas_width, half_canvas_height, fill='#42F796')

    # compute scales
    factor_y = half_canvas_height / max(amplitude_list)
    factor_x = canvas_width / len(amplitude_list)

    for i in range(len(amplitude_list)):
        scaled_y = amplitude_list[i] * factor_y
        scaled_x = i * factor_x
        canvas.create_line(scaled_x, half_canvas_height, scaled_x, half_canvas_height - scaled_y, fill='#42F796')


def initialize_main_window():
    # initialize the main window
    global main_window
    main_window = tk.Tk()
    main_window.title("Wav File Reader")
    main_window.state('zoomed')
    main_menu = tk.Menu(main_window)
    main_window.config(menu=main_menu)
    file_menu = tk.Menu(main_menu, tearoff=0)
    main_menu.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label='Open a WAV File', command=open_WAV_file)

    # initialize the three-framework
    # text label
    topmost_frame = tk.Frame(main_window, bg='lightpink')
    topmost_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    label_para = tk.Label(topmost_frame, text="WAV Basic Parameters", bg='lightgrey')
    label_para.pack(fill=tk.BOTH, expand=True)
    global file_name_var
    file_name_var = tk.StringVar()
    file_name_var.set("File Name: ")
    label_filename = tk.Label(topmost_frame, textvariable=file_name_var, bg='lightgrey')
    label_filename.pack(fill=tk.BOTH, expand=True)
    global num_samples_var
    num_samples_var = tk.StringVar()
    num_samples_var.set("Total Number of Samples: ")
    label_num_samples = tk.Label(topmost_frame, textvariable=num_samples_var, bg='lightgrey')
    label_num_samples.pack(fill=tk.BOTH, expand=True)
    global sampling_freq_var
    sampling_freq_var = tk.StringVar()
    sampling_freq_var.set("Sampling Frequency: ")
    label_sampling_freq = tk.Label(topmost_frame, textvariable=sampling_freq_var, bg='lightgrey')
    label_sampling_freq.pack(fill=tk.BOTH, expand=True)
    # canvas about left channel
    top_frame = tk.Frame(main_window)
    top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    global top_canvas
    top_canvas = tk.Canvas(top_frame, bg='black')
    top_canvas.pack(fill=tk.BOTH, expand=True)
    # canvas about right channel
    bottom_frame = tk.Frame(main_window)
    bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    global bottom_canvas
    bottom_canvas = tk.Canvas(bottom_frame, bg='black')
    bottom_canvas.pack(fill=tk.BOTH, expand=True)

    # mainloop
    tk.mainloop()


def open_WAV_file():
    selected_file_path = tk.filedialog.askopenfilename(title='Select a WAV File',
                                                       filetypes=(('All files', '*.*'),)
                                                       )
    try:
        with open(selected_file_path, 'rb') as file:
            # check if it is WAV format
            if ((read_specific_bytes(file, 8, 4) != b'WAVE') or
                    (read_specific_bytes(file, 0, 4) != b'RIFF')):
                tk.messagebox.showinfo('Error', 'The selected file is not a WAV format, please select a WAV')
                return

            # extract needed info
            sampling_freq_bytes = read_specific_bytes(file, 24, 4)
            sampling_freq_uint = struct.unpack('<I', sampling_freq_bytes)[0]
            block_align_bytes = read_specific_bytes(file, 32, 2)
            block_align_ushort = struct.unpack('<H', block_align_bytes)[0]
            bits_per_sample_bytes = read_specific_bytes(file, 34, 2)
            bits_per_sample_ushort = struct.unpack('<H', bits_per_sample_bytes)[0]
            bytes_per_sample_ushort = bits_per_sample_ushort // 8
            # Find the data chunk
            data_chunk_initial_position = find_data_chunk(file)
            sub_chunk2_size_bytes = read_specific_bytes(file, data_chunk_initial_position + 4, 4)
            sub_chunk2_size_uint = struct.unpack('<I', sub_chunk2_size_bytes)[0]
            # compute num of samples
            num_samples = sub_chunk2_size_uint // block_align_ushort
            global num_samples_var, sampling_freq_var, file_name_var
            num_samples_var.set(f"Total Number of Samples: {num_samples}")
            sampling_freq_var.set(f"Sampling Frequency: {sampling_freq_uint}")
            file_name_var.set(f"File Name: {Path(selected_file_path).name}")

            # collect amplitude data
            left_amplitude_list, right_amplitude_list = [], []
            file.seek(data_chunk_initial_position + 8)  # Move to the beginning of the data chunk
            for i in range(int(num_samples)):
                bytes_left = file.read(int(bytes_per_sample_ushort))
                left_amp = struct.unpack('<h', bytes_left)[0]  # ASSUME signed 16-bits per sample
                left_amplitude_list.append(left_amp)
                bytes_right = file.read(int(bytes_per_sample_ushort))
                right_amp = struct.unpack('<h', bytes_right)[0]  # ASSUME signed 16-bits per sample
                right_amplitude_list.append(right_amp)

            # draw the graphs
            global main_window, top_canvas, bottom_canvas
            main_window.after(200, lambda: draw_lines(top_canvas, left_amplitude_list))
            main_window.after(200, lambda: draw_lines(bottom_canvas, right_amplitude_list))

            return

    except Exception as e:
        messagebox.showinfo('Error', f'An error occurred: {e}')


def main():
    initialize_main_window()


if __name__ == '__main__':
    main()
