import sys
import os
import shlex
import tkinter as tk
from tkinter import scrolledtext

class ShellEmulator:
    def __init__(self, root, vfs_root_path, script_path=None):
        self.root = root
        
        # ЭТАП 2: Логирование параметров при запуске
        print("=== ОТЛАДОЧНЫЙ ВЫВОД ПАРАМЕТРОВ ===")
        print(f"Физический путь к VFS: {os.path.abspath(vfs_root_path)}")
        print(f"Путь к стартовому скрипту: {script_path}")
        print("===================================\n")

        # ЭТАП 1 & 3: Заголовок окна содержит имя виртуальной системы
        self.vfs_name = os.path.basename(os.path.normpath(vfs_root_path))
        self.root.title(f"VFS: {self.vfs_name}")
        self.root.geometry("800 axes 500")

        # ЭТАП 3: Загрузка файловой системы в память (In-Memory VFS)
        self.vfs = self._load_vfs(vfs_root_path)
        self.current_path = []  # Список папок от корня, например ['home', 'user']

        # Создание GUI (ЭТАП 1)
        self.text_area = scrolledtext.ScrolledText(root, bg="black", fg="white", insertbackground="white", font=("Courier", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Привязка клавиши Enter к обработчику команд
        self.text_area.bind("<Return>", self._on_enter)
        
        # Отображение приветствия и первого приглашения (Prompt)
        self._insert_prompt()

        # ЭТАП 2: Выполнение стартового скрипта, если он задан
        if script_path and os.path.exists(script_path):
            self._execute_start_script(script_path)

    # ЭТАП 3: Функция считывания папки с диска в память компьютера
    def _load_vfs(self, real_path):
        vfs_node = {"type": "dir", "children": {}, "permissions": "755"}
        if not os.path.exists(real_path):
            return vfs_node
            
        for item in os.listdir(real_path):
            full_path = os.path.join(real_path, item)
            if os.path.isdir(full_path):
                vfs_node["children"][item] = self._load_vfs(full_path)
            else:
                # Читаем содержимое текстовых файлов для команды cat
                content = ""
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except:
                    content = "[Бинарные данные или ошибка чтения]"
                vfs_node["children"][item] = {
                    "type": "file",
                    "content": content,
                    "permissions": "644"
                }
        return vfs_node

    # Получение текущего узла словаря VFS на основе self.current_path
    def _get_current_node(self):
        node = self.vfs
        for p in self.current_path:
            node = node["children"][p]
        return node

    def _insert_prompt(self):
        path_str = "/" + "/".join(self.current_path)
        self.text_area.insert(tk.END, f"user@vfs:{path_str}$ ")
        self.text_area.see(tk.END)
        # Сохраняем позицию, где начинается ввод пользователя
        self.prompt_end_idx = self.text_area.index(tk.INSERT)

    def _on_enter(self, event):
        # Получаем строку, которую ввел пользователь
        input_line = self.text_area.get(self.prompt_end_idx, "end-1c").strip()
        self.text_area.insert(tk.END, "\n")
        
        if input_line:
            self.execute_command(input_line)
            
        self._insert_prompt()
        return "break" # Предотвращаем стандартный перенос строки tkinter

    # ЭТАП 1: Парсер аргументов в кавычках (используем shlex.split)
    def execute_command(self, cmd_line):
        try:
            args = shlex.split(cmd_line)
        except ValueError as e:
            self.text_area.insert(tk.END, f"Ошибка парсинга кавычек: {e}\n")
            return

        if not args:
            return

        cmd = args[0]
        cmd_args = args[1:]

        # ЭТАП 1 & 4 & 5: Маршрутизация команд
        if cmd == "exit":
            self.root.quit()
            sys.exit(0)
        elif cmd == "ls":
            self._cmd_ls(cmd_args)
        elif cmd == "cd":
            self._cmd_cd(cmd_args)
        elif cmd == "clear":
            self._cmd_clear()
        elif cmd == "cat":
            self._cmd_cat(cmd_args)
        elif cmd == "find":
            self._cmd_find(cmd_args)
        elif cmd == "chmod":
            self._cmd_chmod(cmd_args)
        else:
            # ЭТАП 1: Обработка ошибки неизвестной команды
            self.text_area.insert(tk.END, f"sh: {cmd}: command not found\n")

    # ЭТАП 4: Реализация команды ls
    def _cmd_ls(self, args):
        # Проверка флагов или неверных аргументов
        if len(args) > 0 and args[0].startswith("-"):
            self.text_area.insert(tk.END, f"ls: неверный аргумент/флаг '{args[0]}'\n")
            return
            
        node = self._get_current_node()
        items = list(node["children"].keys())
        if items:
            self.text_area.insert(tk.END, "  ".join(items) + "\n")

    # ЭТАП 4: Реализация команды cd
    def _cmd_cd(self, args):
        if not args:
            self.current_path = [] # cd без аргументов возвращает в корень
            return
        
        target = args[0]
        if target == "/":
            self.current_path = []
            return
            
        segments = target.split("/")
        new_path = list(self.current_path)
        
        for seg in segments:
            if not seg or seg == ".":
                continue
            if seg == "..":
                if new_path:
                    new_path.pop()
                continue
            
            # Проверяем, существует ли папка в VFS
            current_node = self.vfs
            possible_path = list(new_path)
            possible_path.append(seg)
            
            exists = True
            for p in possible_path:
                if p in current_node["children"] and current_node["children"][p]["type"] == "dir":
                    current_node = current_node["children"][p]
                else:
                    exists = False
                    break
            
            if exists:
                new_path.append(seg)
            else:
                self.text_area.insert(tk.END, f"cd: no such file or directory: {target}\n")
                return
                
        self.current_path = new_path

    # ЭТАП 4: Реализация команды clear
    def _cmd_clear(self):
        self.text_area.delete("1.0", tk.END)

    # ЭТАП 4: Реализация команды cat
    def _cmd_cat(self, args):
        if not args:
            self.text_area.insert(tk.END, "cat: Пропущен аргумент (имя файла)\n")
            return
        
        node = self._get_current_node()
        filename = args[0]
        
        if filename in node["children"]:
            file_node = node["children"][filename]
            if file_node["type"] == "file":
                self.text_area.insert(tk.END, file_node["content"] + "\n")
            else:
                self.text_area.insert(tk.END, f"cat: {filename}: Is a directory\n")
        else:
            self.text_area.insert(tk.END, f"cat: {filename}: No such file\n")

    # ЭТАП 4: Реализация команды find
    def _cmd_find(self, args):
        def recurse_find(node, current_prefix):
            results = []
            for name, child in node["children"].items():
                path = f"{current_prefix}/{name}" if current_prefix else name
                results.append(path)
                if child["type"] == "dir":
                    results.extend(recurse_find(child, path))
            return results

        current_node = self._get_current_node()
        found_items = recurse_find(current_node, "")
        if found_items:
            self.text_area.insert(tk.END, "\n".join(found_items) + "\n")

    # ЭТАП 5: Реализация команды chmod (изменение прав доступа в памяти)
    def _cmd_chmod(self, args):
        if len(args) < 2:
            self.text_area.insert(tk.END, "chmod: неверные аргументы. Использование: chmod [права] [имя_файла]\n")
            return
            
        mode = args[0]
        filename = args[1]
        node = self._get_current_node()
        
        if filename in node["children"]:
            node["children"][filename]["permissions"] = mode
            self.text_area.insert(tk.END, f"Права доступа для '{filename}' успешно изменены на {mode} (Только в памяти VFS)\n")
        else:
            self.text_area.insert(tk.END, f"chmod: {filename}: No such file or directory\n")

    # ЭТАП 2: Симуляция выполнения стартового скрипта
    def _execute_start_script(self, script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            for line in f:
                cleaned_line = line.strip()
                # Поддержка комментариев Python (#)
                if not cleaned_line or cleaned_line.startswith("#"):
                    continue
                
                # Эмулируем диалог: пишем команду на экран и выполняем
                path_str = "/" + "/".join(self.current_path)
                self.text_area.insert(tk.END, f"user@vfs:{path_str}$ {cleaned_line}\n")
                self.execute_command(cleaned_line)

if __name__ == "__main__":
    # Чтение аргументов командной строки (ЭТАП 2)
    # Пример запуска: python emulator.py ./my_vfs_folder ./start.txt
    if len(sys.argv) < 2:
        print("Ошибка! Укажите путь к папке VFS.")
        print("Пример: python emulator.py <путь_к_vfs> [путь_к_скрипту]")
        sys.exit(1)
        
    vfs_dir = sys.argv[1]
    script = sys.argv[2] if len(sys.argv) > 2 else None
    
    root = tk.Tk()
    app = ShellEmulator(root, vfs_dir, script)
    root.mainloop()
