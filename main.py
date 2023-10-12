import os
import dotenv
import random
import pathlib
import functools
import threading
import tkinter as tk
import moviepy.editor as mp
from PIL import Image, ImageTk
from typing import List
from tkinter import ttk, messagebox

dotenv.load_dotenv(".env")


def crop_center(image: Image.Image):
    image_width, image_height = image.size
    length = min(image_width, image_height)
    left = (image_width - length) // 2
    top = (image_height - length) // 2
    right = (image_width + length) // 2
    bottom = (image_height + length) // 2
    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image


def populate_treeview(tree: ttk.Treeview, parent, directory, is_root=False):
    if is_root:
        item_text = directory
    else:
        item_text = os.path.basename(directory)
    item_id = tree.insert(parent, "end", text=item_text, open=is_root, values=[str(directory)])
    for item in sorted(os.listdir(directory)):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            populate_treeview(tree, item_id, item_path)


def count_images(folder_path):
    return len(list(pathlib.Path(folder_path).rglob("*.[jJpPgG]*[gGfF]")))


def count_videos(folder_path):
    return len(list(pathlib.Path(folder_path).rglob("*.[aAmM]*[iIvV4]")))


# def stop_process():
#     # 設置停止標誌為 True
#     global stop_flag
#     stop_flag = True


# def execute_func(func, result, progressbar, stop_flag, *args, **kwargs):
#     result[0] = func(progressbar, stop_flag, *args, **kwargs)


def wait_window_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 創建「請稍等」視窗
        wait_window = tk.Toplevel(window)
        wait_window.title("請稍等")
        wait_window_width  = 250
        wait_window_height = 50
        wait_window.geometry(f"{wait_window_width}x{wait_window_height}")
        # 創建進度條
        progressbar = ttk.Progressbar(wait_window, mode="determinate", maximum=100)
        progressbar.pack(pady=10)
        # # 創建停止按鈕
        # stop_button = tk.Button(wait_window, text="停止", command=stop_process)
        # stop_button.pack()
        # # 設置停止標誌的初始狀態
        # stop_flag = False
        # 計算提示視窗的位置
        window_x      = left_frame.winfo_rootx()
        window_y      = left_frame.winfo_rooty()
        window_width  = left_frame.winfo_width()
        window_height = left_frame.winfo_height()
        x = window_x + (window_width  - wait_window_width)  // 2
        y = window_y + (window_height - wait_window_height) // 2
        wait_window.geometry(f"+{x}+{y}")
        wait_window.update()
        # 聚焦於 wait_window
        wait_window.focus_force()
        wait_window.grab_set()
        # 執行被裝飾的函式
        output = func(progressbar, *args, **kwargs)
        # output = func(progressbar, stop_flag, *args, **kwargs)
        # 關閉「請稍等」視窗
        wait_window.destroy()
        return output
    return wrapper


@wait_window_decorator
def load_images(progressbar, folder_path, num_images):
# def load_images(progressbar, stop_flag, folder_path, num_images):
    images = []
    file_paths = list(pathlib.Path(folder_path).rglob("*.[jJpPgG]*[gGfF]"))
    random.shuffle(file_paths)
    if len(file_paths) > 0:
        def load_image(file_path):
            image = Image.open(file_path)
            image = crop_center(image)
            image = image.resize((250, 250))
            images.append(image)
        threads: List[threading.Thread] = []
        for file_path in file_paths[:num_images]:
            thread = threading.Thread(target=load_image, args=(file_path,))
            thread.start()
            threads.append(thread)
        # 等待所有執行緒完成
        while True:
            # if stop_flag: break
            done_threads_num = [ not th.is_alive() for th in threads ].count(True)
            progressbar["value"] = 100 * done_threads_num / len(threads)
            window.update_idletasks()
            if done_threads_num == len(threads): break
    return images


def capture_random_frame(video_path):
    # 隨機選取影片的時間位置
    video = mp.VideoFileClip(video_path)
    duration = video.duration
    random_time = random.uniform(0, duration)
    # 從隨機時間位置截取一幀影像
    frame = video.get_frame(random_time)
    video.close()
    # 回傳影像
    return Image.fromarray(frame)


@wait_window_decorator
def load_videos(progressbar, folder_path, num_images):
# def load_videos(progressbar, stop_flag, folder_path, num_images):
    images = []
    file_paths = list(pathlib.Path(folder_path).rglob("*.[aAmM]*[iIvV4]"))
    if len(file_paths) > 0:
        def capture_and_append_image(file_path):
            image = capture_random_frame(str(file_path))
            image = crop_center(image)
            image = image.resize((250, 250))
            images.append(image)
        threads: List[threading.Thread] = []
        for _ in range(num_images):
            random.shuffle(file_paths)
            thread = threading.Thread(target=capture_and_append_image, args=(file_paths[0],))
            thread.start()
            threads.append(thread)
        # 等待所有執行緒完成
        while True:
            # if stop_flag: break
            done_threads_num = [ not th.is_alive() for th in threads ].count(True)
            progressbar["value"] = 100 * done_threads_num / len(threads)
            window.update_idletasks()
            if done_threads_num == len(threads): break
    return images


