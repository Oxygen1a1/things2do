import tkinter as tk
from tkinter import messagebox
import datetime
import json
import sys
import os

class Event:
    def __init__(self, name, description, x, y, step_x, step_y, end_date):
        self.name = name
        self.description = description
        self.x = x  # 重要性
        self.y = y  # 紧急性
        self.step_x = step_x  # 重要性变化量
        self.step_y = step_y  # 紧急性变化量
        self.created_at = datetime.datetime.now()
        self.last_update = self.created_at  # 上次更新的位置时间，初始为创建时间
        self.end_date = end_date  # 结束时间
        self.canvas_id = None  # 用于关联 Canvas 上的图形对象

    def update_position(self):
        # 获取当前时间
        now = datetime.datetime.now()
        # 计算距离上次更新的天数差
        delta_days = (now - self.last_update).days
        if delta_days > 0:
            # 更新位置
            self.x += self.step_x * delta_days
            self.y += self.step_y * delta_days
            # 更新 last_update 时间为当前时间
            self.last_update = now

class Things2DoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("things2do v1.0")
        self.events = []

        # 设置窗口初始大小
        self.root.geometry("1000x650")

        # 获取程序所在路径
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            self.application_path = os.path.dirname(sys.executable)
        else:
            self.application_path = os.path.dirname(os.path.abspath(__file__))

        # 主框架
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧框架（Canvas 区域）
        self.canvas_frame = tk.Frame(self.main_frame)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 在 Canvas 上方添加标签
        self.canvas_label = tk.Label(self.canvas_frame, text="任务分布图", font=("Arial", 14))
        self.canvas_label.pack(side=tk.TOP, pady=5)

        # 创建 Canvas
        self.canvas_size = 560  # 保证单元格大小为整数（560 / 28 = 20）
        self.grid_count = 28
        self.cell_size = self.canvas_size / self.grid_count
        self.canvas = tk.Canvas(self.canvas_frame, width=self.canvas_size, height=self.canvas_size, bg='white')
        self.canvas.pack(pady=10)

        # 绘制坐标系
        self.draw_grid()

        # 右侧框架（事件列表区域）
        self.listbox_frame = tk.Frame(self.main_frame)
        self.listbox_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 在 Listbox 上方添加标签
        self.listbox_label = tk.Label(self.listbox_frame, text="任务列表(你应该按顺序做这些事情)", font=("Arial", 14))
        self.listbox_label.pack(side=tk.TOP, pady=5)

        # 创建 Listbox
        self.event_listbox = tk.Listbox(self.listbox_frame, width=50)  # 调整宽度
        self.event_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        self.scrollbar = tk.Scrollbar(self.listbox_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.event_listbox.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.event_listbox.yview)

        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # 加载事件
        self.load_events_from_file()

    def draw_grid(self):
        # 绘制网格和坐标轴
        for i in range(self.grid_count + 1):
            # 垂直线
            x = i * self.cell_size
            self.canvas.create_line(x, 0, x, self.canvas_size, fill="lightgray")
            # 水平线
            y = i * self.cell_size
            self.canvas.create_line(0, y, self.canvas_size, y, fill="lightgray")

        mid = self.grid_count // 2 * self.cell_size

        # 绘制坐标轴
        self.canvas.create_line(mid, self.canvas_size, mid, 0, width=2, arrow=tk.LAST)  # Y 轴，添加箭头
        self.canvas.create_line(0, mid, self.canvas_size, mid, width=2, arrow=tk.LAST)  # X 轴，添加箭头

        # 标注坐标轴
        self.canvas.create_text(self.canvas_size - 50, mid + 20, text="重要性", font=("Arial", 12))
        self.canvas.create_text(mid - 30, 20, text="紧急性", font=("Arial", 12))

        # 标记象限
        self.canvas.create_text(mid * 1.5, mid / 2, text="重要且紧急", font=("Arial", 12))
        self.canvas.create_text(mid * 1.5, mid * 1.5, text="重要但不紧急", font=("Arial", 12))
        self.canvas.create_text(mid / 2, mid / 2, text="不重要但紧急", font=("Arial", 12))
        self.canvas.create_text(mid / 2, mid * 1.5, text="不重要且不紧急", font=("Arial", 12))

    def get_quadrant(self, event):
        """根据事件的位置，确定其象限"""
        mid = self.grid_count / 2
        x = event.x
        y = event.y
        if x >= mid and y <= mid:
            return 1  # 第一象限：重要且紧急
        elif x >= mid and y > mid:
            return 2  # 第二象限：重要但不紧急
        elif x < mid and y <= mid:
            return 3  # 第三象限：不重要但紧急
        else:
            return 4  # 第四象限：不重要且不紧急

    def get_event_priority(self, event):
        """根据事件的位置，确定其优先级，用于排序"""
        quadrant = self.get_quadrant(event)
        importance = event.x  # 重要性
        urgency = self.grid_count - event.y  # 紧急性（因为 y 轴向下）
        # 为了在象限内按照重要性和紧急性降序排列，取负值
        return (quadrant, -importance, -urgency)

    def get_quadrant_name(self, event):
        """获取事件所在的象限名称"""
        quadrant = self.get_quadrant(event)
        if quadrant == 1:
            return "重要且紧急"
        elif quadrant == 2:
            return "重要但不紧急"
        elif quadrant == 3:
            return "不重要但紧急"
        else:
            return "不重要且不紧急"

    def get_grid_position(self, x, y):
        """将像素坐标转换为网格坐标"""
        grid_x = int(x / self.cell_size)
        grid_y = int(y / self.cell_size)
        return grid_x, grid_y

    def on_left_click(self, event):
        x, y = event.x, event.y
        grid_x, grid_y = self.get_grid_position(x, y)
        event_obj = self.get_event_at_position(grid_x, grid_y)
        if event_obj:
            self.show_event_details(event_obj)
        # 如果没有任务，左键点击暂时不做处理

    def on_right_click(self, event):
        # 获取点击的网格坐标
        x, y = event.x, event.y
        grid_x, grid_y = self.get_grid_position(x, y)
        # 弹出菜单
        menu = tk.Menu(self.root, tearoff=0)
        event_obj = self.get_event_at_position(grid_x, grid_y)
        if event_obj:
            menu.add_command(label="修改任务", command=lambda: self.modify_event_dialog(event_obj))
            menu.add_command(label="删除任务", command=lambda: self.delete_event(event_obj))
        else:
            menu.add_command(label="添加任务", command=lambda: self.add_event_dialog(grid_x, grid_y))
        menu.post(event.x_root, event.y_root)

    def get_event_at_position(self, grid_x, grid_y):
        """检查指定位置是否有事件"""
        for event in self.events:
            if int(event.x) == grid_x and int(event.y) == grid_y:
                return event
        return None

    def delete_event(self, event_obj):
        # 删除事件
        if messagebox.askyesno("删除任务", f"确定要删除 '{event_obj.name}' 吗？"):
            self.events.remove(event_obj)
            self.canvas.delete(event_obj.canvas_id)
            self.update_event_listbox()

    def modify_event_dialog(self, event):
        dialog = tk.Toplevel(self.root)
        dialog.title("修改任务")

        tk.Label(dialog, text="任务名称：").grid(row=0, column=0)
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, event.name)
        name_entry.grid(row=0, column=1)

        tk.Label(dialog, text="任务描述：").grid(row=1, column=0)
        desc_entry = tk.Entry(dialog)
        desc_entry.insert(0, event.description)
        desc_entry.grid(row=1, column=1)

        tk.Label(dialog, text="重要性变化（每天）：").grid(row=2, column=0)
        step_x_entry = tk.Entry(dialog)
        step_x_entry.insert(0, str(event.step_x))
        step_x_entry.grid(row=2, column=1)

        tk.Label(dialog, text="紧急性变化（每天）：").grid(row=3, column=0)
        step_y_entry = tk.Entry(dialog)
        step_y_entry.insert(0, str(event.step_y))
        step_y_entry.grid(row=3, column=1)

        tk.Label(dialog, text="任务结束日期（YYYY-MM-DD）：").grid(row=4, column=0)
        end_date_entry = tk.Entry(dialog)
        if event.end_date:
            end_date_entry.insert(0, event.end_date.strftime('%Y-%m-%d'))
        end_date_entry.grid(row=4, column=1)

        def save_changes():
            event.name = name_entry.get()
            event.description = desc_entry.get()
            try:
                event.step_x = float(step_x_entry.get())
            except ValueError:
                event.step_x = 0
            try:
                event.step_y = float(step_y_entry.get())
            except ValueError:
                event.step_y = 0
            end_date_str = end_date_entry.get()
            try:
                event.end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                event.end_date = None
            # 更新事件显示
            self.canvas.delete(event.canvas_id)
            self.draw_event(event)
            self.update_event_listbox()
            dialog.destroy()

        tk.Button(dialog, text="保存", command=save_changes).grid(row=5, column=0, columnspan=2)

    def add_event_dialog(self, grid_x, grid_y):
        dialog = tk.Toplevel(self.root)
        dialog.title("添加任务")

        tk.Label(dialog, text="任务名称：").grid(row=0, column=0)
        name_entry = tk.Entry(dialog)
        name_entry.grid(row=0, column=1)

        tk.Label(dialog, text="任务描述：").grid(row=1, column=0)
        desc_entry = tk.Entry(dialog)
        desc_entry.grid(row=1, column=1)

        tk.Label(dialog, text="重要性变化（每天）：").grid(row=2, column=0)
        step_x_entry = tk.Entry(dialog)
        step_x_entry.insert(0, "0")
        step_x_entry.grid(row=2, column=1)

        tk.Label(dialog, text="紧急性变化（每天）：").grid(row=3, column=0)
        step_y_entry = tk.Entry(dialog)
        step_y_entry.insert(0, "0")
        step_y_entry.grid(row=3, column=1)

        tk.Label(dialog, text="任务结束日期（YYYY-MM-DD）：").grid(row=4, column=0)
        end_date_entry = tk.Entry(dialog)
        end_date_entry.grid(row=4, column=1)

        def save_event():
            name = name_entry.get()
            description = desc_entry.get()
            try:
                step_x = float(step_x_entry.get())
            except ValueError:
                step_x = 0
            try:
                step_y = float(step_y_entry.get())
            except ValueError:
                step_y = 0
            end_date_str = end_date_entry.get()
            try:
                end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
            except ValueError:
                end_date = None

            if name:
                event = Event(name, description, grid_x, grid_y, step_x, step_y, end_date)
                self.events.append(event)
                self.draw_event(event)
                self.update_event_listbox()
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "任务名称不能为空！")

        tk.Button(dialog, text="保存", command=save_event).grid(row=5, column=0, columnspan=2)

    def draw_event(self, event):
        # 在 Canvas 上绘制事件
        x = event.x * self.cell_size + self.cell_size / 2
        y = event.y * self.cell_size + self.cell_size / 2
        r = self.cell_size / 2 - 2  # 减去一点距离，避免超出单元格

        # 根据紧急性设置颜色
        color = self.get_color_by_urgency(event.y)

        id = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color)
        # 保存图形对象的 id，以便后续操作
        event.canvas_id = id
        # 在事件上显示名称
        self.canvas.create_text(x, y, text=event.name[:8], font=("Arial", 8), fill="black")

    def get_color_by_urgency(self, y):
        """根据紧急性返回颜色"""
        urgency_level = int(y)
        max_level = self.grid_count - 1
        # 计算颜色值，从红（紧急）到绿（不紧急）
        red = int(255 * (1 - urgency_level / max_level))
        green = int(255 * (urgency_level / max_level))
        blue = 0
        color = f'#{red:02x}{green:02x}{blue:02x}'
        return color

    def show_event_details(self, event):
        quadrant = self.get_quadrant_name(event)
        message = (
            f"名称：{event.name}\n"
            f"描述：{event.description}\n"
            f"象限：{quadrant}\n"
            f"创建时间：{event.created_at.strftime('%Y-%m-%d')}\n"
            f"结束时间：{event.end_date.strftime('%Y-%m-%d') if event.end_date else '未设置结束时间'}"
        )
        messagebox.showinfo("任务详情", message)

    def update_event_listbox(self):
        # 根据象限和重要性、紧急性排序事件
        self.events.sort(key=lambda e: self.get_event_priority(e))
        # 清空 Listbox
        self.event_listbox.delete(0, tk.END)
        # 重新填充 Listbox
        for event in self.events:
            end_date_str = event.end_date.strftime('%Y-%m-%d') if event.end_date else '无结束日期'
            quadrant_str = self.get_quadrant_name(event)
            self.event_listbox.insert(tk.END, f"{event.name} ({quadrant_str}) - {end_date_str}")

    def update_events(self):
        # 更新所有事件的位置
        for event in self.events:
            event.update_position()
            # 限制坐标范围
            event.x = min(max(event.x, 0), self.grid_count - 1)
            event.y = min(max(event.y, 0), self.grid_count - 1)
            # 更新 Canvas 上的图形位置
            self.canvas.delete(event.canvas_id)
            self.draw_event(event)
        # 更新 Listbox
        self.update_event_listbox()
        # 设定下一次更新的时间
        self.root.after(86400000, self.update_events)  # 每天更新一次（单位：毫秒）

    def save_events_to_file(self):
        data = []
        for event in self.events:
            data.append({
                'name': event.name,
                'description': event.description,
                'x': event.x,
                'y': event.y,
                'step_x': event.step_x,
                'step_y': event.step_y,
                'created_at': event.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'last_update': event.last_update.strftime('%Y-%m-%d %H:%M:%S'),
                'end_date': event.end_date.strftime('%Y-%m-%d') if event.end_date else None
            })
        data_file = os.path.join(self.application_path, 'events.json')
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_events_from_file(self):
        try:
            data_file = os.path.join(self.application_path, 'events.json')
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    event = Event(
                        name=item['name'],
                        description=item['description'],
                        x=item['x'],
                        y=item['y'],
                        step_x=item['step_x'],
                        step_y=item['step_y'],
                        end_date=datetime.datetime.strptime(item['end_date'], '%Y-%m-%d') if item['end_date'] else None
                    )
                    event.created_at = datetime.datetime.strptime(item['created_at'], '%Y-%m-%d %H:%M:%S')
                    event.last_update = datetime.datetime.strptime(item['last_update'], '%Y-%m-%d %H:%M:%S')
                    self.events.append(event)
                    self.draw_event(event)
                self.update_event_listbox()
        except FileNotFoundError:
            pass

    def run(self):
        # 开始事件更新循环
        self.update_events()
        # 捕获关闭事件，保存数据
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.save_events_to_file()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Things2DoApp(root)
    app.run()