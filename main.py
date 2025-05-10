import json
import tkinter as tk
from tkinter import simpledialog, ttk, scrolledtext, messagebox
import threading
import time
import random

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from faker import Faker

import logging
from datetime import datetime
from PIL import Image, ImageTk

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='lurebuster.log'
)


class LureBuster:
    def __init__(self, root):
        self.root = root
        self.root.title("LureBuster - Phishing Site Disruptor")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.maxsize(1000, 700)

        self.set_theme()

        self.target_url = tk.StringVar()
        self.request_count = tk.IntVar(value=100)
        self.threads_count = tk.IntVar(value=5)
        self.delay = tk.DoubleVar(value=0.5)
        self.running = False
        self.stats = {
                "requests_sent"      : 0,
                "successful_requests": 0,
                "failed_requests"    : 0,
                "start_time"         : None,
                "end_time"           : None
        }

        self.password_compexities = {
                'Low'    : 6,
                'Medium' : 12,
                'High'   : 18,
                'Higher' : 24,
                'Extreme': 30,
                'Random' : random.randint(6, 30)
        }
        self.faker = Faker()
        self.regions = ["US", "UK", "CA", "AU", "DE", "FR", "JP", "BR", "IN"]
        self.methods = ["GET", "POST", "PATCH", "PUT", "DELETE"]
        self.current_region = tk.StringVar(value="US")
        self.current_method = "POST"
        self.request_threads = []

        self.example_template = {
                "name"       : "Example Template",
                "headers"    : {
                        "User-Agent"     : "{{user_agent}}",
                        "Content-Type"   : "application/x-www-form-urlencoded",
                        "Accept"         : "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                           "image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5"
                },
                "form_fields": {
                        "username": "{{email}}",
                        "password": "{{password}}",
                        "remember": "true"
                }
        }

        # Possible Generators https://faker.readthedocs.io/en/stable/providers.html
        base = ["{{digit}}", "{{int}}", "{{letter}}", "{{letters}}"]
        address = ["{{address}}", "{{city}}", "{{city_suffix}}", "{{country}}", "{{country_code}}", "{{postcode}}",
                   "{{street_name}}", "{{street_suffix}}"]
        bank = ["{{aba}}", "{{bban}}", "{{iban}}", "{{swift11}}", "{{swift8}}"]
        barcode = ["{{ean13}}", "{{ean8}}"]
        company = ["{{bs}}", "{{catch_phrase}}", "{{company}}", "{{company_suffix}}"]
        credit_card = ["{{credit_card_expire}}", "{{credit_card_number}}", "{{credit_card_provider}}",
                       "{{credit_card_security_code}}"]
        currency = ["{{cryptocurrency}}", "{{cryptocurrency_code}}", "{{currency}}", "{{currency_code}}",
                    "{{currency_name}}", "{{currency_symbol}}", "{{pricetag}}"]
        ...
        self.generators = ['{{email}}', '{{password}}', '{{full_name}}', "{{first_name}}", "{{last_name}}",
                           "{{}}", "{{social_security_number}}, {{birth_date}}, {{license_plate}}"]

        self.create_ui()

    def set_theme(self):
        style = ttk.Style()
        style.theme_use('clam')

        self.bg_color = "#ffffff"
        self.fg_color = "#000000"
        self.accent_color = "#5e768d"
        self.success_color = "#a6e3a1"
        self.warning_color = "#f44336"

        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton',
                        background=self.accent_color,
                        foreground='white',
                        font=('Helvetica', 10, 'bold'),
                        padding=5)
        style.map('TButton',
                  background=[('active', self.bg_color)],
                  foreground=[('active', self.fg_color)], )
        style.configure('TEntry',
                        fieldbackground=self.bg_color,
                        foreground=self.fg_color,
                        insertcolor=self.fg_color)
        style.configure('TSpinbox',
                        fieldbackground=self.bg_color,
                        foreground=self.fg_color)
        style.configure('Horizontal.TProgressbar',
                        background=self.accent_color,
                        troughcolor=self.bg_color)
        style.configure('TNotebook', background=self.bg_color)
        style.configure('TNotebook.Tab',
                        background=self.bg_color,
                        foreground=self.fg_color,
                        padding=[10, 5])
        style.map('TNotebook.Tab',
                  background=[('selected', self.accent_color)],
                  foreground=[('selected', 'white')])
        self.style = style

        self.root.configure(bg=self.bg_color)

    def create_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        canvas = tk.Canvas(header_frame, width=60, height=60, bg=self.bg_color, highlightthickness=0)
        canvas.pack(side=tk.LEFT, padx=(0, 10))

        pil_image = Image.open("assets/bait.jpg")  # replace with your image path
        pil_image = pil_image.resize((50, 50), Image.Resampling.LANCZOS)
        self.logo_image = ImageTk.PhotoImage(pil_image)
        canvas.create_image(30, 30, image=self.logo_image, anchor=tk.CENTER)

        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)

        title_label = ttk.Label(title_frame, text="LureBuster", font=("Helvetica", 24, "bold"))
        title_label.pack(anchor=tk.W)

        subtitle_label = ttk.Label(title_frame, text="Phishing Site Disruptor", font=("Helvetica", 12))
        subtitle_label.pack(anchor=tk.W)

        warning_frame = ttk.Frame(main_frame)
        warning_frame.pack(fill=tk.X, pady=(0, 10))

        warning_label = ttk.Label(
                warning_frame,
                text="⚠️ EDUCATIONAL PURPOSES ONLY: This tool is for security research and education. Misuse may "
                     "violate laws.",
                foreground=self.warning_color,
                font=("Helvetica", 10, "italic")
        )
        warning_label.pack(fill=tk.X)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        main_tab = ttk.Frame(notebook)
        notebook.add(main_tab, text="Attack Console")

        templates_tab = ttk.Frame(notebook)
        notebook.add(templates_tab, text="Request Templates")

        analytics_tab = ttk.Frame(notebook)
        notebook.add(analytics_tab, text="Analytics")

        settings_tab = ttk.Frame(notebook)
        notebook.add(settings_tab, text="Settings")

        self.build_main_tab(main_tab)

        self.build_templates_tab(templates_tab)

        self.build_analytics_tab(analytics_tab)

        self.build_settings_tab(settings_tab)

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_label = ttk.Label(status_frame, text="Ready", font=("Helvetica", 9))
        self.status_label.pack(side=tk.LEFT)

        version_label = ttk.Label(status_frame, text="v1.0.0", font=("Helvetica", 9))
        version_label.pack(side=tk.RIGHT)

    def build_main_tab(self, parent):
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        url_frame = ttk.Frame(left_frame)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        url_label = ttk.Label(url_frame, text="Target Phishing URL:")
        url_label.pack(anchor=tk.W)

        method_combo = ttk.Combobox(
                url_frame,
                textvariable=self.current_method,
                values=self.methods,
                width=10,
                state='readonly'
        )
        method_combo.current(0)
        method_combo.pack(side=tk.RIGHT, pady=(5, 0))

        url_entry = ttk.Entry(url_frame, textvariable=self.target_url, width=50)
        url_entry.pack(fill=tk.X, pady=(5, 0))

        params_frame = ttk.LabelFrame(left_frame, text="Attack Parameters")
        params_frame.pack(fill=tk.X, pady=(0, 10))

        count_frame = ttk.Frame(params_frame)
        count_frame.pack(fill=tk.X, pady=5)

        count_label = ttk.Label(count_frame, text="Number of Requests:")
        count_label.pack(side=tk.LEFT)

        count_spinbox = ttk.Spinbox(
                count_frame,
                from_=1,
                to=10000,
                textvariable=self.request_count,
                width=10
        )
        count_spinbox.pack(side=tk.RIGHT)

        threads_frame = ttk.Frame(params_frame)
        threads_frame.pack(fill=tk.X, pady=5)

        threads_label = ttk.Label(threads_frame, text="Number of Threads:")
        threads_label.pack(side=tk.LEFT)

        threads_spinbox = ttk.Spinbox(
                threads_frame,
                from_=1,
                to=50,
                textvariable=self.threads_count,
                width=10
        )
        threads_spinbox.pack(side=tk.RIGHT)

        delay_frame = ttk.Frame(params_frame)
        delay_frame.pack(fill=tk.X, pady=5)

        delay_label = ttk.Label(delay_frame, text="Delay Between Requests (seconds):")
        delay_label.pack(side=tk.LEFT)

        delay_spinbox = ttk.Spinbox(
                delay_frame,
                from_=0.0,
                to=10.0,
                increment=0.1,
                textvariable=self.delay,
                width=10
        )
        delay_spinbox.pack(side=tk.RIGHT)

        region_frame = ttk.Frame(params_frame)
        region_frame.pack(fill=tk.X, pady=5)

        region_label = ttk.Label(region_frame, text="Primary Region for Data:")
        region_label.pack(side=tk.LEFT)

        region_combo = ttk.Combobox(
                region_frame,
                textvariable=self.current_region,
                values=self.regions,
                width=10,
                state='readonly'
        )
        region_combo.pack(side=tk.RIGHT)

        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        select_template_button = ttk.Button(
                buttons_frame,
                text="Select Template",
                command=self.select_template_for_attack
        )
        select_template_button.pack(side=tk.LEFT, padx=5)

        # Add a label to show selected template
        self.template_label = ttk.Label(
                buttons_frame,
                text="No template selected",
                foreground="gray"
        )
        self.template_label.pack(side=tk.LEFT, padx=5)

        self.start_button = ttk.Button(
                buttons_frame,
                text="Start Attack",
                command=self.start_attack
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(
                buttons_frame,
                text="Stop",
                command=self.stop_attack,
                state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)

        progress_frame = ttk.LabelFrame(left_frame, text="Progress")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
                progress_frame,
                orient=tk.HORIZONTAL,
                length=100,
                mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        self.progress_label = ttk.Label(progress_frame, text="0/0 requests completed")
        self.progress_label.pack(anchor=tk.W, padx=5, pady=(0, 5))

        stats_frame = ttk.LabelFrame(left_frame, text="Statistics")
        stats_frame.pack(fill=tk.X)

        stats_inner_frame = ttk.Frame(stats_frame)
        stats_inner_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(stats_inner_frame, text="Requests Sent:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sent_label = ttk.Label(stats_inner_frame, text="0")
        self.sent_label.grid(row=0, column=1, sticky=tk.E, pady=2)

        ttk.Label(stats_inner_frame, text="Successful:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.success_label = ttk.Label(stats_inner_frame, text="0")
        self.success_label.grid(row=1, column=1, sticky=tk.E, pady=2)

        ttk.Label(stats_inner_frame, text="Failed:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.failed_label = ttk.Label(stats_inner_frame, text="0")
        self.failed_label.grid(row=2, column=1, sticky=tk.E, pady=2)

        ttk.Label(stats_inner_frame, text="Elapsed Time:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.time_label = ttk.Label(stats_inner_frame, text="00:00:00")
        self.time_label.grid(row=3, column=1, sticky=tk.E, pady=2)

        ttk.Label(stats_inner_frame, text="Requests/sec:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.rate_label = ttk.Label(stats_inner_frame, text="0.0")
        self.rate_label.grid(row=4, column=1, sticky=tk.E, pady=2)

        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        log_label = ttk.Label(right_frame, text="Activity Log:")
        log_label.pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(
                right_frame,
                wrap=tk.WORD,
                width=50,
                height=20,
                bg=self.bg_color,
                fg=self.fg_color,
                insertbackground=self.fg_color
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.log_text.config(state=tk.DISABLED)

    def build_templates_tab(self, parent):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = ttk.Label(
                info_frame,
                text="Configure request templates to match the target phishing site's form structure.",
                wraplength=800
        )
        info_label.pack(anchor=tk.W)

        columns_frame = ttk.Frame(parent)
        columns_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(columns_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        templates_label = ttk.Label(left_frame, text="Available Templates:")
        templates_label.pack(anchor=tk.W)

        self.templates_listbox = tk.Listbox(
                left_frame,
                bg=self.bg_color,
                fg=self.fg_color,
                selectbackground=self.accent_color,
                selectforeground="white",
                height=15
        )
        self.templates_listbox.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.templates_listbox.bind('<<ListboxSelect>>', self.on_template_select)

        template_buttons_frame = ttk.Frame(left_frame)
        template_buttons_frame.pack(fill=tk.X, pady=(5, 0))

        add_template_button = ttk.Button(
                template_buttons_frame,
                text="Add New",
                command=self.add_template
        )
        add_template_button.pack(side=tk.LEFT, padx=(0, 5))

        delete_template_button = ttk.Button(
                template_buttons_frame,
                text="Delete",
                command=self.delete_template
        )
        delete_template_button.pack(side=tk.LEFT)

        right_frame = ttk.Frame(columns_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        editor_label = ttk.Label(right_frame, text="Template Editor:")
        editor_label.pack(anchor=tk.W)

        self.template_editor = scrolledtext.ScrolledText(
                right_frame,
                wrap=tk.WORD,
                width=50,
                height=15,
                bg=self.bg_color,
                fg=self.fg_color,
                insertbackground=self.fg_color
        )
        self.template_editor.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # Add Save button frame below the editor
        save_button_frame = ttk.Frame(right_frame)
        save_button_frame.pack(fill=tk.X, pady=(5, 0))

        save_template_button = ttk.Button(
                save_button_frame,
                text="Save Template",
                command=self.save_template
        )
        save_template_button.pack(side=tk.RIGHT)

        help_frame = ttk.LabelFrame(parent, text="Template Help")
        help_frame.pack(fill=tk.X, pady=(10, 0))

        help_text = ttk.Label(
                help_frame,
                text="Templates use placeholders like {{email}} that will be replaced with generated data.\n"
                     "Available generators: email, password, username, first_name, last_name, phone_number, "
                     "address, credit_card, user_agent, ip_address",
                wraplength=800
        )
        help_text.pack(padx=5, pady=5)

        self.templates = {}
        self.current_template = None
        self.load_templates()

    def load_templates(self):
        """Load templates from persistent storage"""
        try:
            with open('templates.json', 'r') as f:
                self.templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.templates.update(self.example_template)

        self.templates_listbox.delete(0, tk.END)
        for name in self.templates:
            self.templates_listbox.insert(tk.END, name)

        if self.templates:
            self.current_template = self.templates[list(self.templates.keys())[0]]

    def select_template_for_attack(self):
        """Open a dialog to select which template to use for the attack"""
        if not self.templates:
            messagebox.showwarning("Warning", "No templates available")
            return

        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Template")
        dialog.geometry("300x300")

        # List available templates
        listbox = tk.Listbox(
                dialog,
                bg=self.bg_color,
                fg=self.fg_color,
                selectbackground=self.accent_color,
                selectforeground="white",
                height=5
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for name in self.templates:
            listbox.insert(tk.END, name)

        # Add select button
        def on_select():
            selection = listbox.curselection()
            if selection:
                self.selected_template = listbox.get(selection[0])
                self.template_label.config(
                        text=f"Template: {self.selected_template}",
                        foreground=self.fg_color
                )
                dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(padx=5, pady=(0, 5))

        ttk.Button(
                button_frame,
                text="Select",
                command=on_select,
        ).pack(side=tk.RIGHT)

        dialog.transient(self.root)
        dialog.grab_set()
        dialog.wait_window(dialog)

    def build_analytics_tab(self, parent):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = ttk.Label(
                info_frame,
                text="Real-time analytics of your phishing disruption campaigns.",
                wraplength=800
        )
        info_label.pack(anchor=tk.W)

        charts_frame = ttk.Frame(parent)
        charts_frame.pack(fill=tk.BOTH, expand=True)

        rate_frame = ttk.LabelFrame(charts_frame, text="Request Rate Over Time")
        rate_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.rate_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.rate_figure.patch.set_facecolor(self.bg_color)
        self.rate_plot = self.rate_figure.add_subplot(111)
        self.rate_plot.set_facecolor(self.bg_color)
        self.rate_plot.tick_params(colors=self.fg_color)
        self.rate_plot.spines['bottom'].set_color(self.fg_color)
        self.rate_plot.spines['top'].set_color(self.fg_color)
        self.rate_plot.spines['left'].set_color(self.fg_color)
        self.rate_plot.spines['right'].set_color(self.fg_color)
        self.rate_plot.set_xlabel('Time', color=self.fg_color)
        self.rate_plot.set_ylabel('Requests/sec', color=self.fg_color)
        self.rate_plot.set_title('Request Rate', color=self.fg_color)

        self.rate_canvas = FigureCanvasTkAgg(self.rate_figure, rate_frame)
        self.rate_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        status_frame = ttk.LabelFrame(charts_frame, text="Request Status")
        status_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.status_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.status_figure.patch.set_facecolor(self.bg_color)
        self.status_plot = self.status_figure.add_subplot(111)
        self.status_plot.set_facecolor(self.bg_color)
        self.status_plot.tick_params(colors=self.fg_color)
        self.status_plot.set_title('Request Status', color=self.fg_color)

        self.status_canvas = FigureCanvasTkAgg(self.status_figure, status_frame)
        self.status_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        history_frame = ttk.LabelFrame(parent, text="Campaign History")
        history_frame.pack(fill=tk.X, pady=(10, 0))

        columns = ("date", "target", "requests", "success_rate", "duration")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings")

        self.history_tree.heading("date", text="Date")
        self.history_tree.heading("target", text="Target")
        self.history_tree.heading("requests", text="Requests")
        self.history_tree.heading("success_rate", text="Success Rate")
        self.history_tree.heading("duration", text="Duration")

        self.history_tree.column("date", width=150)
        self.history_tree.column("target", width=300)
        self.history_tree.column("requests", width=100)
        self.history_tree.column("success_rate", width=100)
        self.history_tree.column("duration", width=100)

        self.start_button = ttk.Button(
                history_frame,
                text="Clear",
                command=self.clear_history
        )

        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        self.history_tree.pack(fill=tk.X, padx=5, pady=5)

        example_data = [
                ("2023-05-01 14:30", "https://fake-bank.phishing.com", "5000", "98%", "00:15:23"),
                ("2023-04-28 09:15", "https://paypal-secure.phishing.net", "2500", "95%", "00:08:45"),
                ("2023-04-25 18:20", "https://login-account.phishing.org", "10000", "99%", "00:30:12")
        ]

        for item in example_data:
            self.history_tree.insert("", tk.END, values=item)

    def clear_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)

        self.rate_plot.clear()
        self.rate_canvas.draw()
        self.status_plot.clear()
        self.status_canvas.draw()

    def build_settings_tab(self, parent):
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_label = ttk.Label(
                info_frame,
                text="Configure application settings and data generation parameters.",
                wraplength=800
        )
        info_label.pack(anchor=tk.W)

        settings_frame = ttk.Frame(parent)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(settings_frame, text="General Settings")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        proxy_frame = ttk.Frame(left_frame)
        proxy_frame.pack(fill=tk.X, pady=5)

        proxy_label = ttk.Label(proxy_frame, text="Use Proxy:")
        proxy_label.pack(side=tk.LEFT)

        self.proxy_var = tk.BooleanVar(value=False)
        proxy_check = ttk.Checkbutton(proxy_frame, variable=self.proxy_var)
        proxy_check.pack(side=tk.RIGHT)

        proxy_addr_frame = ttk.Frame(left_frame)
        proxy_addr_frame.pack(fill=tk.X, pady=5)

        proxy_addr_label = ttk.Label(proxy_addr_frame, text="Proxy Address:")
        proxy_addr_label.pack(side=tk.LEFT)

        self.proxy_addr_var = tk.StringVar()
        proxy_addr_entry = ttk.Entry(proxy_addr_frame, textvariable=self.proxy_addr_var)
        proxy_addr_entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        log_level_frame = ttk.Frame(left_frame)
        log_level_frame.pack(fill=tk.X, pady=5)

        log_level_label = ttk.Label(log_level_frame, text="Log Level:")
        log_level_label.pack(side=tk.LEFT)

        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(
                log_level_frame,
                textvariable=self.log_level_var,
                values=["DEBUG", "INFO", "WARNING", "ERROR"],
                width=10
        )
        log_level_combo.pack(side=tk.RIGHT)

        autosave_frame = ttk.Frame(left_frame)
        autosave_frame.pack(fill=tk.X, pady=5)

        autosave_label = ttk.Label(autosave_frame, text="Auto-save Logs:")
        autosave_label.pack(side=tk.LEFT)

        self.autosave_var = tk.BooleanVar(value=True)
        autosave_check = ttk.Checkbutton(autosave_frame, variable=self.autosave_var)
        autosave_check.pack(side=tk.RIGHT)

        right_frame = ttk.LabelFrame(settings_frame, text="Data Generation Settings")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        pwd_frame = ttk.Frame(right_frame)
        pwd_frame.pack(fill=tk.X, pady=5)

        pwd_label = ttk.Label(pwd_frame, text="Password Complexity:")
        pwd_label.pack(side=tk.LEFT)

        self.pwd_var = tk.StringVar(value="Medium")
        pwd_combo = ttk.Combobox(
                pwd_frame,
                textvariable=self.pwd_var,
                values=self.password_compexities.keys(),
                width=10
        )

        pwd_combo.pack(side=tk.RIGHT)

        special_frame = ttk.Frame(right_frame)
        special_frame.pack(fill=tk.X, pady=5)

        special_label = ttk.Label(special_frame, text="Include Special Characters:")
        special_label.pack(side=tk.LEFT)

        self.special_var = tk.BooleanVar(value=True)
        special_check = ttk.Checkbutton(special_frame, variable=self.special_var)
        special_check.pack(side=tk.RIGHT)

        cc_frame = ttk.Frame(right_frame)
        cc_frame.pack(fill=tk.X, pady=5)

        cc_label = ttk.Label(cc_frame, text="Credit Card Types:")
        cc_label.pack(anchor=tk.W)

        cc_types_frame = ttk.Frame(right_frame)
        cc_types_frame.pack(fill=tk.X, pady=(0, 5))

        self.visa_var = tk.BooleanVar(value=True)
        visa_check = ttk.Checkbutton(cc_types_frame, text="Visa", variable=self.visa_var)
        visa_check.pack(side=tk.LEFT)

        self.mc_var = tk.BooleanVar(value=True)
        mc_check = ttk.Checkbutton(cc_types_frame, text="MasterCard", variable=self.mc_var)
        mc_check.pack(side=tk.LEFT)

        self.amex_var = tk.BooleanVar(value=True)
        amex_check = ttk.Checkbutton(cc_types_frame, text="Amex", variable=self.amex_var)
        amex_check.pack(side=tk.LEFT)

        self.discover_var = tk.BooleanVar(value=True)
        discover_check = ttk.Checkbutton(cc_types_frame, text="Discover", variable=self.discover_var)
        discover_check.pack(side=tk.LEFT)

        save_settings_button = ttk.Button(
                parent,
                text="Save Settings",
                command=self.save_settings
        )
        save_settings_button.pack(anchor=tk.E, pady=(10, 0))

    def add_template(self):
        """Add a new template"""
        name = simpledialog.askstring("New Template", "Enter template name:")
        if not name:
            return

        if name in self.templates:
            messagebox.showerror("Error", "A template with this name already exists")
            return

        self.templates[name] = self.example_template
        self.templates[name]["name"] = name

        self.templates_listbox.insert(tk.END, name)
        self.save_templates()

    def delete_template(self):
        """Delete selected template"""
        selection = self.templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "No template selected")
            return

        selected_name = self.templates_listbox.get(selection[0])

        if messagebox.askyesno("Confirm", f"Delete template '{selected_name}'?"):
            del self.templates[selected_name]
            self.templates_listbox.delete(selection[0])
            self.template_editor.delete(1.0, tk.END)
            self.save_templates()

    def save_template(self):
        """Save the currently edited template"""
        if not self.current_template:
            messagebox.showwarning("Warning", "No template selected")
            return

        try:
            edited_content = self.template_editor.get("1.0", tk.END).strip()
            template_data = json.loads(edited_content)
            self.templates[self.current_template] = template_data

            self.save_templates()

            messagebox.showinfo("Success", "Template saved successfully")

        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Invalid JSON: {str(e)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")

    def save_templates(self):
        """Save templates to persistent storage"""
        with open('templates.json', 'w') as f:
            json.dump(self.templates, f, indent=2)

    def on_template_select(self, event):
        """Handle template selection from listbox"""
        selection = self.templates_listbox.curselection()
        if not selection:
            return

        selected_name = self.templates_listbox.get(selection[0])
        self.current_template = selected_name

        self.template_editor.delete(1.0, tk.END)
        template_data = self.templates[selected_name]
        self.template_editor.insert(tk.END, json.dumps(template_data, indent=4))

    def save_settings(self):
        # This does not work yet
        self.log_message("Settings saved")
        messagebox.showinfo("Settings Saved", "Your settings have been saved.")

    def start_attack(self):
        url = self.target_url.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a target URL")
            return

        if not url.startswith(("http://", "https://")):
            url = "http://" + url
            self.target_url.set(url)

        if self.request_count.get() <= 0:
            messagebox.showerror("Error", "Number of requests must be greater than 0")
            return

        if self.threads_count.get() <= 0:
            messagebox.showerror("Error", "Number of threads must be greater than 0")
            return

        if not messagebox.askyesno("Confirm Attack",
                                   f"Are you sure you want to send {self.request_count.get()} requests to {url}?\n\n"
                                   "This tool should only be used for educational purposes and security testing "
                                   "on systems you have permission to test."):
            return

        self.select_template_for_attack()
        if not self.selected_template:
            return

        self.stats = {
                "requests_sent"      : 0,
                "successful_requests": 0,
                "failed_requests"    : 0,
                "start_time"         : time.time(),
                "end_time"           : None,
                "request_times"      : [],
                "request_rates"      : []
        }

        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar["maximum"] = self.request_count.get()
        self.progress_bar["value"] = 0
        self.progress_label.config(text=f"0/{self.request_count.get()} requests completed")
        self.status_label.config(text="Running attack...")

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.log_message(f"Starting attack on {url}")
        self.log_message(f"Sending {self.request_count.get()} requests using {self.threads_count.get()} threads")

        self.timer_thread = threading.Thread(target=self.update_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()

        self.request_threads = []
        for i in range(self.threads_count.get()):
            thread = threading.Thread(target=self.send_requests, args=(i + 1,))
            thread.daemon = True
            thread.start()
            self.request_threads.append(thread)

        self.chart_thread = threading.Thread(target=self.update_charts)
        self.chart_thread.daemon = True
        self.chart_thread.start()

    def stop_attack(self):
        self.running = False
        self.status_label.config(text="Stopping attack...")
        self.log_message("Stopping attack...")

        for thread in self.request_threads:
            if thread.is_alive():
                thread.join(1.0)  # Wait with timeoutn

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Attack stopped")
        self.log_message("Attack stopped")

        if self.stats["end_time"] is None:
            self.stats["end_time"] = time.time()

        self.add_to_history()

    def send_requests(self, thread_id):
        url = self.target_url.get()
        count = self.request_count.get()
        delay = self.delay.get()

        sending_template = self.selected_template.copy()

        while self.running and self.stats["requests_sent"] < count:
            email = faker.email()
            password_complexity = self.pwd_var.get()
            password = faker.password(length=self.password_compexities.get(password_complexity, 6))
            user_agent = faker.user_agent()

            sending_template["headers"]["User-Agent"] = user_agent
            sending_template["form_fields"]["email"] = email
            sending_template["form_fields"]["password"] = password

            try:
                success = random.random() > 0.1

                status = "SUCCESS" if success else "FAILED"
                self.log_message(f"Thread {thread_id}: Sent request with email {email} - {status}")

                self.stats["requests_sent"] += 1
                if success:
                    self.stats["successful_requests"] += 1
                else:
                    self.stats["failed_requests"] += 1

                current_time = time.time() - self.stats["start_time"]
                self.stats["request_times"].append(current_time)

                if len(self.stats["request_times"]) > 1:
                    recent_times = self.stats["request_times"][-10:]
                    if len(recent_times) > 1:
                        time_diff = recent_times[-1] - recent_times[0]
                        if time_diff > 0:
                            rate = len(recent_times) / time_diff
                            self.stats["request_rates"].append((current_time, rate))

                self.update_progress()

                if self.stats["requests_sent"] >= count:
                    if self.running:
                        self.stats["end_time"] = time.time()
                        self.root.after(0, self.attack_completed)
                    break

                time.sleep(delay)

            except Exception as e:
                self.log_message(f"Thread {thread_id}: Error sending request: {str(e)}")
                self.stats["requests_sent"] += 1
                self.stats["failed_requests"] += 1
                self.update_progress()
                time.sleep(delay)

    def create_payload(self) -> dict:
        """Creates the fake data payload"""

        region_to_locale = {
                "US": "en_US",
                "UK": "en_GB",
                "CA": "en_CA",
                "AU": "en_AU",
                "DE": "de_DE",
                "FR": "fr_FR",
                "JP": "ja_JP",
                "BR": "pt_BR",
                "IN": "en_IN",
                "IT": "it_IT"
        }

        region = self.current_region.get()
        faker = Faker(region_to_locale.get(region, "en_US"))

    def replace_generators(self, template: dict) -> dict:
        ...

    def update_progress(self):
        self.progress_bar["value"] = self.stats["requests_sent"]
        self.progress_label.config(text=f"{self.stats['requests_sent']}/{self.request_count.get()} requests completed")
        self.sent_label.config(text=str(self.stats["requests_sent"]))
        self.success_label.config(text=str(self.stats["successful_requests"]))
        self.failed_label.config(text=str(self.stats["failed_requests"]))

        if self.stats["start_time"]:
            elapsed = time.time() - self.stats["start_time"]
            if elapsed > 0:
                rate = self.stats["requests_sent"] / elapsed
                self.rate_label.config(text=f"{rate:.1f}")

    def update_timer(self):
        while self.running:
            if self.stats["start_time"]:
                elapsed = time.time() - self.stats["start_time"]
                hours, remainder = divmod(int(elapsed), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                self.time_label.config(text=time_str)
            time.sleep(1)

    def update_charts(self):
        while self.running:
            if len(self.stats["request_rates"]) > 1:
                times, rates = zip(*self.stats["request_rates"])

                self.rate_plot.clear()
                self.rate_plot.plot(times, rates, color=self.accent_color)
                self.rate_plot.set_facecolor(self.bg_color)
                self.rate_plot.tick_params(colors=self.fg_color)
                self.rate_plot.set_xlabel('Time (s)', color=self.fg_color)
                self.rate_plot.set_ylabel('Requests/sec', color=self.fg_color)
                self.rate_plot.set_title('Request Rate', color=self.fg_color)
                self.rate_canvas.draw()

            labels = ['Success', 'Failed']
            sizes = [self.stats["successful_requests"], self.stats["failed_requests"]]
            colors = [self.success_color, self.warning_color]

            self.status_plot.clear()
            if sum(sizes) > 0:  # Avoid division by zero
                self.status_plot.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
                self.status_plot.set_title('Request Status', color=self.fg_color)
                self.status_canvas.draw()

            time.sleep(0.5)

    def attack_completed(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="Attack completed")
        self.log_message("Attack completed")

        self.add_to_history()

        elapsed = self.stats["end_time"] - self.stats["start_time"]
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        success_rate = 0
        if self.stats["requests_sent"] > 0:
            success_rate = (self.stats["successful_requests"] / self.stats["requests_sent"]) * 100

        messagebox.showinfo("Attack Summary",
                            f"Attack completed\n\n"
                            f"Target: {self.target_url.get()}\n"
                            f"Requests sent: {self.stats['requests_sent']}\n"
                            f"Successful: {self.stats['successful_requests']} ({success_rate:.1f}%)\n"
                            f"Failed: {self.stats['failed_requests']}\n"
                            f"Duration: {time_str}\n")

    def add_to_history(self):
        if self.stats["start_time"] and self.stats["end_time"]:
            elapsed = self.stats["end_time"] - self.stats["start_time"]
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            success_rate = 0
            if self.stats["requests_sent"] > 0:
                success_rate = (self.stats["successful_requests"] / self.stats["requests_sent"]) * 100

            date_str = datetime.fromtimestamp(self.stats["start_time"]).strftime("%Y-%m-%d %H:%M")

            self.history_tree.insert("", 0, values=(
                    date_str,
                    self.target_url.get(),
                    str(self.stats["requests_sent"]),
                    f"{success_rate:.1f}%",
                    time_str
            ))

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

        logging.info(message)


def main():
    root = tk.Tk()
    LureBuster(root)
    root.mainloop()


if __name__ == "__main__":
    main()
