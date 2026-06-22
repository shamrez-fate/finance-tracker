"""
app.py — Main CustomTkinter GUI for Personal Finance Tracker.
"""

from __future__ import annotations

import calendar
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import tkinter.ttk as ttk

import customtkinter as ctk

import database as db
import utils


# ── Theme constants ──────────────────────────────────────────────────────────
BG         = "#0F1117"
SURFACE    = "#1A1D27"
SURFACE2   = "#22253A"
BORDER     = "#2A2D3E"
ACCENT     = "#6C63FF"
ACCENT2    = "#8F88FF"
TEXT       = "#E8E8F0"
SUBTEXT    = "#8888AA"
GREEN      = "#2ECC71"
RED        = "#E74C3C"
YELLOW     = "#F1C40F"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ── Re-usable widget helpers ─────────────────────────────────────────────────

def _label(parent, text, size=13, weight="normal", color=TEXT, **kw):
    return ctk.CTkLabel(parent, text=text, font=("Inter", size, weight),
                        text_color=color, **kw)


def _button(parent, text, command, fg=ACCENT, hover=ACCENT2, width=120, **kw):
    return ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=fg, hover_color=hover,
        font=("Inter", 12, "bold"),
        corner_radius=8, width=width, **kw,
    )


def _entry(parent, placeholder="", width=200, **kw):
    return ctk.CTkEntry(
        parent, placeholder_text=placeholder,
        fg_color=SURFACE2, border_color=BORDER,
        text_color=TEXT, placeholder_text_color=SUBTEXT,
        font=("Inter", 12), width=width, **kw,
    )


def _combo(parent, values, width=180, **kw):
    return ctk.CTkComboBox(
        parent, values=values,
        fg_color=SURFACE2, border_color=BORDER,
        button_color=ACCENT, dropdown_fg_color=SURFACE,
        text_color=TEXT, font=("Inter", 12),
        width=width, **kw,
    )


def _card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12,
                        border_width=1, border_color=BORDER, **kw)


def _embed_figure(fig, parent, padx=0, pady=0):
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=padx, pady=pady)
    return canvas


# ── Main app ─────────────────────────────────────────────────────────────────

class FinanceTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.initialize_database()

        self.title("Finance Tracker")
        self.geometry("1280x800")
        self.minsize(1100, 700)
        self.configure(fg_color=BG)

        self._build_sidebar()
        self._build_content_area()
        self._show_dashboard()

    # ── Sidebar ──────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=SURFACE, width=220,
                                    corner_radius=0, border_width=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(28, 20), padx=20)
        ctk.CTkLabel(logo_frame, text="💰", font=("Inter", 30)).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" Finance\nTracker",
                     font=("Inter", 14, "bold"), text_color=TEXT,
                     justify="left").pack(side="left", padx=8)

        ctk.CTkFrame(self.sidebar, fg_color=BORDER, height=1).pack(fill="x", padx=16, pady=4)

        nav_items = [
            ("📊  Dashboard",   self._show_dashboard),
            ("➕  Add Transaction", self._show_add_transaction),
            ("📋  Transactions", self._show_transactions),
            ("📈  Analytics",   self._show_analytics),
            ("📆  Monthly Summary", self._show_monthly_summary),
            ("🏷️  Categories",  self._show_categories),
        ]

        self._nav_buttons: list[ctk.CTkButton] = []
        for label, cmd in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=label, command=lambda c=cmd: self._nav(c),
                anchor="w", font=("Inter", 12),
                fg_color="transparent", hover_color=SURFACE2,
                text_color=SUBTEXT, corner_radius=8,
                height=40,
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_buttons.append(btn)

        # Version tag at bottom
        ctk.CTkLabel(self.sidebar, text="v1.0 · Personal Edition",
                     font=("Inter", 10), text_color=SUBTEXT).pack(
            side="bottom", pady=14)

        self._active_btn: ctk.CTkButton | None = None

    def _nav(self, command):
        command()

    def _highlight_nav(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color=ACCENT, text_color=TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=SUBTEXT)

    # ── Content area ─────────────────────────────────────────────────────────

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def _show_dashboard(self):
        self._highlight_nav(0)
        self._clear_content()

        now = datetime.now()
        summary = db.monthly_summary(now.year, now.month)
        trend   = db.monthly_trend(12)
        recent  = db.fetch_transactions(limit=8)

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))
        _label(header, "Dashboard", size=22, weight="bold").pack(side="left")
        _label(header, now.strftime("  %B %Y"), size=13, color=SUBTEXT).pack(side="left", pady=(5,0))

        # KPI cards
        kpi_row = ctk.CTkFrame(self.content, fg_color="transparent")
        kpi_row.pack(fill="x", padx=28, pady=12)
        for col in range(3):
            kpi_row.grid_columnconfigure(col, weight=1, uniform="kpi")

        kpis = [
            ("Total Income",   f"PKR {summary['income']:,.0f}",  GREEN,  "↑ This month"),
            ("Total Expense",  f"PKR {summary['expense']:,.0f}", RED,    "↓ This month"),
            ("Net Savings",    f"PKR {summary['net']:,.0f}",
             GREEN if summary['net'] >= 0 else RED,              "Balance"),
        ]
        for col, (title, value, color, sub) in enumerate(kpis):
            card = _card(kpi_row)
            card.grid(row=0, column=col, padx=6, sticky="ew")
            _label(card, title, size=11, color=SUBTEXT).pack(anchor="w", padx=16, pady=(14, 2))
            _label(card, value, size=22, weight="bold", color=color).pack(anchor="w", padx=16)
            _label(card, sub, size=10, color=SUBTEXT).pack(anchor="w", padx=16, pady=(0, 14))

        # Charts row
        charts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        charts_row.pack(fill="both", expand=True, padx=28, pady=(4, 8))
        charts_row.grid_columnconfigure(0, weight=2)
        charts_row.grid_columnconfigure(1, weight=1)
        charts_row.grid_rowconfigure(0, weight=1)

        # Bar chart
        bar_card = _card(charts_row)
        bar_card.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
        if trend:
            fig = utils.chart_monthly_bar(trend)
            _embed_figure(fig, bar_card, padx=12, pady=12)
        else:
            _label(bar_card, "No data yet", color=SUBTEXT).pack(expand=True)

        # Donut chart
        donut_card = _card(charts_row)
        donut_card.grid(row=0, column=1, padx=(6, 0), sticky="nsew")
        if summary["by_category"]:
            fig2 = utils.chart_category_donut(summary["by_category"], "expense")
            _embed_figure(fig2, donut_card, padx=8, pady=8)
        else:
            _label(donut_card, "No expense data", color=SUBTEXT).pack(expand=True)

        # Recent transactions strip
        recent_card = _card(self.content)
        recent_card.pack(fill="x", padx=28, pady=(0, 18))
        _label(recent_card, "Recent Transactions", size=13, weight="bold").pack(
            anchor="w", padx=16, pady=(12, 6))
        self._render_tx_strip(recent_card, recent)

    def _render_tx_strip(self, parent, transactions: list[dict]):
        if not transactions:
            _label(parent, "No transactions yet.", color=SUBTEXT).pack(pady=12)
            return
        for tx in transactions:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            color = tx.get("color") or (GREEN if tx["type"] == "income" else RED)
            circle = ctk.CTkLabel(row, text="●", font=("Inter", 10),
                                  text_color=color, width=18)
            circle.pack(side="left")
            _label(row, tx.get("category") or "—", size=11, color=SUBTEXT,
                   width=130, anchor="w").pack(side="left", padx=(4, 0))
            _label(row, tx.get("description") or "", size=11,
                   anchor="w").pack(side="left", padx=8, fill="x", expand=True)
            _label(row, tx["date"], size=10, color=SUBTEXT).pack(side="right", padx=8)
            sign = "+" if tx["type"] == "income" else "−"
            _label(row, f"{sign} PKR {tx['amount']:,.0f}", size=12,
                   weight="bold", color=GREEN if tx["type"] == "income" else RED
                   ).pack(side="right")
        ctk.CTkFrame(parent, fg_color=BORDER, height=1).pack(fill="x", padx=16, pady=(4, 10))

    # ========================================================================
    # ADD TRANSACTION
    # ========================================================================

    def _show_add_transaction(self, prefill: dict | None = None):
        self._highlight_nav(1)
        self._clear_content()

        editing = prefill is not None
        title_text = "Edit Transaction" if editing else "Add Transaction"

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))
        _label(header, title_text, size=22, weight="bold").pack(side="left")

        form_card = _card(self.content)
        form_card.pack(fill="x", padx=28, pady=10)

        # Type selector
        type_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        type_frame.pack(fill="x", padx=20, pady=(18, 8))
        _label(type_frame, "Transaction Type", size=11, color=SUBTEXT).pack(anchor="w")

        type_var = ctk.StringVar(value=prefill.get("type", "expense") if prefill else "expense")
        tabs = ctk.CTkSegmentedButton(
            type_frame,
            values=["expense", "income"],
            variable=type_var,
            fg_color=SURFACE2, selected_color=ACCENT,
            selected_hover_color=ACCENT2,
            unselected_color=SURFACE2, unselected_hover_color=BORDER,
            text_color=TEXT, font=("Inter", 12, "bold"),
            corner_radius=8, height=36,
        )
        tabs.pack(anchor="w", pady=(6, 0))

        # Grid fields
        fields_frame = ctk.CTkFrame(form_card, fg_color="transparent")
        fields_frame.pack(fill="x", padx=20, pady=8)
        for c in range(2):
            fields_frame.grid_columnconfigure(c, weight=1, uniform="ff")

        # Amount
        _label(fields_frame, "Amount (PKR)", size=11, color=SUBTEXT).grid(
            row=0, column=0, sticky="w", pady=(4, 2))
        amount_entry = _entry(fields_frame, "0.00", width=0)
        amount_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        if prefill:
            amount_entry.insert(0, str(prefill.get("amount", "")))

        # Date
        _label(fields_frame, "Date (YYYY-MM-DD)", size=11, color=SUBTEXT).grid(
            row=0, column=1, sticky="w", pady=(4, 2))
        date_entry = _entry(fields_frame, datetime.now().strftime("%Y-%m-%d"), width=0)
        date_entry.grid(row=1, column=1, sticky="ew")
        if prefill:
            date_entry.insert(0, prefill.get("date", ""))
        else:
            date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Category
        cats = db.fetch_categories()
        cat_names = [c["name"] for c in cats]
        cat_map   = {c["name"]: c for c in cats}

        _label(fields_frame, "Category", size=11, color=SUBTEXT).grid(
            row=2, column=0, sticky="w", pady=(12, 2))
        cat_combo = _combo(fields_frame, cat_names or ["(none)"], width=0)
        cat_combo.grid(row=3, column=0, sticky="ew", padx=(0, 10))
        if prefill and prefill.get("category"):
            cat_combo.set(prefill["category"])
        else:
            # Default to first matching type
            def _update_cats(*_):
                filtered = [c["name"] for c in cats if c["type"] == type_var.get()]
                cat_combo.configure(values=filtered or ["(none)"])
                if filtered:
                    cat_combo.set(filtered[0])
            type_var.trace_add("write", _update_cats)
            _update_cats()

        # Description
        _label(fields_frame, "Description (optional)", size=11, color=SUBTEXT).grid(
            row=2, column=1, sticky="w", pady=(12, 2))
        desc_entry = _entry(fields_frame, "e.g. Groceries at Metro", width=0)
        desc_entry.grid(row=3, column=1, sticky="ew")
        if prefill:
            desc_entry.insert(0, prefill.get("description") or "")

        # Submit
        def _submit():
            raw_amount = amount_entry.get().strip()
            raw_date   = date_entry.get().strip()
            cat_name   = cat_combo.get().strip()
            desc       = desc_entry.get().strip()
            tx_type    = type_var.get()

            # Validate
            try:
                amount = float(raw_amount)
                assert amount > 0
            except Exception:
                messagebox.showerror("Invalid Amount", "Enter a positive number for amount.")
                return
            try:
                datetime.strptime(raw_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.")
                return

            cat_id = cat_map[cat_name]["id"] if cat_name in cat_map else None

            if editing:
                db.update_transaction(prefill["id"], tx_type, amount, cat_id, desc, raw_date)
                messagebox.showinfo("Updated", "Transaction updated successfully.")
            else:
                db.add_transaction(tx_type, amount, cat_id, desc, raw_date)
                messagebox.showinfo("Saved", "Transaction added successfully.")
            self._show_transactions()

        btn_row = ctk.CTkFrame(form_card, fg_color="transparent")
        btn_row.pack(anchor="e", padx=20, pady=(8, 18))
        _button(btn_row, "Cancel", self._show_transactions,
                fg=SURFACE2, hover=BORDER).pack(side="left", padx=(0, 8))
        _button(btn_row, "Save Transaction", _submit, width=160).pack(side="left")

    # ========================================================================
    # TRANSACTIONS LIST
    # ========================================================================

    def _show_transactions(self):
        self._highlight_nav(2)
        self._clear_content()

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 4))
        _label(header, "Transactions", size=22, weight="bold").pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")
        _button(btn_row, "＋ Add", self._show_add_transaction, width=100).pack(side="left", padx=4)
        _button(btn_row, "⬇ Export CSV", self._export_transactions_csv,
                fg=SURFACE2, hover=BORDER, width=120).pack(side="left")

        # Filters
        filter_card = _card(self.content)
        filter_card.pack(fill="x", padx=28, pady=(8, 6))
        frow = ctk.CTkFrame(filter_card, fg_color="transparent")
        frow.pack(fill="x", padx=14, pady=10)

        self._search_var = ctk.StringVar()
        search_box = _entry(frow, "Search description / category …", width=240)
        search_box.pack(side="left", padx=(0, 10))
        search_box.configure(textvariable=self._search_var)

        self._type_filter_var = ctk.StringVar(value="all")
        type_seg = ctk.CTkSegmentedButton(
            frow, values=["all", "income", "expense"],
            variable=self._type_filter_var,
            fg_color=SURFACE2, selected_color=ACCENT,
            selected_hover_color=ACCENT2,
            unselected_color=SURFACE2, unselected_hover_color=BORDER,
            text_color=TEXT, font=("Inter", 11),
            corner_radius=6, height=32,
        )
        type_seg.pack(side="left", padx=4)

        cats = db.fetch_categories()
        cat_options = ["All categories"] + [c["name"] for c in cats]
        self._cat_filter_var = ctk.StringVar(value="All categories")
        cat_combo = _combo(frow, cat_options, width=160)
        cat_combo.pack(side="left", padx=10)
        cat_combo.configure(variable=self._cat_filter_var)

        _button(frow, "Filter", lambda: self._load_tx_table(
            tx_table, cats), width=80).pack(side="left")
        _button(frow, "Clear", lambda: self._reset_filters(
            search_box, cat_combo, tx_table, cats),
                fg=SURFACE2, hover=BORDER, width=70).pack(side="left", padx=6)

        # Table
        table_card = _card(self.content)
        table_card.pack(fill="both", expand=True, padx=28, pady=(0, 18))

        tx_table = self._build_tx_table(table_card)
        self._load_tx_table(tx_table, cats)

    def _build_tx_table(self, parent) -> ttk.Treeview:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Finance.Treeview",
                        background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE,
                        rowheight=36, borderwidth=0,
                        font=("Inter", 11))
        style.configure("Finance.Treeview.Heading",
                        background=SURFACE2, foreground=SUBTEXT,
                        borderwidth=0, font=("Inter", 11, "bold"),
                        relief="flat")
        style.map("Finance.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT)])

        cols = ("Date", "Type", "Category", "Description", "Amount")
        tree = ttk.Treeview(parent, columns=cols, show="headings",
                            style="Finance.Treeview", selectmode="browse")
        widths = [100, 80, 130, 300, 110]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=60,
                        anchor="center" if col in ("Date", "Type", "Amount") else "w")

        sb = ctk.CTkScrollbar(parent, command=tree.yview)
        sb.pack(side="right", fill="y", padx=(0, 4), pady=4)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(fill="both", expand=True, padx=4, pady=4)

        # Context menu
        menu = tk.Menu(self, tearoff=0, bg=SURFACE, fg=TEXT,
                       activebackground=ACCENT, activeforeground=TEXT,
                       borderwidth=0, font=("Inter", 11))
        menu.add_command(label="✏️  Edit",   command=lambda: self._edit_tx(tree))
        menu.add_command(label="🗑  Delete", command=lambda: self._delete_tx(tree))

        def _show_menu(event):
            row = tree.identify_row(event.y)
            if row:
                tree.selection_set(row)
                menu.post(event.x_root, event.y_root)

        tree.bind("<Button-3>", _show_menu)
        tree.bind("<Double-1>",  lambda e: self._edit_tx(tree))

        # store reference
        self._tx_tree = tree
        return tree

    def _load_tx_table(self, tree: ttk.Treeview, cats: list[dict]):
        search  = self._search_var.get().strip() if hasattr(self, "_search_var") else ""
        tf      = self._type_filter_var.get() if hasattr(self, "_type_filter_var") else "all"
        cat_nm  = self._cat_filter_var.get() if hasattr(self, "_cat_filter_var") else "All categories"

        cat_id = None
        if cat_nm != "All categories":
            matched = [c for c in cats if c["name"] == cat_nm]
            if matched:
                cat_id = matched[0]["id"]

        txs = db.fetch_transactions(
            type_filter=None if tf == "all" else tf,
            category_id=cat_id,
            search=search or None,
        )
        for row in tree.get_children():
            tree.delete(row)
        for tx in txs:
            sign = "+" if tx["type"] == "income" else "−"
            tree.insert("", "end", iid=str(tx["id"]),
                        values=(
                            tx["date"],
                            tx["type"].capitalize(),
                            tx.get("category") or "—",
                            tx.get("description") or "",
                            f"{sign} {tx['amount']:,.0f}",
                        ),
                        tags=(tx["type"],))
        tree.tag_configure("income",  foreground=GREEN)
        tree.tag_configure("expense", foreground=RED)

        # Keep row count
        self._tx_data = {str(tx["id"]): tx for tx in txs}

    def _reset_filters(self, search_box, cat_combo, tree, cats):
        self._search_var.set("")
        self._type_filter_var.set("all")
        self._cat_filter_var.set("All categories")
        cat_combo.set("All categories")
        self._load_tx_table(tree, cats)

    def _edit_tx(self, tree: ttk.Treeview):
        sel = tree.selection()
        if not sel:
            return
        tx = self._tx_data.get(sel[0])
        if tx:
            self._show_add_transaction(prefill=tx)

    def _delete_tx(self, tree: ttk.Treeview):
        sel = tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Delete", "Delete this transaction?"):
            db.delete_transaction(int(sel[0]))
            self._show_transactions()

    def _export_transactions_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Transactions",
        )
        if not path:
            return
        txs = db.fetch_transactions()
        utils.export_transactions_csv(txs, path)
        messagebox.showinfo("Exported", f"Transactions saved to:\n{path}")

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    def _show_analytics(self):
        self._highlight_nav(3)
        self._clear_content()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))
        _label(header, "Analytics", size=22, weight="bold").pack(side="left")

        trend   = db.monthly_trend(12)
        now     = datetime.now()
        summary = db.monthly_summary(now.year, now.month)

        # Net savings line
        line_card = _card(self.content)
        line_card.pack(fill="x", padx=28, pady=(4, 8))
        _label(line_card, "Net Savings Trend (12 months)", size=13,
               weight="bold").pack(anchor="w", padx=16, pady=(12, 4))
        if trend:
            fig = utils.chart_net_line(trend)
            _embed_figure(fig, line_card, padx=12, pady=(0, 12))
        else:
            _label(line_card, "No data yet", color=SUBTEXT).pack(pady=16)

        # Donut row
        donuts_row = ctk.CTkFrame(self.content, fg_color="transparent")
        donuts_row.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        donuts_row.grid_columnconfigure(0, weight=1, uniform="d")
        donuts_row.grid_columnconfigure(1, weight=1, uniform="d")
        donuts_row.grid_rowconfigure(0, weight=1)

        for col, type_ in enumerate(("income", "expense")):
            card = _card(donuts_row)
            card.grid(row=0, column=col, padx=6, sticky="nsew")
            if summary["by_category"]:
                fig = utils.chart_category_donut(summary["by_category"], type_)
                _embed_figure(fig, card, padx=8, pady=8)
            else:
                _label(card, "No data yet", color=SUBTEXT).pack(expand=True)

    # ========================================================================
    # MONTHLY SUMMARY
    # ========================================================================

    def _show_monthly_summary(self):
        self._highlight_nav(4)
        self._clear_content()

        now = datetime.now()
        self._sum_year  = ctk.IntVar(value=now.year)
        self._sum_month = ctk.IntVar(value=now.month)

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))
        _label(header, "Monthly Summary", size=22, weight="bold").pack(side="left")

        # Month picker
        picker = ctk.CTkFrame(header, fg_color=SURFACE2, corner_radius=8)
        picker.pack(side="right")

        months = [calendar.month_abbr[i] for i in range(1, 13)]
        year_entry = _entry(picker, width=70)
        year_entry.pack(side="left", padx=8, pady=6)
        year_entry.insert(0, str(now.year))

        month_combo = _combo(picker, months, width=90)
        month_combo.pack(side="left", pady=6)
        month_combo.set(calendar.month_abbr[now.month])

        def _load():
            try:
                yr = int(year_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Enter a valid year.")
                return
            mn = months.index(month_combo.get()) + 1
            self._render_monthly_summary(yr, mn, summary_frame)

        _button(picker, "Load", _load, width=70).pack(side="left", padx=8, pady=6)

        # Summary frame
        summary_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        summary_frame.pack(fill="both", expand=True, padx=28, pady=4)
        self._render_monthly_summary(now.year, now.month, summary_frame)

    def _render_monthly_summary(self, year: int, month: int, container):
        for w in container.winfo_children():
            w.destroy()

        summary = db.monthly_summary(year, month)
        month_label = datetime(year, month, 1).strftime("%B %Y")

        # KPI row
        kpi_row = ctk.CTkFrame(container, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(8, 12))
        for c in range(3):
            kpi_row.grid_columnconfigure(c, weight=1, uniform="sk")

        kpis = [
            ("Income",  f"PKR {summary['income']:,.0f}",  GREEN),
            ("Expense", f"PKR {summary['expense']:,.0f}", RED),
            ("Net",     f"PKR {summary['net']:,.0f}",
             GREEN if summary["net"] >= 0 else RED),
        ]
        for col, (t, v, c) in enumerate(kpis):
            card = _card(kpi_row)
            card.grid(row=0, column=col, padx=6, sticky="ew")
            _label(card, t, size=11, color=SUBTEXT).pack(anchor="w", padx=14, pady=(12, 2))
            _label(card, v, size=20, weight="bold", color=c).pack(anchor="w", padx=14, pady=(0, 12))

        # Category breakdown table
        table_card = _card(container)
        table_card.pack(fill="both", expand=True, pady=(0, 4))
        hrow = ctk.CTkFrame(table_card, fg_color="transparent")
        hrow.pack(fill="x", padx=16, pady=(12, 6))
        _label(hrow, f"Category Breakdown — {month_label}", size=13, weight="bold").pack(side="left")
        _button(hrow, "⬇ Export CSV",
                lambda: self._export_summary_csv(summary, year, month),
                fg=SURFACE2, hover=BORDER, width=120).pack(side="right")

        if not summary["by_category"]:
            _label(table_card, "No transactions for this month.", color=SUBTEXT).pack(pady=20)
            return

        # Header row
        hr = ctk.CTkFrame(table_card, fg_color=SURFACE2, height=32)
        hr.pack(fill="x", padx=16, pady=(0, 4))
        for text, w in [("Category", 200), ("Type", 90), ("Amount", 140)]:
            _label(hr, text, size=11, color=SUBTEXT, width=w, anchor="w").pack(
                side="left", padx=8, pady=6)

        scroll_frame = ctk.CTkScrollableFrame(table_card, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        total_inc = sum(r["total"] for r in summary["by_category"] if r["type"] == "income") or 1
        total_exp = sum(r["total"] for r in summary["by_category"] if r["type"] == "expense") or 1

        for row in summary["by_category"]:
            rframe = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            rframe.pack(fill="x", pady=3)
            color = GREEN if row["type"] == "income" else RED
            cat_color = row.get("color") or color
            _label(rframe, "●", size=10, color=cat_color, width=14).pack(side="left")
            _label(rframe, row["name"] or "—", size=12, width=186,
                   anchor="w").pack(side="left", padx=(4, 0))
            _label(rframe, row["type"].capitalize(), size=11, color=SUBTEXT,
                   width=90, anchor="w").pack(side="left", padx=8)
            _label(rframe, f"PKR {row['total']:,.0f}", size=12,
                   weight="bold", color=color, width=130, anchor="w").pack(side="left")

            # Mini bar
            denom  = total_inc if row["type"] == "income" else total_exp
            pct    = row["total"] / denom
            bar_bg = ctk.CTkFrame(rframe, fg_color=BORDER, height=6,
                                  width=120, corner_radius=3)
            bar_bg.pack(side="left", padx=8)
            bar_bg.pack_propagate(False)
            ctk.CTkFrame(bar_bg, fg_color=cat_color, height=6,
                         width=max(4, int(120 * pct)),
                         corner_radius=3).place(x=0, y=0)

    def _export_summary_csv(self, summary: dict, year: int, month: int):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export Summary",
            initialfile=f"summary_{year}_{month:02d}.csv",
        )
        if not path:
            return
        utils.export_summary_csv(summary, year, month, path)
        messagebox.showinfo("Exported", f"Summary saved to:\n{path}")

    # ========================================================================
    # CATEGORIES
    # ========================================================================

    def _show_categories(self):
        self._highlight_nav(5)
        self._clear_content()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(24, 8))
        _label(header, "Categories", size=22, weight="bold").pack(side="left")

        cats = db.fetch_categories()
        income_cats  = [c for c in cats if c["type"] == "income"]
        expense_cats = [c for c in cats if c["type"] == "expense"]

        # Add form
        add_card = _card(self.content)
        add_card.pack(fill="x", padx=28, pady=(4, 8))
        _label(add_card, "New Category", size=13, weight="bold").pack(
            anchor="w", padx=16, pady=(12, 6))
        form_row = ctk.CTkFrame(add_card, fg_color="transparent")
        form_row.pack(fill="x", padx=16, pady=(0, 14))
        name_entry = _entry(form_row, "Category name", width=200)
        name_entry.pack(side="left", padx=(0, 10))
        type_seg_var = ctk.StringVar(value="expense")
        type_seg = ctk.CTkSegmentedButton(
            form_row, values=["income", "expense"], variable=type_seg_var,
            fg_color=SURFACE2, selected_color=ACCENT, selected_hover_color=ACCENT2,
            unselected_color=SURFACE2, unselected_hover_color=BORDER,
            text_color=TEXT, font=("Inter", 11), corner_radius=6, height=32,
        )
        type_seg.pack(side="left", padx=4)

        def _add_cat():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Category name cannot be empty.")
                return
            db.add_category(name, type_seg_var.get())
            self._show_categories()

        _button(form_row, "Add", _add_cat, width=80).pack(side="left", padx=10)

        # Lists
        lists_row = ctk.CTkFrame(self.content, fg_color="transparent")
        lists_row.pack(fill="both", expand=True, padx=28, pady=(0, 18))
        lists_row.grid_columnconfigure(0, weight=1, uniform="cl")
        lists_row.grid_columnconfigure(1, weight=1, uniform="cl")
        lists_row.grid_rowconfigure(0, weight=1)

        for col, (label, cat_list, color) in enumerate([
            ("Income Categories",  income_cats,  GREEN),
            ("Expense Categories", expense_cats, RED),
        ]):
            card = _card(lists_row)
            card.grid(row=0, column=col, padx=6, sticky="nsew")
            _label(card, label, size=13, weight="bold", color=color).pack(
                anchor="w", padx=16, pady=(12, 6))
            scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            for cat in cat_list:
                row = ctk.CTkFrame(scroll, fg_color=SURFACE2, corner_radius=8)
                row.pack(fill="x", pady=3)
                _label(row, "●", size=10, color=cat["color"]).pack(side="left", padx=8, pady=8)
                _label(row, cat["name"], size=12).pack(side="left", fill="x", expand=True)
                _button(row, "✕", lambda cid=cat["id"]: self._del_cat(cid),
                        fg="transparent", hover=RED, width=30,
                        text_color=SUBTEXT).pack(side="right", padx=8)

    def _del_cat(self, cat_id: int):
        if messagebox.askyesno("Delete", "Delete this category?\nTransactions will be uncategorized."):
            db.delete_category(cat_id)
            self._show_categories()