def create_collage(images: List[Image.Image], collage_width, collage_height):
    collage = Image.new("RGB", (collage_width, collage_height))
    x_offset = 0
    y_offset = 0
    for image in images:
        collage.paste(image, (x_offset, y_offset))
        x_offset += image.width
        if x_offset >= collage_width:
            x_offset = 0
            y_offset += image.height
    return collage


def on_treeview_doubleclick(event):
    item_id = tree.focus()
    current_state = tree.item(item_id, "open")
    tree.item(item_id, open=not current_state)


def on_treeview_select(event):
    selected_item = tree.focus()
    item_text = tree.item(selected_item, "text")
    selected_folder_entry.delete(0, tk.END)
    selected_folder_entry.insert(tk.END, item_text)
    item_path = tree.item(selected_item, "values")[0]
    num_image, num_video = count_images(item_path), count_videos(item_path)
    info_text = []
    if num_image: info_text.append(f"{num_image}P")
    if num_video: info_text.append(f"{num_video}V")
    info_text = f"({'+'.join(info_text)})"
    selected_folder_info_entry.delete(0, tk.END)
    selected_folder_info_entry.insert(tk.END, info_text)
    # show_collage()


def show_collage(target):
    assert target in [ "images", "videos" ]
    item_path = tree.item(tree.focus(), "values")[0]
    if not os.path.isabs(item_path):
        item_path = os.path.abspath(item_path)
    num_images = (lower_frame.winfo_width() // 250) * (lower_frame.winfo_height() // 250)
    if   target == "images": images = load_images(item_path, num_images)
    elif target == "videos": images = load_videos(item_path, num_images)
    collage_width  = (lower_frame.winfo_width()  // 250) *250
    collage_height = (lower_frame.winfo_height() // 250) *250
    collage = create_collage(images, collage_width, collage_height)
    # 調整拼貼圖像的大小
    collage = collage.resize((collage_width, collage_height))
    image = ImageTk.PhotoImage(collage)
    image_label.configure(image=image)
    image_label.image = image


def show_images_collage():
    show_collage("images")


def show_videos_collage():
    show_collage("videos")


def append_folder_postfix():
    name = selected_folder_entry.get()
    name_postfix = selected_folder_info_entry.get()
    if name[-len(name_postfix):] == name_postfix:
        return
    selected_folder_entry.insert(tk.END, ' '+name_postfix)


def rename_folder():
    name = selected_folder_entry.get()
    item_id = tree.focus()
    item_text = tree.item(item_id, "text")
    if item_text == name:
        return
    old_path = tree.item(item_id, "values")[0]
    new_path = os.path.join(os.path.dirname(old_path), name)
    os.rename(old_path, new_path)
    tree.item(item_id, text=name, values=[str(new_path)])
    item_children_ids = tree.get_children(item_id)
    for item_child_id in item_children_ids:
        item_child_path = tree.item(item_child_id, "values")[0]
        item_child_path = item_child_path.replace(old_path, new_path)
        tree.item(item_child_id, values=[str(item_child_path)])


def set_hidden_recursive(folder_path=None):
    if folder_path is None:
        folder_path = tree.item(tree.focus(), "values")[0]
    # 設定資料夾屬性為隱藏
    os.system(f'attrib +h "{folder_path}"')
    # 遞迴處理資料夾中的所有內容物
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            set_hidden_recursive(item_path)
        else:
            os.system(f'attrib +h "{item_path}"')


def unset_hidden_recursive(folder_path=None):
    if folder_path is None:
        folder_path = tree.item(tree.focus(), "values")[0]
    # 設定資料夾屬性為隱藏
    os.system(f'attrib -h "{folder_path}"')
    # 遞迴處理資料夾中的所有內容物
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            unset_hidden_recursive(item_path)
        else:
            os.system(f'attrib -h "{item_path}"')


def reformat_files():
    result = messagebox.askyesno("確認", "您確定要格式化檔案名稱嗎？")
    if result:
        folder_path = tree.item(tree.focus(), "values")[0]
        file_paths = sorted(list(pathlib.Path(folder_path).glob("*[jJpPgG]*[gGfF]")))
        for file_id, file_path in enumerate(file_paths):
            new_filename = f"temp_{file_id+1}." + str(os.path.basename(file_path)).split('.')[-1].lower()
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            os.rename(file_path, new_filepath)
        file_paths = sorted(list(pathlib.Path(folder_path).glob("*.[jJpPgG]*[gGfF]")))
        for file_id, file_path in enumerate(file_paths):
            new_filename = f"P ({file_id+1:03})." + str(os.path.basename(file_path)).split('.')[-1].lower()
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            os.rename(file_path, new_filepath)
        file_paths = sorted(list(pathlib.Path(folder_path).glob("*.[aAmM]*[iIvV4]")))
        for file_id, file_path in enumerate(file_paths):
            new_filename = f"temp_{file_id+1}." + str(os.path.basename(file_path)).split('.')[-1].lower()
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            os.rename(file_path, new_filepath)
        file_paths = sorted(list(pathlib.Path(folder_path).glob("*.[aAmM]*[iIvV4]")))
        for file_id, file_path in enumerate(file_paths):
            new_filename = f"V ({file_id+1:03})." + str(os.path.basename(file_path)).split('.')[-1].lower()
            new_filepath = os.path.join(os.path.dirname(file_path), new_filename)
            os.rename(file_path, new_filepath)


# 創建主視窗
window = tk.Tk()
window.title("影音管理工具")
window.geometry("1400x900")

# 創建 PanedWindow 控件
paned_window = ttk.PanedWindow(window, orient=tk.HORIZONTAL)
paned_window.pack(fill=tk.BOTH, expand=True)

# 創建左方 Frame 控件
left_frame = tk.Frame(paned_window)
paned_window.add(left_frame, weight=8)

# 創建右方 Frame 控件
right_frame = tk.Frame(paned_window)
paned_window.add(right_frame, weight=2)

# 創建 Treeview 控件
tree = ttk.Treeview(right_frame)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 創建 Scrollbar 控件
scrollbar = tk.Scrollbar(right_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 設定 Scrollbar 與 Treeview 的關聯
scrollbar.config(command=tree.yview)
tree.config(yscrollcommand=scrollbar.set)

# 綁定事件，當右鍵雙擊樹狀列表時觸發展開/收起功能
tree.bind("<Button-2>", on_treeview_doubleclick)
# 綁定事件，當選中樹狀列表項目時觸發顯示選中資料夾名稱
tree.bind("<<TreeviewSelect>>", on_treeview_select)

# 創建上方 Frame 控件
upper_frame = tk.Frame(left_frame)
upper_frame.pack(fill=tk.BOTH, pady=20)

# 創建 Entry 控件，用於顯示選中的資料夾名稱
selected_folder_entry = tk.Entry(upper_frame, width=80)
selected_folder_entry.pack()

# 創建 Label 控件，用於顯示選中的資料夾的資訊
selected_folder_info_entry = tk.Entry(upper_frame)
selected_folder_info_entry.pack(pady=0)

# 創建 Frame 控件，用於放置按鈕
buttons_frame = tk.Frame(upper_frame)
buttons_frame.pack(pady=10)

# 創建 Button 控件，用於顯示圖片拼貼
show_images_collage_button = tk.Button(buttons_frame, text="顯示圖片", command=show_images_collage)
show_images_collage_button.pack(side=tk.LEFT)

# 創建 Button 控件，用於顯示圖片拼貼
show_videos_collage_button = tk.Button(buttons_frame, text="顯示影片截圖", command=show_videos_collage)
show_videos_collage_button.pack(side=tk.LEFT, padx=10)

# 創建 Button 控件，用於附上資訊後綴
rename_button = tk.Button(buttons_frame, text="附上資訊後綴", command=append_folder_postfix)
rename_button.pack(side=tk.LEFT)

# 創建 Button 控件，用於修改資料夾名稱
rename_button = tk.Button(buttons_frame, text="修改資料夾名稱", command=rename_folder)
rename_button.pack(side=tk.LEFT, padx=10)

# 創建 Button 控件，用於隱藏資料夾
reformat_button = tk.Button(buttons_frame, text="隱藏資料夾", command=set_hidden_recursive)
reformat_button.pack(side=tk.LEFT)

# 創建 Button 控件，用於取消隱藏資料夾
reformat_button = tk.Button(buttons_frame, text="取消隱藏資料夾", command=unset_hidden_recursive)
reformat_button.pack(side=tk.LEFT, padx=10)

# 創建 Button 控件，用於格式化檔案名稱
reformat_button = tk.Button(buttons_frame, text="格式化檔案名稱", command=reformat_files)
reformat_button.pack(side=tk.LEFT)

# 創建下方 Frame 控件，用於顯示圖像
lower_frame = tk.Frame(left_frame)
lower_frame.pack(fill=tk.BOTH, expand=True)

# 創建 Label 控件，用於顯示圖片
image_label = tk.Label(lower_frame)
image_label.pack()

# 指定要顯示的根目錄
root_directory = os.getenv("ROOT_DIRECTORY")

# 呼叫函式以填充樹狀列表，並指定根目錄為開啟狀態
populate_treeview(tree, "", root_directory, is_root=True)

# 啟動主迴圈
window.mainloop()