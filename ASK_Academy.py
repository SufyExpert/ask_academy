"""
ASK Academy School Management System — Enhanced Edition
Full multi-filter system across all screens, improved UI, comprehensive error handling.
Azure SQL database via pyodbc.
"""

import threading
import time
from tkinter import ttk, messagebox
import customtkinter as ctk
import pyodbc
from datetime import datetime, date
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import os
import ast

# ── App-wide color constants ─────────────────────────────────────────────────
DARK_NAVY   = "#1B2A4A"
MID_BLUE    = "#2563EB"
ACCENT      = "#3B82F6"
LIGHT_BG    = "#F0F4FA"
CARD_BG     = "#FFFFFF"
TEXT_DARK   = "#1E293B"
TEXT_MUTED  = "#64748B"
SUCCESS     = "#10B981"
DANGER      = "#EF4444"
WARNING     = "#F59E0B"
BORDER      = "#E2E8F0"
NAV_DIVIDER = "#334E7A"
CARD_SHADOW = "#D1D9E6"
FILTER_BG   = "#EEF2FF"
FILTER_ACT  = "#DBEAFE"

# ── Azure SQL connection string ──────────────────────────────────────────────
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=tcp:ask-academy1.database.windows.net,1433;"
    "DATABASE=ASK_Academy;"
    "UID=sufyan;"
    "PWD=sufysufysufy0!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def styled_treeview(parent):
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Custom.Treeview",
                    background=CARD_BG, foreground=TEXT_DARK,
                    rowheight=32, fieldbackground=CARD_BG,
                    font=("Segoe UI", 11))
    style.configure("Custom.Treeview.Heading",
                    background=DARK_NAVY, foreground="white",
                    font=("Segoe UI", 11, "bold"), relief="flat",
                    padding=(8, 6))
    style.map("Custom.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])
    tree = ttk.Treeview(parent, style="Custom.Treeview", show="headings")
    tree.tag_configure("oddrow",  background="#F5F8FF")
    tree.tag_configure("evenrow", background=CARD_BG)
    return tree


def card_frame(parent, **kwargs):
    shadow = ctk.CTkFrame(parent, fg_color=CARD_SHADOW, corner_radius=12, border_width=0)
    inner  = ctk.CTkFrame(shadow, fg_color=CARD_BG, corner_radius=10,
                          border_width=1, border_color=BORDER, **kwargs)
    inner.pack(fill="both", expand=True, padx=1, pady=(0, 2))
    inner._shadow_frame = shadow
    return inner


def shadow_card(parent, **kwargs):
    shadow = ctk.CTkFrame(parent, fg_color=CARD_SHADOW, corner_radius=12)
    inner  = ctk.CTkFrame(shadow, fg_color=CARD_BG, corner_radius=10,
                          border_width=1, border_color=BORDER, **kwargs)
    inner.pack(fill="both", expand=True, padx=1, pady=(0, 2))
    return shadow, inner


def primary_btn(parent, text, command, width=130, fg=MID_BLUE):
    return ctk.CTkButton(parent, text=text, command=command,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         fg_color=fg, hover_color=ACCENT,
                         corner_radius=8, height=36, width=width,
                         border_width=0)


def danger_btn(parent, text, command, width=110):
    return ctk.CTkButton(parent, text=text, command=command,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         fg_color=DANGER, hover_color="#DC2626",
                         corner_radius=8, height=36, width=width)


def warning_btn(parent, text, command, width=110):
    return ctk.CTkButton(parent, text=text, command=command,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         fg_color=WARNING, hover_color="#D97706",
                         corner_radius=8, height=36, width=width,
                         text_color="white")


def section_label(parent, text):
    return ctk.CTkLabel(parent, text=text,
                        font=ctk.CTkFont("Segoe UI", 20, "bold"),
                        text_color=DARK_NAVY)


def filter_tag_btn(parent, label, on_remove):
    """Pill-shaped active filter tag with × remove button."""
    frame = ctk.CTkFrame(parent, fg_color=FILTER_ACT, corner_radius=20,
                         border_width=1, border_color=ACCENT)
    ctk.CTkLabel(frame, text=label, font=ctk.CTkFont("Segoe UI", 10, "bold"),
                 text_color=MID_BLUE, fg_color="transparent").pack(side="left", padx=(10, 4), pady=4)
    ctk.CTkButton(frame, text="×", width=20, height=20, corner_radius=10,
                  fg_color="transparent", hover_color="#BFDBFE",
                  text_color=MID_BLUE, font=ctk.CTkFont("Segoe UI", 13, "bold"),
                  command=on_remove).pack(side="left", padx=(0, 6))
    return frame


# ── PDF Export helper ────────────────────────────────────────────────────────

def export_pdf(title, columns, rows, filename="report.pdf"):
    try:
        doc    = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        elements.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
            styles["Normal"]))
        elements.append(Spacer(1, 16))

        data = [list(columns)] + [list(map(str, r)) for r in rows]
        col_count = len(columns)
        col_width  = 480 / col_count

        table = Table(data, colWidths=[col_width] * col_count)
        table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(DARK_NAVY)),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  10),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  10),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4FB")]),
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 9),
            ("GRID",          (0, 0), (-1, -1), 0.4, colors.HexColor(BORDER)),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ]))
        elements.append(table)
        doc.build(elements)
        if os.name == "nt":
            os.startfile(filename)
        else:
            os.system(f"xdg-open {filename}")
    except Exception as e:
        messagebox.showerror("PDF Export Error", str(e))


# ── Filter Panel Widget ──────────────────────────────────────────────────────

class FilterPanel:
    """
    A collapsible multi-filter panel. Pass a list of filter_defs:
    Each def is a dict:
        { "label": str, "type": "text"|"dropdown"|"date_range"|"number_range",
          "column": str,    # DB column name used in WHERE
          "options": list,  # for dropdown type
          "options_fn": callable  # lazy-loaded options
        }
    """

    def __init__(self, parent, filter_defs, on_apply, on_clear):
        self.filter_defs = filter_defs
        self.on_apply    = on_apply
        self.on_clear    = on_clear
        self.active_filters = {}   # column → (label, value_tuple)
        self._widgets   = {}
        self._expanded  = True

        # Outer wrapper
        self._wrapper = ctk.CTkFrame(parent, fg_color="transparent")

        # Header bar (always visible)
        self._hdr = ctk.CTkFrame(self._wrapper, fg_color=DARK_NAVY,
                                 corner_radius=10, height=44)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)

        ctk.CTkLabel(self._hdr, text="⚙  Filters",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color="white", fg_color="transparent").pack(
            side="left", padx=14, pady=10)

        self._count_lbl = ctk.CTkLabel(self._hdr, text="",
                                       font=ctk.CTkFont("Segoe UI", 10),
                                       text_color="#93C5FD",
                                       fg_color="transparent")
        self._count_lbl.pack(side="left", padx=4)

        # Right-side header buttons
        rbtn_frame = ctk.CTkFrame(self._hdr, fg_color="transparent")
        rbtn_frame.pack(side="right", padx=8)

        primary_btn(rbtn_frame, "Apply Filters", self._apply, width=120,
                    fg=SUCCESS).pack(side="left", padx=4, pady=6)
        primary_btn(rbtn_frame, "Clear All", self._clear_all, width=90,
                    fg="#64748B").pack(side="left", padx=4, pady=6)

        toggle_btn = ctk.CTkButton(rbtn_frame, text="▲", width=32, height=28,
                                   fg_color="transparent", hover_color="#334E7A",
                                   text_color="white", corner_radius=6,
                                   font=ctk.CTkFont("Segoe UI", 12, "bold"),
                                   command=self._toggle)
        toggle_btn.pack(side="left", padx=4, pady=6)
        self._toggle_btn = toggle_btn

        # Body (collapsible)
        self._body = ctk.CTkFrame(self._wrapper, fg_color="#F8FAFF",
                                  corner_radius=0,
                                  border_width=1, border_color=BORDER)
        self._body.pack(fill="x")
        self._build_filter_rows()

        # Active filter tags bar
        self._tags_outer = ctk.CTkFrame(self._wrapper, fg_color="transparent")
        self._tags_outer.pack(fill="x", pady=(4, 0))
        self._tags_frame = ctk.CTkFrame(self._tags_outer, fg_color="transparent")
        self._tags_frame.pack(fill="x")

    def pack(self, **kwargs):
        self._wrapper.pack(**kwargs)

    def grid(self, **kwargs):
        self._wrapper.grid(**kwargs)

    def _toggle(self):
        if self._expanded:
            self._body.pack_forget()
            self._toggle_btn.configure(text="▼")
        else:
            self._body.pack(fill="x")
            self._toggle_btn.configure(text="▲")
        self._expanded = not self._expanded

    def _build_filter_rows(self):
        # Grid layout for filter fields
        row_frame = ctk.CTkFrame(self._body, fg_color="transparent")
        row_frame.pack(fill="x", padx=14, pady=10)

        col = 0
        row = 0
        max_cols = 4  # 4 filters per row

        for i, fd in enumerate(self.filter_defs):
            cell = ctk.CTkFrame(row_frame, fg_color="transparent")
            cell.grid(row=row, column=col, padx=8, pady=6, sticky="w")

            ctk.CTkLabel(cell, text=fd["label"],
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=TEXT_MUTED).pack(anchor="w", pady=(0, 3))

            ftype = fd.get("type", "text")

            if ftype == "text":
                w = ctk.CTkEntry(cell, width=170, placeholder_text=f"Search {fd['label']}...",
                                 fg_color=CARD_BG, border_color=BORDER,
                                 corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
                w.pack()
                self._widgets[fd["label"]] = ("text", w)

            elif ftype == "dropdown":
                opts = fd.get("options", [])
                if callable(fd.get("options_fn")):
                    try:
                        opts = fd["options_fn"]()
                    except Exception:
                        opts = []
                opts = ["— Any —"] + [str(o) for o in opts if o]
                var = ctk.StringVar(value="— Any —")
                w = ctk.CTkComboBox(cell, values=opts, variable=var,
                                    width=170, fg_color=CARD_BG,
                                    border_color=BORDER, button_color=MID_BLUE,
                                    corner_radius=8, state="readonly",
                                    font=ctk.CTkFont("Segoe UI", 11))
                w.pack()
                self._widgets[fd["label"]] = ("dropdown", var, opts)

            elif ftype == "date_range":
                sub = ctk.CTkFrame(cell, fg_color="transparent")
                sub.pack()
                from_e = ctk.CTkEntry(sub, width=115, placeholder_text="From YYYY-MM-DD",
                                      fg_color=CARD_BG, border_color=BORDER,
                                      corner_radius=8, font=ctk.CTkFont("Segoe UI", 10))
                from_e.pack(side="left", padx=(0, 4))
                to_e = ctk.CTkEntry(sub, width=115, placeholder_text="To YYYY-MM-DD",
                                    fg_color=CARD_BG, border_color=BORDER,
                                    corner_radius=8, font=ctk.CTkFont("Segoe UI", 10))
                to_e.pack(side="left")
                self._widgets[fd["label"]] = ("date_range", from_e, to_e)

            elif ftype == "number_range":
                sub = ctk.CTkFrame(cell, fg_color="transparent")
                sub.pack()
                min_e = ctk.CTkEntry(sub, width=80, placeholder_text="Min",
                                     fg_color=CARD_BG, border_color=BORDER,
                                     corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
                min_e.pack(side="left", padx=(0, 4))
                ctk.CTkLabel(sub, text="–", text_color=TEXT_MUTED,
                             font=ctk.CTkFont("Segoe UI", 12)).pack(side="left", padx=2)
                max_e = ctk.CTkEntry(sub, width=80, placeholder_text="Max",
                                     fg_color=CARD_BG, border_color=BORDER,
                                     corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
                max_e.pack(side="left", padx=(4, 0))
                self._widgets[fd["label"]] = ("number_range", min_e, max_e)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def _apply(self):
        """Read all widget values, build active_filters dict."""
        self.active_filters = {}
        errors = []

        for fd in self.filter_defs:
            lbl   = fd["label"]
            col   = fd["column"]
            ftype = fd.get("type", "text")
            w_info = self._widgets.get(lbl)
            if not w_info:
                continue

            if ftype == "text":
                val = w_info[1].get().strip()
                if val:
                    self.active_filters[col] = ("like", val, f"{lbl}: \"{val}\"")

            elif ftype == "dropdown":
                val = w_info[1].get()
                if val and val != "— Any —":
                    self.active_filters[col] = ("eq", val, f"{lbl}: {val}")

            elif ftype == "date_range":
                f_val = w_info[1].get().strip()
                t_val = w_info[2].get().strip()
                if f_val or t_val:
                    # Validate dates
                    for v in [f_val, t_val]:
                        if v:
                            try:
                                datetime.strptime(v, "%Y-%m-%d")
                            except ValueError:
                                errors.append(f"{lbl}: Date must be YYYY-MM-DD format")
                    if not errors:
                        self.active_filters[col] = ("date_range", f_val, t_val,
                                                     f"{lbl}: {f_val or '...'} → {t_val or '...'}")

            elif ftype == "number_range":
                min_val = w_info[1].get().strip()
                max_val = w_info[2].get().strip()
                if min_val or max_val:
                    for v, name in [(min_val, "Min"), (max_val, "Max")]:
                        if v:
                            try:
                                float(v)
                            except ValueError:
                                errors.append(f"{lbl} {name}: Must be a number")
                    if not errors:
                        self.active_filters[col] = ("number_range", min_val, max_val,
                                                     f"{lbl}: {min_val or '0'} – {max_val or '∞'}")

        if errors:
            messagebox.showerror("Filter Validation Error",
                                 "Please fix the following errors:\n\n• " + "\n• ".join(errors))
            return

        self._update_tags()
        self._update_count()
        self.on_apply(self.active_filters)

    def _clear_all(self):
        if self.active_filters:
            if not messagebox.askyesno("Clear Filters",
                                       "Remove all active filters and show all records?"):
                return
        # Reset all widgets
        for fd in self.filter_defs:
            lbl   = fd["label"]
            ftype = fd.get("type", "text")
            w_info = self._widgets.get(lbl)
            if not w_info:
                continue
            if ftype == "text":
                w_info[1].delete(0, "end")
            elif ftype == "dropdown":
                w_info[1].set("— Any —")
            elif ftype == "date_range":
                w_info[1].delete(0, "end")
                w_info[2].delete(0, "end")
            elif ftype == "number_range":
                w_info[1].delete(0, "end")
                w_info[2].delete(0, "end")

        self.active_filters = {}
        self._update_tags()
        self._update_count()
        self.on_clear()

    def _remove_filter(self, col):
        if col in self.active_filters:
            # Also reset the widget
            for fd in self.filter_defs:
                if fd["column"] == col:
                    self._reset_widget(fd)
                    break
            del self.active_filters[col]
        self._update_tags()
        self._update_count()
        self.on_apply(self.active_filters)

    def _reset_widget(self, fd):
        lbl   = fd["label"]
        ftype = fd.get("type", "text")
        w_info = self._widgets.get(lbl)
        if not w_info:
            return
        if ftype == "text":
            w_info[1].delete(0, "end")
        elif ftype == "dropdown":
            w_info[1].set("— Any —")
        elif ftype == "date_range":
            w_info[1].delete(0, "end")
            w_info[2].delete(0, "end")
        elif ftype == "number_range":
            w_info[1].delete(0, "end")
            w_info[2].delete(0, "end")

    def _update_tags(self):
        for w in self._tags_frame.winfo_children():
            w.destroy()
        if self.active_filters:
            ctk.CTkLabel(self._tags_frame, text="Active:",
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=TEXT_MUTED).pack(side="left", padx=(0, 6), pady=2)
        for col, info in self.active_filters.items():
            tag_label = info[-1]  # last element is display label
            _col = col  # capture for lambda
            t = filter_tag_btn(self._tags_frame, tag_label,
                                lambda c=_col: self._remove_filter(c))
            t.pack(side="left", padx=3, pady=2)

    def _update_count(self):
        n = len(self.active_filters)
        self._count_lbl.configure(
            text=f"({n} active)" if n > 0 else "")

    def build_where_clause(self, active_filters=None):
        """Return (where_str, params_list) from active_filters."""
        if active_filters is None:
            active_filters = self.active_filters
        clauses = []
        params  = []
        for col, info in active_filters.items():
            kind = info[0]
            if kind == "like":
                clauses.append(f"CAST([{col}] AS NVARCHAR(MAX)) LIKE ?")
                params.append(f"%{info[1]}%")
            elif kind == "eq":
                clauses.append(f"[{col}] = ?")
                params.append(info[1])
            elif kind == "date_range":
                if info[1]:
                    clauses.append(f"CONVERT(DATE,[{col}]) >= ?")
                    params.append(info[1])
                if info[2]:
                    clauses.append(f"CONVERT(DATE,[{col}]) <= ?")
                    params.append(info[2])
            elif kind == "number_range":
                if info[1]:
                    clauses.append(f"[{col}] >= ?")
                    params.append(float(info[1]))
                if info[2]:
                    clauses.append(f"[{col}] <= ?")
                    params.append(float(info[2]))
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        return where, params


# ── Main Application ─────────────────────────────────────────────────────────

class ASKAcademyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASK Academy — School Management System")
        self.root.geometry("1380x860")
        self.root.minsize(1100, 700)
        self.root.configure(bg=LIGHT_BG)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.conn   = None
        self.cursor = None
        self.current_user_role = None

        self._show_loading()
        threading.Thread(target=self._connect, daemon=True).start()

    # ── Connection ────────────────────────────────────────────────────────

    def _connect(self):
        start = time.time()
        try:
            self.conn   = pyodbc.connect(CONN_STR)
            self.cursor = self.conn.cursor()
            success = True
        except Exception as e:
            print(f"Connection failed: {e}")
            success = False
        finally:
            elapsed = time.time() - start
            if elapsed < 2.5:
                time.sleep(2.5 - elapsed)

        if success:
            self.root.after(0, lambda: (self._loading_win.destroy(), self._login()))
        else:
            self.root.after(0, lambda: (
                messagebox.showerror("Connection Failed",
                                     "Could not connect to the Azure database.\n"
                                     "Please check your internet connection and try again."),
                self.root.destroy()
            ))

    def _show_loading(self):
        self._loading_win = ctk.CTkToplevel(self.root)
        self._loading_win.title("Connecting")
        self._loading_win.geometry("340x130")
        self._loading_win.resizable(False, False)
        self._loading_win.transient(self.root)
        self._loading_win.grab_set()
        self._loading_win.configure(fg_color=CARD_BG)

        w = self._loading_win
        w.update_idletasks()
        x = (w.winfo_screenwidth()  // 2) - 170
        y = (w.winfo_screenheight() // 2) - 65
        w.geometry(f"340x130+{x}+{y}")

        ctk.CTkLabel(w, text="ASK Academy",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=DARK_NAVY).pack(pady=(20, 4))
        ctk.CTkLabel(w, text="Connecting to database, please wait...",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=TEXT_MUTED).pack()
        bar = ctk.CTkProgressBar(w, mode="indeterminate", width=280,
                                 fg_color=BORDER, progress_color=ACCENT)
        bar.pack(pady=14)
        bar.start()

    # ── Login ─────────────────────────────────────────────────────────────

    def _login(self):
        self._clear()
        self.root.state("zoomed")

        outer = ctk.CTkFrame(self.root, fg_color=LIGHT_BG)
        outer.pack(expand=True, fill="both")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        shadow_wrap = ctk.CTkFrame(outer, fg_color=CARD_SHADOW, corner_radius=16)
        shadow_wrap.grid(row=0, column=0)
        card = ctk.CTkFrame(shadow_wrap, fg_color=CARD_BG, corner_radius=14,
                            border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=2, pady=(0, 3))

        ctk.CTkFrame(card, fg_color=MID_BLUE, corner_radius=0, height=5).pack(fill="x", side="top")

        ctk.CTkLabel(card, text="ASK Academy",
                     font=ctk.CTkFont("Segoe UI", 32, "bold"),
                     text_color=DARK_NAVY).pack(pady=(32, 4), padx=60)
        ctk.CTkLabel(card, text="School Management System",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=TEXT_MUTED).pack(pady=(0, 28))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(padx=50, pady=4)

        def row(label, widget_fn):
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", pady=7)
            ctk.CTkLabel(r, text=label, width=95,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         anchor="e", text_color=TEXT_MUTED).pack(side="left", padx=(0, 12))
            w = widget_fn(r)
            w.pack(side="left", fill="x", expand=True)
            return w

        role_var = ctk.StringVar(value="owner")
        row("Role", lambda p: ctk.CTkComboBox(
            p, values=["owner", "staff"], variable=role_var,
            width=260, font=ctk.CTkFont("Segoe UI", 12),
            fg_color=LIGHT_BG, border_color=BORDER, button_color=MID_BLUE,
            corner_radius=8))

        user_entry = row("Username", lambda p: ctk.CTkEntry(
            p, width=260, font=ctk.CTkFont("Segoe UI", 12),
            fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8,
            placeholder_text="Enter username"))

        pass_entry = row("Password", lambda p: ctk.CTkEntry(
            p, width=260, show="*", font=ctk.CTkFont("Segoe UI", 12),
            fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8,
            placeholder_text="Enter password"))

        err_label = ctk.CTkLabel(card, text="",
                                 font=ctk.CTkFont("Segoe UI", 11),
                                 text_color=DANGER)
        err_label.pack(pady=4)

        def do_login(event=None):
            u, p, r = user_entry.get().strip(), pass_entry.get(), role_var.get()
            if not u or not p:
                err_label.configure(text="Please enter username and password.")
                return
            try:
                self.cursor.execute(
                    "SELECT role FROM Users WHERE username=? AND password=? AND role=?",
                    (u, p, r))
                res = self.cursor.fetchone()
                if res:
                    self.current_user_role = res[0]
                    self._dashboard()
                else:
                    err_label.configure(text="Invalid username, password, or role.")
            except pyodbc.Error as e:
                err_label.configure(text=f"Database error: {str(e).split(chr(10))[0]}")

        pass_entry.bind("<Return>", do_login)
        ctk.CTkButton(card, text="Sign In", command=do_login,
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=MID_BLUE, hover_color="#1D4ED8",
                      corner_radius=10, height=42, width=260).pack(pady=(8, 36))

    # ── Navigation bar ────────────────────────────────────────────────────

    def _navbar(self, active=None):
        bar = ctk.CTkFrame(self.root, fg_color=DARK_NAVY,
                           corner_radius=0, height=54)
        bar.pack(side="top", fill="x")
        bar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(bar, fg_color="#142038", corner_radius=0, width=160)
        logo_frame.pack(side="left", fill="y")
        logo_frame.pack_propagate(False)
        ctk.CTkLabel(logo_frame, text="ASK Academy",
                     font=ctk.CTkFont("Segoe UI", 14, "bold"),
                     text_color="white").pack(side="left", padx=16)

        ctk.CTkFrame(bar, width=1, fg_color=NAV_DIVIDER,
                     corner_radius=0).pack(side="left", fill="y", pady=10, padx=2)

        all_items = [
            ("Dashboard",          self._dashboard),
            ("Students",           self._screen_students),
            ("Teachers",           self._screen_teachers),
            ("Batches",            self._screen_batches),
            ("Rooms",              self._screen_rooms),
            ("Classes",            self._screen_classes),
            ("Timetable",          self._screen_timetable),
            ("Tests",              self._screen_tests),
            ("Results",            self._screen_results),
            ("Student Attendance", self._screen_attendance),
            ("Teacher Attendance", self._screen_teacher_attendance),
            ("Fees",               self._screen_fees),
            ("Salaries",           self._screen_salaries),
            ("Assets",             self._screen_assets),
            ("Maintenance",        self._screen_maintenance),
            ("Expenses",           self._screen_expenses),
            ("Audit Log",          self._screen_auditlog),
        ]

        staff_hidden = {"Fees", "Salaries", "Assets", "Maintenance", "Expenses", "Audit Log"}
        items = all_items if self.current_user_role == "owner" else [
            (t, c) for t, c in all_items if t not in staff_hidden
        ]

        scroll_frame = ctk.CTkFrame(bar, fg_color="transparent")
        scroll_frame.pack(side="left", fill="both", expand=True)

        for text, cmd in items:
            is_active = (text == active)
            btn = ctk.CTkButton(
                scroll_frame, text=text, command=cmd,
                font=ctk.CTkFont("Segoe UI", 11, "bold" if is_active else "normal"),
                fg_color=ACCENT if is_active else "transparent",
                hover_color="#1E40AF", text_color="white",
                corner_radius=6, height=34, width=0)
            btn.pack(side="left", padx=2, pady=10)

        time_label = ctk.CTkLabel(bar, text="",
                                  font=ctk.CTkFont("Segoe UI", 10),
                                  text_color="#94A3B8")
        time_label.pack(side="right", padx=8)
        self._update_clock(time_label)

        ctk.CTkButton(bar, text="Logout", command=self._confirm_logout,
                      font=ctk.CTkFont("Segoe UI", 11, "bold"),
                      fg_color="#DC2626", hover_color="#B91C1C",
                      corner_radius=6, height=30, width=76).pack(side="right", padx=10)
        return bar

    def _confirm_logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self._login()

    def _update_clock(self, label):
        try:
            label.configure(text=datetime.now().strftime("%d %b %Y  %I:%M %p"))
            self.root.after(30000, lambda: self._update_clock(label))
        except Exception:
            pass

    # ── Dashboard ─────────────────────────────────────────────────────────

    def _dashboard(self):
        self._clear()
        self._navbar("Dashboard")

        body = ctk.CTkFrame(self.root, fg_color=LIGHT_BG)
        body.pack(fill="both", expand=True, padx=20, pady=16)

        stats_row = ctk.CTkFrame(body, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))

        stat_data = [
            ("Students",  "SELECT COUNT(*) FROM dbo.Student",  MID_BLUE),
            ("Teachers",  "SELECT COUNT(*) FROM dbo.Teacher",  "#059669"),
            ("Batches",   "SELECT COUNT(*) FROM dbo.Batch",    "#7C3AED"),
            ("Rooms",     "SELECT COUNT(*) FROM dbo.Room",     "#D97706"),
            ("Classes",   "SELECT COUNT(*) FROM dbo.Class",    "#0E7490"),
        ]

        for label, query, color in stat_data:
            try:
                self.cursor.execute(query)
                count = self.cursor.fetchone()[0]
            except Exception:
                count = "—"

            shadow_w = ctk.CTkFrame(stats_row, fg_color=CARD_SHADOW, corner_radius=12)
            shadow_w.pack(side="left", expand=True, fill="both", padx=6)
            c = ctk.CTkFrame(shadow_w, fg_color=CARD_BG, corner_radius=10,
                             border_width=1, border_color=BORDER)
            c.pack(fill="both", expand=True, padx=1, pady=(0, 2))
            ctk.CTkFrame(c, fg_color=color, height=4, corner_radius=0).pack(fill="x")
            ctk.CTkLabel(c, text=str(count),
                         font=ctk.CTkFont("Segoe UI", 38, "bold"),
                         text_color=color).pack(pady=(16, 2))
            ctk.CTkLabel(c, text=label,
                         font=ctk.CTkFont("Segoe UI", 12, "bold"),
                         text_color=TEXT_MUTED).pack(pady=(0, 18))

        main_row = ctk.CTkFrame(body, fg_color="transparent")
        main_row.pack(fill="both", expand=True)

        qa_shadow = ctk.CTkFrame(main_row, fg_color=CARD_SHADOW, corner_radius=12, width=240)
        qa_shadow.pack(side="left", fill="y", padx=(0, 12))
        qa_shadow.pack_propagate(False)
        qa = ctk.CTkFrame(qa_shadow, fg_color=CARD_BG, corner_radius=10,
                          border_width=1, border_color=BORDER)
        qa.pack(fill="both", expand=True, padx=1, pady=(0, 2))
        qa.pack_propagate(False)

        hdr = ctk.CTkFrame(qa, fg_color=DARK_NAVY, corner_radius=0, height=42)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="Quick Actions",
                     font=ctk.CTkFont("Segoe UI", 12, "bold"),
                     text_color="white").pack(pady=10, padx=16, anchor="w")

        actions = [
            ("➕  Add Student",            self._popup_add_student),
            ("➕  Add Teacher",            self._popup_add_teacher),
            ("📋  Student Attendance",     self._popup_add_student_attendance),
            ("📋  Teacher Attendance",     self._popup_add_teacher_attendance),
            ("📝  Add Result",             self._popup_add_result),
            ("🧾  Print Fee Challan",      self._popup_fee_challan),
            ("📄  Export Student Report",  self._export_student_report),
            ("📄  Export Teacher Report",  self._export_teacher_report),
            ("🔍  View Audit Log",         self._screen_auditlog),
        ]

        for text, cmd in actions:
            btn = ctk.CTkButton(qa, text=text, command=cmd,
                          font=ctk.CTkFont("Segoe UI", 11),
                          fg_color="transparent", hover_color="#EFF6FF",
                          corner_radius=6, height=36, anchor="w",
                          text_color=TEXT_DARK, border_width=0)
            btn.pack(fill="x", padx=10, pady=2)

        chart_shadow = ctk.CTkFrame(main_row, fg_color=CARD_SHADOW, corner_radius=12)
        chart_shadow.pack(side="left", fill="both", expand=True)
        chart_card = ctk.CTkFrame(chart_shadow, fg_color=CARD_BG, corner_radius=10,
                                  border_width=1, border_color=BORDER)
        chart_card.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        chart_hdr = ctk.CTkFrame(chart_card, fg_color="transparent")
        chart_hdr.pack(fill="x", padx=16, pady=(14, 0))
        ctk.CTkLabel(chart_hdr, text="Student Enrollment by Year",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=DARK_NAVY).pack(side="left")
        self._draw_enrollment_chart(chart_card)

    def _draw_enrollment_chart(self, parent):
        try:
            self.cursor.execute(
                "SELECT YearOfAdmission, COUNT(*) FROM dbo.Student "
                "GROUP BY YearOfAdmission ORDER BY YearOfAdmission")
            rows = self.cursor.fetchall()
            years  = [str(r[0]) for r in rows]
            counts = [r[1] for r in rows]
        except Exception:
            years, counts = [], []

        fig, ax = plt.subplots(figsize=(7, 4), facecolor=CARD_BG)
        ax.set_facecolor("#F8FAFF")

        if years:
            bars = ax.bar(years, counts, color=MID_BLUE, width=0.5,
                          zorder=3, edgecolor="white", linewidth=1.5)
            for i, bar in enumerate(bars):
                bar.set_alpha(0.85 + 0.15 * (i / max(len(bars)-1, 1)))
            ax.bar_label(bars, padding=4, fontsize=10, color=DARK_NAVY, fontweight="bold")
        else:
            ax.text(0.5, 0.5, "No enrollment data",
                    ha="center", va="center", fontsize=12, color=TEXT_MUTED)

        ax.spines[["top","right"]].set_visible(False)
        ax.spines[["bottom","left"]].set_color(BORDER)
        ax.tick_params(colors=TEXT_MUTED, labelsize=10)
        ax.set_ylabel("Students", color=TEXT_MUTED, fontsize=10)
        ax.yaxis.grid(True, linestyle="--", alpha=0.4, color=BORDER)
        ax.set_axisbelow(True)
        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=14, pady=12)

    # ── Enhanced CRUD screen with FilterPanel ─────────────────────────────

    def _crud_screen(self, nav_label, title, columns, fields_info, queries,
                     filter_defs=None):
        """
        Reusable screen with full FilterPanel + legacy search bar.
        filter_defs: list of filter definition dicts for FilterPanel
        """
        self._clear()
        self._navbar(nav_label)

        body = ctk.CTkFrame(self.root, fg_color=LIGHT_BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        body.grid_rowconfigure(3, weight=1)
        body.grid_columnconfigure(0, weight=1)

        # Row 0: Title + buttons
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        section_label(top, title).pack(side="left")

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(side="right")

        result_count_lbl = ctk.CTkLabel(btn_frame, text="",
                                        font=ctk.CTkFont("Segoe UI", 11),
                                        text_color=TEXT_MUTED)
        result_count_lbl.pack(side="left", padx=12)

        def do_export():
            rows_data = [tree.item(i)["values"] for i in tree.get_children()]
            if not rows_data:
                messagebox.showwarning("No Data", "There is nothing to export.")
                return
            export_pdf(title, columns, rows_data,
                       f"{title.replace(' ', '_')}.pdf")

        primary_btn(btn_frame, "📄 Export PDF", do_export, width=120, fg=DARK_NAVY).pack(side="left", padx=4)
        primary_btn(btn_frame, "+ Add New",
                    lambda: self._open_form("add", fields_info, queries, None, refresh),
                    width=110).pack(side="left", padx=4)

        # Row 1: Filter panel (if filter_defs provided)
        if filter_defs:
            def apply_filters(active):
                refresh(active_filters=active)

            def clear_filters():
                refresh()

            fp = FilterPanel(body, filter_defs, apply_filters, clear_filters)
            fp.grid(row=1, column=0, sticky="ew", pady=(0, 8))
            self._active_filter_panel = fp
        else:
            self._active_filter_panel = None

        # Row 2: Quick search bar
        s_shadow = ctk.CTkFrame(body, fg_color=CARD_SHADOW, corner_radius=10)
        s_shadow.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        search_card = ctk.CTkFrame(s_shadow, fg_color=CARD_BG, corner_radius=9,
                                   border_width=1, border_color=BORDER)
        search_card.pack(fill="both", expand=True, padx=1, pady=(0, 2))
        sf = ctk.CTkFrame(search_card, fg_color="transparent")
        sf.pack(padx=14, pady=8, anchor="w")

        ctk.CTkLabel(sf, text="🔍  Quick Search:",
                     text_color=TEXT_MUTED,
                     font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(0, 6))

        searchable = [f[0] for f in fields_info if f[1] == "entry"]
        field_cb = ctk.CTkComboBox(sf, values=searchable or ["—"], state="readonly",
                                   width=150, fg_color=LIGHT_BG, border_color=BORDER,
                                   corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
        field_cb.pack(side="left", padx=4)
        if searchable:
            field_cb.set(searchable[0])

        term_entry = ctk.CTkEntry(sf, width=240,
                                  placeholder_text="Type to search...",
                                  fg_color=LIGHT_BG, border_color=BORDER,
                                  corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
        term_entry.pack(side="left", padx=4)

        primary_btn(sf, "Search",
                    lambda: refresh(field=field_cb.get(), term=term_entry.get()),
                    width=80).pack(side="left", padx=4)
        primary_btn(sf, "Clear",
                    lambda: (term_entry.delete(0, "end"), refresh()),
                    width=70, fg=TEXT_MUTED).pack(side="left", padx=4)

        term_entry.bind("<Return>",
                        lambda e: refresh(field=field_cb.get(), term=term_entry.get()))

        # Row 3: Table
        t_shadow = ctk.CTkFrame(body, fg_color=CARD_SHADOW, corner_radius=10)
        t_shadow.grid(row=3, column=0, sticky="nsew")
        t_shadow.grid_rowconfigure(0, weight=1)
        t_shadow.grid_columnconfigure(0, weight=1)
        tree_card = ctk.CTkFrame(t_shadow, fg_color=CARD_BG, corner_radius=9,
                                 border_width=1, border_color=BORDER)
        tree_card.grid(row=0, column=0, sticky="nsew", padx=1, pady=(0, 2))
        tree_card.grid_rowconfigure(0, weight=1)
        tree_card.grid_columnconfigure(0, weight=1)

        tree = styled_treeview(tree_card)
        tree["columns"] = columns
        for col in columns:
            tree.heading(col, text=col,
                         command=lambda c=col: sort_tree(c))
            tree.column(col, width=max(100, 700 // len(columns)), anchor="center")
        tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        vsb = ctk.CTkScrollbar(tree_card, command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vsb.set)

        hsb = ctk.CTkScrollbar(tree_card, orientation="horizontal", command=tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        tree.configure(xscrollcommand=hsb.set)

        # Column sort state
        _sort_state = {}

        def sort_tree(col_name):
            items = [(tree.set(k, col_name), k) for k in tree.get_children("")]
            asc   = not _sort_state.get(col_name, False)
            _sort_state[col_name] = asc
            try:
                items.sort(key=lambda x: float(x[0]) if x[0].replace('.','').replace('-','').isdigit() else x[0].lower(),
                           reverse=not asc)
            except Exception:
                items.sort(key=lambda x: x[0].lower(), reverse=not asc)
            for idx, (_, k) in enumerate(items):
                tree.move(k, "", idx)
            # Update row tags after sort
            for i, k in enumerate(tree.get_children()):
                tree.item(k, tags=("evenrow" if i % 2 == 0 else "oddrow",))

        def refresh(field="", term="", active_filters=None):
            for row in tree.get_children():
                tree.delete(row)
            try:
                base_q = queries["select"]
                params = []

                # Build conditions list
                conditions = []

                # From FilterPanel
                if active_filters is None and self._active_filter_panel:
                    active_filters = self._active_filter_panel.active_filters

                if active_filters:
                    fp_where, fp_params = FilterPanel(
                        body, [], lambda x: None, lambda: None
                    ).build_where_clause.__func__(
                        FilterPanel.__new__(FilterPanel), active_filters
                    ) if False else ("", [])
                    # Use the panel's own method if available
                    if self._active_filter_panel:
                        fp_where, fp_params = self._active_filter_panel.build_where_clause(active_filters)
                        if fp_where:
                            conditions.append(fp_where.replace("WHERE ", ""))
                            params.extend(fp_params)

                # From quick search
                if field and term and searchable:
                    conditions.append(f"CAST([{field}] AS NVARCHAR(MAX)) LIKE ?")
                    params.append(f"%{term}%")

                if conditions:
                    base_q += " WHERE " + " AND ".join(conditions)

                self.cursor.execute(base_q, params)
                rows_fetched = self.cursor.fetchall()

                for i, row in enumerate(rows_fetched):
                    tag = "evenrow" if i % 2 == 0 else "oddrow"
                    tree.insert("", "end",
                                values=[str(v) if v is not None else "" for v in row],
                                tags=(tag,))

                count = len(rows_fetched)
                result_count_lbl.configure(
                    text=f"Showing {count} record{'s' if count != 1 else ''}",
                    text_color=SUCCESS if count > 0 else DANGER)

            except pyodbc.Error as e:
                messagebox.showerror("Database Error",
                                     f"Failed to load records:\n{str(e).split(chr(10))[0]}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tree.bind("<Double-1>",
                  lambda e: self._on_tree_double_click(e, tree, fields_info, queries, refresh))
        refresh()

    def _on_tree_double_click(self, event, tree, fields_info, queries, refresh_fn):
        sel = tree.selection()
        if sel:
            data = tree.item(sel[0])["values"]
            self._open_form("edit", fields_info, queries, data, refresh_fn)

    def _open_form(self, mode, fields_info, queries, record_data, refresh_fn):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Record" if mode == "add" else "Edit Record")
        popup.geometry("480x" + str(80 + len(fields_info) * 58 + 120))
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x", side="top")
        icon = "✏️" if mode == "edit" else "➕"
        ctk.CTkLabel(hdr_bar,
                     text=f"{icon}  {'Add New Record' if mode == 'add' else 'Edit Record'}",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        f_shadow = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        f_shadow.pack(padx=20, pady=12, fill="x")
        form = ctk.CTkFrame(f_shadow, fg_color=CARD_BG, corner_radius=9,
                            border_width=1, border_color=BORDER)
        form.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        widgets = {}
        pk_count = queries["delete"].count("?")

        for i, (label, ftype, options, default) in enumerate(fields_info):
            row_f = ctk.CTkFrame(form, fg_color="transparent")
            row_f.pack(fill="x", padx=14, pady=6)
            ctk.CTkLabel(row_f, text=label + ":", width=140,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=TEXT_MUTED, anchor="e").pack(side="left", padx=(0, 10))

            if ftype == "entry":
                w = ctk.CTkEntry(row_f, width=240, corner_radius=8,
                                 fg_color=LIGHT_BG, border_color=BORDER,
                                 font=ctk.CTkFont("Segoe UI", 11))
            else:
                opts = options() if callable(options) else (options or [])
                w = ctk.CTkComboBox(row_f, values=opts, width=244, corner_radius=8,
                                    fg_color=LIGHT_BG, border_color=BORDER,
                                    button_color=MID_BLUE, state="readonly",
                                    font=ctk.CTkFont("Segoe UI", 11))
            w.pack(side="left")
            widgets[label] = w

            if mode == "edit" and record_data:
                val = str(record_data[i]) if record_data[i] is not None else ""
                if isinstance(w, ctk.CTkComboBox):
                    w.set(val)
                else:
                    w.insert(0, val)
                if i < pk_count:
                    w.configure(state="disabled")
            elif mode == "add" and default is not None:
                if isinstance(w, ctk.CTkEntry):
                    w.insert(0, str(default))
                else:
                    w.set(str(default))

        err_lbl = ctk.CTkLabel(popup, text="",
                               font=ctk.CTkFont("Segoe UI", 11),
                               text_color=DANGER)
        err_lbl.pack(pady=(0, 4))

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=10)

        def get_values():
            return [w.get() for w in widgets.values()]

        def do_save():
            vals = get_values()
            # Basic required field check
            n = queries["insert"].count("?")
            if any(v.strip() == "" for v in vals[-n:]):
                err_lbl.configure(text="All fields are required.")
                return
            try:
                self.cursor.execute(queries["insert"], vals[-n:])
                self.conn.commit()
                messagebox.showinfo("Success", "Record added successfully.", parent=popup)
                refresh_fn()
                popup.destroy()
            except pyodbc.Error as e:
                err_lbl.configure(text=str(e).split("\n")[0][:120])

        def do_update():
            vals    = get_values()
            pk_vals = [str(record_data[i]) for i in range(pk_count)]
            set_vals = [v for i, v in enumerate(vals) if i >= pk_count]
            try:
                self.cursor.execute(queries["update"], set_vals + pk_vals)
                self.conn.commit()
                messagebox.showinfo("Success", "Record updated successfully.", parent=popup)
                refresh_fn()
                popup.destroy()
            except pyodbc.Error as e:
                err_lbl.configure(text=str(e).split("\n")[0][:120])

        def do_delete():
            if not messagebox.askyesno(
                    "Confirm Delete",
                    "⚠️  This action cannot be undone.\n\nAre you sure you want to delete this record?",
                    parent=popup):
                return
            pk_vals = [str(record_data[i]) for i in range(pk_count)]
            try:
                for pre in queries.get("pre_delete", []):
                    self.cursor.execute(pre, pk_vals)
                self.cursor.execute(queries["delete"], pk_vals)
                self.conn.commit()
                messagebox.showinfo("Deleted", "Record deleted successfully.", parent=popup)
                refresh_fn()
                popup.destroy()
            except pyodbc.Error as e:
                err_lbl.configure(text=str(e).split("\n")[0][:120])

        if mode == "add":
            primary_btn(btn_row, "💾  Save", do_save, width=120).pack(side="left", padx=8)
        else:
            primary_btn(btn_row, "✔  Update", do_update, width=120).pack(side="left", padx=6)
            danger_btn(btn_row,  "🗑  Delete", do_delete, width=110).pack(side="left", padx=6)

        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=6)

    # ── CRUD screens with full filter definitions ─────────────────────────

    def _screen_students(self):
        self._crud_screen("Students", "Students",
            ("StudentID","Name","Contact","ParentContact","Year","BatchID","ClassID"),
            [("StudentID",       "entry",    None, None),
             ("Name",            "entry",    None, None),
             ("Contact",         "entry",    None, None),
             ("ParentContact",   "entry",    None, None),
             ("YearOfAdmission", "entry",    None, str(datetime.now().year)),
             ("BatchID",         "combobox", self._get_batches, None),
             ("ClassID",         "combobox", ["MAT9","MAT10","INT1","INT2"], None)],
            {"select":  "SELECT StudentID, Name, Contact, ParentContact, YearOfAdmission, BatchID, ClassID FROM dbo.Student",
             "insert":  "EXEC dbo.sp_InsertStudent ?, ?, ?, ?, ?, ?, ?",
             "update":  "EXEC dbo.sp_UpdateStudent ?, ?, ?, ?, ?, ?, ?",
             "delete":  "DELETE FROM dbo.Student WHERE StudentID = ?",
             "pre_delete": [
                 "DELETE FROM dbo.Attendance WHERE StudentID = ?",
                 "DELETE FROM dbo.Result     WHERE StudentID = ?",
                 "DELETE FROM dbo.Fee        WHERE StudentID = ?",
             ]},
            filter_defs=[
                {"label": "Student ID",   "type": "text",     "column": "StudentID"},
                {"label": "Name",         "type": "text",     "column": "Name"},
                {"label": "Batch",        "type": "dropdown", "column": "BatchID",
                 "options_fn": self._get_batches},
                {"label": "Class",        "type": "dropdown", "column": "ClassID",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
                {"label": "Year of Adm.", "type": "number_range", "column": "YearOfAdmission"},
                {"label": "Contact",      "type": "text",     "column": "Contact"},
            ])

    def _screen_teachers(self):
        self._crud_screen("Teachers", "Teachers",
            ("TeacherID","Name","Subject","DailySalary"),
            [("TeacherID",   "entry", None, None),
             ("Name",        "entry", None, None),
             ("Subject",     "entry", None, None),
             ("DailySalary", "entry", None, "0.00")],
            {"select": "SELECT TeacherID, Name, Subject, DailySalary FROM dbo.Teacher",
             "insert": "INSERT INTO dbo.Teacher VALUES (?, ?, ?, ?)",
             "update": "UPDATE dbo.Teacher SET Name=?, Subject=?, DailySalary=? WHERE TeacherID=?",
             "delete": "DELETE FROM dbo.Teacher WHERE TeacherID=?",
             "pre_delete": [
                 "DELETE FROM dbo.TeacherAttendance WHERE TeacherID=?",
                 "DELETE FROM dbo.Salary WHERE TeacherID=?",
             ]},
            filter_defs=[
                {"label": "Teacher ID",    "type": "text",         "column": "TeacherID"},
                {"label": "Name",          "type": "text",         "column": "Name"},
                {"label": "Subject",       "type": "text",         "column": "Subject"},
                {"label": "Daily Salary",  "type": "number_range", "column": "DailySalary"},
            ])

    def _screen_batches(self):
        self._crud_screen("Batches", "Batches",
            ("BatchID","Name","Year","Program","ClassID"),
            [("BatchID",  "entry",    None, None),
             ("Name",     "entry",    None, None),
             ("Year",     "entry",    None, str(datetime.now().year)),
             ("Program",  "combobox", ["Matric","Intermediate"], None),
             ("ClassID",  "combobox", ["MAT9","MAT10","INT1","INT2"], None)],
            {"select": "SELECT BatchID, Name, Year, Program, ClassID FROM dbo.Batch",
             "insert": "INSERT INTO dbo.Batch VALUES (?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Batch SET Name=?, Year=?, Program=?, ClassID=? WHERE BatchID=?",
             "delete": "DELETE FROM dbo.Batch WHERE BatchID=?",
             "pre_delete": ["DELETE FROM dbo.TimetableEntry WHERE BatchID=?"]},
            filter_defs=[
                {"label": "Batch ID",  "type": "text",         "column": "BatchID"},
                {"label": "Name",      "type": "text",         "column": "Name"},
                {"label": "Year",      "type": "number_range", "column": "Year"},
                {"label": "Program",   "type": "dropdown",     "column": "Program",
                 "options": ["Matric","Intermediate"]},
                {"label": "Class",     "type": "dropdown",     "column": "ClassID",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
            ])

    def _screen_rooms(self):
        self._crud_screen("Rooms", "Rooms",
            ("RoomID","Capacity","AC Count","Chair Count","ClassID"),
            [("RoomID",      "entry",    None, None),
             ("Capacity",    "combobox", ["40","60","80"], None),
             ("AC_Count",    "entry",    None, "0"),
             ("Chair_Count", "entry",    None, "0"),
             ("ClassID",     "combobox", ["MAT9","MAT10","INT1","INT2"], None)],
            {"select": "SELECT RoomID, Capacity, AC_Count, Chair_Count, ClassID FROM dbo.Room",
             "insert": "INSERT INTO dbo.Room VALUES (?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Room SET Capacity=?, AC_Count=?, Chair_Count=?, ClassID=? WHERE RoomID=?",
             "delete": "DELETE FROM dbo.Room WHERE RoomID=?"},
            filter_defs=[
                {"label": "Room ID",    "type": "text",         "column": "RoomID"},
                {"label": "Capacity",   "type": "dropdown",     "column": "Capacity",
                 "options": ["40","60","80"]},
                {"label": "AC Count",   "type": "number_range", "column": "AC_Count"},
                {"label": "Chair Count","type": "number_range", "column": "Chair_Count"},
                {"label": "Class",      "type": "dropdown",     "column": "ClassID",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
            ])

    def _screen_classes(self):
        self._crud_screen("Classes", "Classes",
            ("ClassID","Name"),
            [("ClassID", "combobox", ["MAT9","MAT10","INT1","INT2"], None),
             ("Name",    "entry",    None, None)],
            {"select": "SELECT ClassID, Name FROM dbo.Class",
             "insert": "INSERT INTO dbo.Class VALUES (?, ?)",
             "update": "UPDATE dbo.Class SET Name=? WHERE ClassID=?",
             "delete": "DELETE FROM dbo.Class WHERE ClassID=?"},
            filter_defs=[
                {"label": "Class ID",   "type": "dropdown", "column": "ClassID",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
                {"label": "Name",       "type": "text",     "column": "Name"},
            ])

    def _screen_timetable(self):
        self._crud_screen("Timetable", "Timetable",
            ("BatchID","Day","Period","Subject"),
            [("BatchID",  "combobox", self._get_batches, None),
             ("Day",      "combobox", ["Monday","Tuesday","Wednesday","Thursday","Friday"], None),
             ("Period",   "combobox", ["1","2","3","4","5","6"], None),
             ("Subject",  "entry",    None, None)],
            {"select": "SELECT BatchID, Day, Period, Subject FROM dbo.TimetableEntry",
             "insert": "EXEC dbo.sp_InsertTimetableEntry ?, ?, ?, ?",
             "update": "UPDATE dbo.TimetableEntry SET Subject=? WHERE BatchID=? AND Day=? AND Period=?",
             "delete": "DELETE FROM dbo.TimetableEntry WHERE BatchID=? AND Day=? AND Period=?"},
            filter_defs=[
                {"label": "Batch",   "type": "dropdown",
                 "column": "BatchID", "options_fn": self._get_batches},
                {"label": "Day",     "type": "dropdown", "column": "Day",
                 "options": ["Monday","Tuesday","Wednesday","Thursday","Friday"]},
                {"label": "Period",  "type": "dropdown", "column": "Period",
                 "options": ["1","2","3","4","5","6"]},
                {"label": "Subject", "type": "text",     "column": "Subject"},
            ])

    def _screen_tests(self):
        self._crud_screen("Tests", "Tests",
            ("TestID","Subject","Date","MaxMarks","BatchID","ClassID"),
            [("TestID",   "entry",    None, None),
             ("Subject",  "entry",    None, None),
             ("Date",     "entry",    None, datetime.now().strftime("%Y-%m-%d")),
             ("MaxMarks", "entry",    None, "100"),
             ("BatchID",  "combobox", self._get_batches, None),
             ("ClassID",  "combobox", ["MAT9","MAT10","INT1","INT2"], None)],
            {"select": "SELECT TestID, Subject, Date, MaxMarks, BatchID, ClassID FROM dbo.Test",
             "insert": "INSERT INTO dbo.Test VALUES (?, ?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Test SET Subject=?, Date=?, MaxMarks=?, BatchID=?, ClassID=? WHERE TestID=?",
             "delete": "DELETE FROM dbo.Test WHERE TestID=?"},
            filter_defs=[
                {"label": "Test ID",    "type": "text",         "column": "TestID"},
                {"label": "Subject",    "type": "text",         "column": "Subject"},
                {"label": "Date Range", "type": "date_range",   "column": "Date"},
                {"label": "Max Marks",  "type": "number_range", "column": "MaxMarks"},
                {"label": "Batch",      "type": "dropdown",
                 "column": "BatchID", "options_fn": self._get_batches},
                {"label": "Class",      "type": "dropdown",     "column": "ClassID",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
            ])

    def _screen_results(self):
        self._crud_screen("Results", "Results",
            ("ResultID","StudentID","TestID","ObtainedMarks"),
            [("ResultID",      "entry",    None, None),
             ("StudentID",     "combobox", self._get_students, None),
             ("TestID",        "combobox", self._get_tests,    None),
             ("ObtainedMarks", "entry",    None, "0")],
            {"select": "SELECT ResultID, StudentID, TestID, ObtainedMarks FROM dbo.Result",
             "insert": "INSERT INTO dbo.Result VALUES (?, ?, ?, ?)",
             "update": "UPDATE dbo.Result SET StudentID=?, TestID=?, ObtainedMarks=? WHERE ResultID=?",
             "delete": "DELETE FROM dbo.Result WHERE ResultID=?"},
            filter_defs=[
                {"label": "Student ID",      "type": "dropdown",
                 "column": "StudentID", "options_fn": self._get_students},
                {"label": "Test ID",         "type": "dropdown",
                 "column": "TestID", "options_fn": self._get_tests},
                {"label": "Obtained Marks",  "type": "number_range", "column": "ObtainedMarks"},
            ])

    def _screen_attendance(self):
        self._crud_screen("Student Attendance", "Student Attendance",
            ("AttendanceID","StudentID","Date","Status"),
            [("AttendanceID", "entry",    None, None),
             ("StudentID",    "combobox", self._get_students, None),
             ("Date",         "entry",    None, datetime.now().strftime("%Y-%m-%d")),
             ("Status",       "combobox", ["Present","Absent"], "Present")],
            {"select": "SELECT AttendanceID, StudentID, Date, Status FROM dbo.Attendance",
             "insert": "INSERT INTO dbo.Attendance VALUES (?, ?, ?, ?)",
             "update": "UPDATE dbo.Attendance SET StudentID=?, Date=?, Status=? WHERE AttendanceID=?",
             "delete": "DELETE FROM dbo.Attendance WHERE AttendanceID=?"},
            filter_defs=[
                {"label": "Student ID",  "type": "dropdown",
                 "column": "StudentID", "options_fn": self._get_students},
                {"label": "Date Range",  "type": "date_range", "column": "Date"},
                {"label": "Status",      "type": "dropdown",   "column": "Status",
                 "options": ["Present","Absent"]},
                # Batch filter joins through Student table — handled via subquery
                {"label": "Batch",       "type": "dropdown",
                 "column": "BatchID_Join",  # special — handled in custom refresh
                 "options_fn": self._get_batches},
                {"label": "Class",       "type": "dropdown",
                 "column": "ClassID_Join",
                 "options": ["MAT9","MAT10","INT1","INT2"]},
            ])

    def _screen_teacher_attendance(self):
        self._crud_screen("Teacher Attendance", "Teacher Attendance",
            ("AttendanceID","TeacherID","Date","Status"),
            [("AttendanceID", "entry",    None, None),
             ("TeacherID",    "combobox", self._get_teachers, None),
             ("Date",         "entry",    None, datetime.now().strftime("%Y-%m-%d")),
             ("Status",       "combobox", ["Present","Absent"], "Present")],
            {"select": "SELECT AttendanceID, TeacherID, Date, Status FROM dbo.TeacherAttendance",
             "insert": "INSERT INTO dbo.TeacherAttendance VALUES (?, ?, ?, ?)",
             "update": "UPDATE dbo.TeacherAttendance SET TeacherID=?, Date=?, Status=? WHERE AttendanceID=?",
             "delete": "DELETE FROM dbo.TeacherAttendance WHERE AttendanceID=?"},
            filter_defs=[
                {"label": "Teacher ID",  "type": "dropdown",
                 "column": "TeacherID", "options_fn": self._get_teachers},
                {"label": "Date Range",  "type": "date_range", "column": "Date"},
                {"label": "Status",      "type": "dropdown",   "column": "Status",
                 "options": ["Present","Absent"]},
            ])

    def _screen_fees(self):
        self._crud_screen("Fees", "Student Fees",
            ("FeeID","StudentID","Amount","Discount","DueDate","PaidStatus"),
            [("FeeID",      "entry",    None, None),
             ("StudentID",  "combobox", self._get_students, None),
             ("Amount",     "entry",    None, "0.00"),
             ("Discount",   "entry",    None, "0.00"),
             ("DueDate",    "entry",    None, datetime.now().strftime("%Y-%m-%d")),
             ("PaidStatus", "combobox", ["0","1"], "0")],
            {"select": "SELECT FeeID, StudentID, Amount, Discount, DueDate, PaidStatus FROM dbo.Fee",
             "insert": "INSERT INTO dbo.Fee VALUES (?, ?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Fee SET StudentID=?, Amount=?, Discount=?, DueDate=?, PaidStatus=? WHERE FeeID=?",
             "delete": "DELETE FROM dbo.Fee WHERE FeeID=?"},
            filter_defs=[
                {"label": "Student ID",  "type": "dropdown",
                 "column": "StudentID", "options_fn": self._get_students},
                {"label": "Paid Status", "type": "dropdown",   "column": "PaidStatus",
                 "options": ["0 (Unpaid)","1 (Paid)"]},
                {"label": "Due Date",    "type": "date_range", "column": "DueDate"},
                {"label": "Amount",      "type": "number_range", "column": "Amount"},
                {"label": "Discount",    "type": "number_range", "column": "Discount"},
            ])

    def _screen_salaries(self):
        self._crud_screen("Salaries", "Teacher Salaries",
            ("SalaryID","TeacherID","Month","DaysPresent","Amount"),
            [("SalaryID",        "entry",    None, None),
             ("TeacherID",       "combobox", self._get_teachers, None),
             ("Month",           "entry",    None, datetime.now().strftime("%Y-%m")),
             ("TotalDaysPresent","entry",    None, "0"),
             ("Amount",          "entry",    None, "0.00")],
            {"select": "SELECT SalaryID, TeacherID, Month, TotalDaysPresent, Amount FROM dbo.Salary",
             "insert": "INSERT INTO dbo.Salary VALUES (?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Salary SET TeacherID=?, Month=?, TotalDaysPresent=?, Amount=? WHERE SalaryID=?",
             "delete": "DELETE FROM dbo.Salary WHERE SalaryID=?"},
            filter_defs=[
                {"label": "Teacher ID",   "type": "dropdown",
                 "column": "TeacherID", "options_fn": self._get_teachers},
                {"label": "Month",        "type": "text",         "column": "Month"},
                {"label": "Days Present", "type": "number_range", "column": "TotalDaysPresent"},
                {"label": "Amount",       "type": "number_range", "column": "Amount"},
            ])

    def _screen_assets(self):
        self._crud_screen("Assets", "Classroom Assets",
            ("AssetID","RoomID","Type","Quantity"),
            [("AssetID",  "entry",    None, None),
             ("RoomID",   "combobox", self._get_rooms, None),
             ("Type",     "combobox", ["Chair","AC"], None),
             ("Quantity", "entry",    None, "0")],
            {"select": "SELECT AssetID, RoomID, Type, Quantity FROM dbo.ClassroomAsset",
             "insert": "EXEC dbo.sp_InsertClassroomAsset ?, ?, ?",
             "update": "UPDATE dbo.ClassroomAsset SET RoomID=?, Type=?, Quantity=? WHERE AssetID=?",
             "delete": "DELETE FROM dbo.ClassroomAsset WHERE AssetID=?",
             "pre_delete": ["DELETE FROM dbo.Maintenance WHERE AssetID=?"]},
            filter_defs=[
                {"label": "Asset ID",  "type": "text",         "column": "AssetID"},
                {"label": "Room",      "type": "dropdown",
                 "column": "RoomID", "options_fn": self._get_rooms},
                {"label": "Type",      "type": "dropdown",     "column": "Type",
                 "options": ["Chair","AC"]},
                {"label": "Quantity",  "type": "number_range", "column": "Quantity"},
            ])

    def _screen_maintenance(self):
        self._crud_screen("Maintenance", "Maintenance Records",
            ("MaintenanceID","AssetID","RepairDate","Cost","Status"),
            [("MaintenanceID", "entry",    None, None),
             ("AssetID",       "combobox", self._get_assets, None),
             ("RepairDate",    "entry",    None, datetime.now().strftime("%Y-%m-%d")),
             ("Cost",          "entry",    None, "0.00"),
             ("Status",        "combobox", ["Pending","Done"], "Pending")],
            {"select": "SELECT MaintenanceID, AssetID, RepairDate, Cost, Status FROM dbo.Maintenance",
             "insert": "INSERT INTO dbo.Maintenance VALUES (?, ?, ?, ?, ?)",
             "update": "UPDATE dbo.Maintenance SET AssetID=?, RepairDate=?, Cost=?, Status=? WHERE MaintenanceID=?",
             "delete": "DELETE FROM dbo.Maintenance WHERE MaintenanceID=?"},
            filter_defs=[
                {"label": "Asset ID",     "type": "dropdown",
                 "column": "AssetID", "options_fn": self._get_assets},
                {"label": "Repair Date",  "type": "date_range",   "column": "RepairDate"},
                {"label": "Cost",         "type": "number_range", "column": "Cost"},
                {"label": "Status",       "type": "dropdown",     "column": "Status",
                 "options": ["Pending","Done"]},
            ])

    def _screen_expenses(self):
        self._crud_screen("Expenses", "Expenses",
            ("ExpenseID","Type","Amount","Date"),
            [("ExpenseID", "entry", None, None),
             ("Type",      "entry", None, None),
             ("Amount",    "entry", None, "0.00"),
             ("Date",      "entry", None, datetime.now().strftime("%Y-%m-%d"))],
            {"select": "SELECT ExpenseID, Type, Amount, Date FROM dbo.Expense",
             "insert": "INSERT INTO dbo.Expense VALUES (?, ?, ?, ?)",
             "update": "UPDATE dbo.Expense SET Type=?, Amount=?, Date=? WHERE ExpenseID=?",
             "delete": "DELETE FROM dbo.Expense WHERE ExpenseID=?"},
            filter_defs=[
                {"label": "Type",       "type": "text",         "column": "Type"},
                {"label": "Amount",     "type": "number_range", "column": "Amount"},
                {"label": "Date Range", "type": "date_range",   "column": "Date"},
            ])

    # ── Audit Log screen with filters ────────────────────────────────────

    def _screen_auditlog(self):
        self._clear()
        self._navbar("Audit Log")

        body = ctk.CTkFrame(self.root, fg_color=LIGHT_BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        body.grid_rowconfigure(3, weight=1)
        body.grid_columnconfigure(0, weight=1)

        # Title row
        top = ctk.CTkFrame(body, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        section_label(top, "Audit Log").pack(side="left")

        result_lbl = ctk.CTkLabel(top, text="",
                                  font=ctk.CTkFont("Segoe UI", 11),
                                  text_color=TEXT_MUTED)
        result_lbl.pack(side="left", padx=14)

        def do_export():
            rows = [tree.item(i)["values"] for i in tree.get_children()]
            if not rows:
                messagebox.showwarning("No Data", "Nothing to export.")
                return
            export_pdf("Audit Log Report",
                       ("Date","User","Action","Record ID","Details"),
                       rows, "AuditLog.pdf")

        primary_btn(top, "📄 Export PDF", do_export, width=120, fg=DARK_NAVY).pack(side="right")

        # Filter panel
        filter_defs = [
            {"label": "Table / Action", "type": "text",       "column": "TableName"},
            {"label": "User",           "type": "text",       "column": "ChangedBy"},
            {"label": "Action",         "type": "dropdown",   "column": "Action",
             "options": ["INSERT","UPDATE","DELETE"]},
            {"label": "Date Range",     "type": "date_range", "column": "ChangeDate"},
        ]

        def apply_audit(active):
            load_audit(active)

        def clear_audit():
            load_audit({})

        fp = FilterPanel(body, filter_defs, apply_audit, clear_audit)
        fp.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        # Table
        t2_shadow = ctk.CTkFrame(body, fg_color=CARD_SHADOW, corner_radius=10)
        t2_shadow.grid(row=3, column=0, sticky="nsew")
        t2_shadow.grid_rowconfigure(0, weight=1)
        t2_shadow.grid_columnconfigure(0, weight=1)
        tree_card = ctk.CTkFrame(t2_shadow, fg_color=CARD_BG, corner_radius=9,
                                 border_width=1, border_color=BORDER)
        tree_card.grid(row=0, column=0, sticky="nsew", padx=1, pady=(0, 2))
        tree_card.grid_rowconfigure(0, weight=1)
        tree_card.grid_columnconfigure(0, weight=1)

        cols = ("Date","User","Action","Record ID","Details")
        tree = styled_treeview(tree_card)
        tree["columns"] = cols
        widths = [160, 120, 160, 140, 500]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        vsb = ctk.CTkScrollbar(tree_card, command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ctk.CTkScrollbar(tree_card, orientation="horizontal", command=tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        def load_audit(active_filters=None):
            for item in tree.get_children():
                tree.delete(item)
            try:
                base_q = "SELECT * FROM dbo.AuditLog"
                params = []

                if active_filters:
                    conditions = []
                    for col_k, info in active_filters.items():
                        kind = info[0]
                        if kind == "like":
                            if col_k == "TableName":
                                conditions.append("(TableName LIKE ? OR Action LIKE ?)")
                                params += [f"%{info[1]}%", f"%{info[1]}%"]
                            else:
                                conditions.append(f"CAST([{col_k}] AS NVARCHAR(MAX)) LIKE ?")
                                params.append(f"%{info[1]}%")
                        elif kind == "eq":
                            conditions.append(f"[{col_k}] = ?")
                            params.append(info[1])
                        elif kind == "date_range":
                            if info[1]:
                                conditions.append(f"CONVERT(DATE,[{col_k}]) >= ?")
                                params.append(info[1])
                            if info[2]:
                                conditions.append(f"CONVERT(DATE,[{col_k}]) <= ?")
                                params.append(info[2])
                    if conditions:
                        base_q += " WHERE " + " AND ".join(conditions)

                base_q += " ORDER BY ChangeDate DESC"
                self.cursor.execute(base_q, params)
                raw_cols = [d[0] for d in self.cursor.description]
                rows_all = self.cursor.fetchall()

                for i, row in enumerate(rows_all):
                    rd = dict(zip(raw_cols, row))
                    action = rd.get("Action", "")
                    old    = rd.get("OldValues", "") or ""
                    new    = rd.get("NewValues", "") or ""

                    def clean(v):
                        if isinstance(v, str) and v.strip().startswith(("[","(")):
                            try:    return ", ".join(map(str, ast.literal_eval(v)))
                            except: pass
                        return v

                    if action == "INSERT":   details = f"New: {clean(new)}"
                    elif action == "DELETE": details = f"Deleted: {clean(old)}"
                    elif action == "UPDATE": details = f"FROM: {clean(old)}  TO: {clean(new)}"
                    else:                    details = clean(new) or clean(old)

                    tag = "evenrow" if i % 2 == 0 else "oddrow"
                    tree.insert("", "end", tags=(tag,), values=[
                        rd.get("ChangeDate",""), rd.get("ChangedBy",""),
                        f"{rd.get('TableName','')} {action}",
                        rd.get("RecordID", rd.get("RecordlD","")),
                        details
                    ])

                result_lbl.configure(
                    text=f"Showing {len(rows_all)} log entr{'ies' if len(rows_all)!=1 else 'y'}",
                    text_color=SUCCESS if rows_all else DANGER)

            except pyodbc.Error as e:
                messagebox.showerror("Database Error", str(e).split("\n")[0])

        load_audit()

    # ── Quick-capture popups ──────────────────────────────────────────────

    def _popup_add_student(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Student")
        popup.geometry("480x530")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x", side="top")
        ctk.CTkLabel(hdr_bar, text="➕  Add New Student",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        f_shadow = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        f_shadow.pack(padx=18, pady=12, fill="x")
        form = ctk.CTkFrame(f_shadow, fg_color=CARD_BG, corner_radius=9,
                            border_width=1, border_color=BORDER)
        form.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        def field(label, widget_fn):
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(r, text=label + ":", width=140,
                         font=ctk.CTkFont("Segoe UI", 11, "bold"),
                         text_color=TEXT_MUTED, anchor="e").pack(side="left", padx=(0, 10))
            w = widget_fn(r)
            w.pack(side="left")
            return w

        name_e    = field("Name",           lambda p: ctk.CTkEntry(p, width=240, fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8, font=ctk.CTkFont("Segoe UI", 11)))
        contact_e = field("Contact",        lambda p: ctk.CTkEntry(p, width=240, fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8, font=ctk.CTkFont("Segoe UI", 11)))
        parent_e  = field("Parent Contact", lambda p: ctk.CTkEntry(p, width=240, fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8, font=ctk.CTkFont("Segoe UI", 11)))
        year_e    = field("Year of Adm.",   lambda p: ctk.CTkEntry(p, width=240, fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8, font=ctk.CTkFont("Segoe UI", 11)))
        year_e.insert(0, str(datetime.now().year))

        batch_var = ctk.StringVar(value="Select Batch")
        class_var = ctk.StringVar(value="Select Class")
        id_var    = ctk.StringVar(value="")

        batch_cb = field("Batch", lambda p: ctk.CTkOptionMenu(
            p, values=self._get_batches(), variable=batch_var, width=242,
            fg_color=LIGHT_BG, button_color=MID_BLUE))
        class_cb = field("Class", lambda p: ctk.CTkOptionMenu(
            p, values=["MAT9","MAT10","INT1","INT2"], variable=class_var, width=242,
            fg_color=LIGHT_BG, button_color=MID_BLUE))

        field("Student ID (auto)", lambda p: ctk.CTkEntry(
            p, width=240, textvariable=id_var, state="readonly",
            fg_color=LIGHT_BG, border_color=BORDER))

        def gen_id(*_):
            b, c = batch_var.get(), class_var.get()
            if "Select" in (b, c): return
            try:
                prefix_map = {"MAT9":"MAT","MAT10":"MAT","INT1":"INT","INT2":"INT"}
                start_map  = {"MAT9":1,"INT1":1,"MAT10":201,"INT2":201}
                cls_prefix = prefix_map.get(c, c)
                start = start_map.get(c, 1)
                self.cursor.execute(
                    "SELECT StudentID FROM dbo.Student WHERE BatchID=? AND ClassID=? ORDER BY StudentID DESC",
                    (b, c))
                existing = [r[0] for r in self.cursor.fetchall()]
                max_n = 0
                for sid in existing:
                    try:
                        n = int(sid.split("-")[-1])
                        if n >= start: max_n = max(max_n, n)
                    except: pass
                next_n = max_n + 1 if max_n >= start else start
                id_var.set(f"{b}-{cls_prefix}-{str(next_n).zfill(3)}")
            except Exception as e:
                print(e)

        batch_cb.configure(command=gen_id)
        class_cb.configure(command=gen_id)

        err = ctk.CTkLabel(popup, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=DANGER)
        err.pack(pady=4)

        def save():
            sid = id_var.get()
            if not sid:
                err.configure(text="Please select a valid batch and class first.")
                return
            if not name_e.get().strip():
                err.configure(text="Name is required.")
                return
            if not year_e.get().strip().isdigit():
                err.configure(text="Year must be a valid number.")
                return
            try:
                self.cursor.execute("EXEC dbo.sp_InsertStudent ?, ?, ?, ?, ?, ?, ?",
                    (sid, name_e.get().strip(), contact_e.get(),
                     parent_e.get(), int(year_e.get()),
                     batch_var.get(), class_var.get()))
                self.conn.commit()
                messagebox.showinfo("Success", "Student added successfully.", parent=popup)
                popup.destroy()
                self._dashboard()
            except pyodbc.Error as e:
                err.configure(text=str(e).split("\n")[0][:100])

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=12)
        primary_btn(btn_row, "💾  Save Student", save, width=150).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")

    def _popup_add_teacher(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add Teacher")
        popup.geometry("420x360")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x", side="top")
        ctk.CTkLabel(hdr_bar, text="➕  Add New Teacher",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        f_shadow = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        f_shadow.pack(padx=18, pady=12, fill="x")
        form = ctk.CTkFrame(f_shadow, fg_color=CARD_BG, corner_radius=9,
                            border_width=1, border_color=BORDER)
        form.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        fields_data = [("Teacher ID","tid"),("Name","name"),("Subject","subj"),("Daily Salary","sal")]
        entries = {}
        for label, key in fields_data:
            r = ctk.CTkFrame(form, fg_color="transparent")
            r.pack(fill="x", padx=12, pady=6)
            ctk.CTkLabel(r, text=label+":", width=120, anchor="e",
                         text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,10))
            e = ctk.CTkEntry(r, width=230, fg_color=LIGHT_BG, border_color=BORDER,
                             corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
            e.pack(side="left")
            entries[key] = e

        err = ctk.CTkLabel(popup, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=DANGER)
        err.pack(pady=4)

        def save():
            vals = [entries[k].get().strip() for k in ("tid","name","subj","sal")]
            if not all(vals):
                err.configure(text="All fields are required.")
                return
            try:
                float(vals[3])
            except ValueError:
                err.configure(text="Daily Salary must be a number.")
                return
            try:
                self.cursor.execute(
                    "INSERT INTO dbo.Teacher VALUES (?, ?, ?, ?)", vals)
                self.conn.commit()
                messagebox.showinfo("Success", "Teacher added successfully.", parent=popup)
                popup.destroy()
            except pyodbc.Error as e:
                err.configure(text=str(e).split("\n")[0][:100])

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=12)
        primary_btn(btn_row, "💾  Save Teacher", save, width=150).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")

    def _popup_add_student_attendance(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Student Attendance")
        popup.geometry("520x540")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x")
        ctk.CTkLabel(hdr_bar, text="📋  Student Attendance",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        filter_card = card_frame(popup)
        filter_card.pack(padx=18, pady=(10, 0), fill="x")

        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(row1, text="Batch:", width=60, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,6))
        batch_var = ctk.StringVar(value="— Select —")
        batch_cb  = ctk.CTkComboBox(row1, values=["— Select —"] + self._get_batches(),
                                    variable=batch_var, width=150,
                                    fg_color=LIGHT_BG, border_color=BORDER, button_color=MID_BLUE,
                                    corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
        batch_cb.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row1, text="Date:", width=40, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,6))
        date_e = ctk.CTkEntry(row1, width=130, fg_color=LIGHT_BG, border_color=BORDER,
                               corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
        date_e.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_e.pack(side="left")

        primary_btn(row1, "Load Students", lambda: load_students(), width=130, fg=MID_BLUE).pack(side="left", padx=10)

        # Scrollable attendance list
        list_shadow = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        list_shadow.pack(padx=18, pady=10, fill="both", expand=True)
        list_card = ctk.CTkFrame(list_shadow, fg_color=CARD_BG, corner_radius=9,
                                 border_width=1, border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        status_vars = {}

        def load_students():
            for w in scroll.winfo_children():
                w.destroy()
            status_vars.clear()
            b = batch_var.get()
            if "Select" in b:
                messagebox.showwarning("Select Batch", "Please select a batch first.", parent=popup)
                return
            d = date_e.get().strip()
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be in YYYY-MM-DD format.", parent=popup)
                return
            try:
                self.cursor.execute(
                    "SELECT StudentID, Name FROM dbo.Student WHERE BatchID=? ORDER BY StudentID",
                    (b,))
                students = self.cursor.fetchall()
                if not students:
                    ctk.CTkLabel(scroll, text="No students found in this batch.",
                                 text_color=TEXT_MUTED).pack(pady=20)
                    return

                hdr = ctk.CTkFrame(scroll, fg_color=DARK_NAVY, corner_radius=6)
                hdr.pack(fill="x", pady=(0, 4))
                for txt, w in [("Student ID", 120),("Name", 200),("Status", 150)]:
                    ctk.CTkLabel(hdr, text=txt, width=w, anchor="w",
                                 text_color="white",
                                 font=ctk.CTkFont("Segoe UI", 10, "bold")).pack(side="left", padx=8, pady=6)

                for i, (sid, sname) in enumerate(students):
                    row_bg = "#F5F8FF" if i % 2 == 0 else CARD_BG
                    r = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=4)
                    r.pack(fill="x", pady=1)
                    ctk.CTkLabel(r, text=sid, width=120, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=8, pady=5)
                    ctk.CTkLabel(r, text=sname, width=200, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
                    var = ctk.StringVar(value="Present")
                    seg = ctk.CTkSegmentedButton(r, values=["Present","Absent"],
                                                 variable=var, width=150,
                                                 selected_color=SUCCESS,
                                                 selected_hover_color="#059669",
                                                 unselected_color=LIGHT_BG,
                                                 font=ctk.CTkFont("Segoe UI", 10, "bold"))
                    seg.pack(side="left", padx=8)
                    status_vars[sid] = var
            except pyodbc.Error as e:
                messagebox.showerror("Error", str(e).split("\n")[0], parent=popup)

        err = ctk.CTkLabel(popup, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=DANGER)
        err.pack(pady=2)

        def save_all():
            if not status_vars:
                messagebox.showwarning("No Data", "Please load students first.", parent=popup)
                return
            d = date_e.get().strip()
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                err.configure(text="Invalid date format.")
                return
            try:
                self.cursor.execute(
                    "SELECT MAX(CAST(SUBSTRING(AttendanceID,2,LEN(AttendanceID)) AS INT)) FROM dbo.Attendance")
                max_id = self.cursor.fetchone()[0] or 0
                nxt = max_id + 1
                saved = 0
                for sid, var in status_vars.items():
                    # Check for duplicate
                    self.cursor.execute(
                        "SELECT AttendanceID FROM dbo.Attendance WHERE StudentID=? AND Date=?",
                        (sid, d))
                    existing = self.cursor.fetchone()
                    if existing:
                        self.cursor.execute(
                            "UPDATE dbo.Attendance SET Status=? WHERE StudentID=? AND Date=?",
                            (var.get(), sid, d))
                    else:
                        aid = f"A{str(nxt).zfill(4)}"
                        nxt += 1
                        self.cursor.execute(
                            "INSERT INTO dbo.Attendance VALUES (?, ?, ?, ?)",
                            (aid, sid, d, var.get()))
                    saved += 1
                self.conn.commit()
                messagebox.showinfo("Saved",
                                    f"Attendance saved for {saved} students on {d}.",
                                    parent=popup)
                popup.destroy()
            except pyodbc.Error as e:
                err.configure(text=str(e).split("\n")[0][:100])

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=8)
        primary_btn(btn_row, "💾  Save Attendance", save_all, width=160).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")

    def _popup_add_teacher_attendance(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Teacher Attendance")
        popup.geometry("480x480")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x")
        ctk.CTkLabel(hdr_bar, text="📋  Teacher Attendance",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        top_card = card_frame(popup)
        top_card.pack(padx=18, pady=10, fill="x")
        r = ctk.CTkFrame(top_card, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(r, text="Date:", width=50, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,6))
        date_e = ctk.CTkEntry(r, width=140, fg_color=LIGHT_BG, border_color=BORDER,
                               corner_radius=8, font=ctk.CTkFont("Segoe UI", 11))
        date_e.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_e.pack(side="left")
        primary_btn(r, "Load Teachers", lambda: load_teachers(), width=130).pack(side="left", padx=10)

        list_shadow = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        list_shadow.pack(padx=18, pady=8, fill="both", expand=True)
        list_card = ctk.CTkFrame(list_shadow, fg_color=CARD_BG, corner_radius=9,
                                 border_width=1, border_color=BORDER)
        list_card.pack(fill="both", expand=True, padx=1, pady=(0, 2))

        scroll = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        t_status_vars = {}

        def load_teachers():
            for w in scroll.winfo_children():
                w.destroy()
            t_status_vars.clear()
            d = date_e.get().strip()
            try:
                datetime.strptime(d, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be YYYY-MM-DD.", parent=popup)
                return
            try:
                self.cursor.execute("SELECT TeacherID, Name FROM dbo.Teacher ORDER BY Name")
                teachers = self.cursor.fetchall()
                for i, (tid, tname) in enumerate(teachers):
                    bg = "#F5F8FF" if i % 2 == 0 else CARD_BG
                    row_f = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=4)
                    row_f.pack(fill="x", pady=1)
                    ctk.CTkLabel(row_f, text=tid, width=100, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=8, pady=5)
                    ctk.CTkLabel(row_f, text=tname, width=200, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
                    var = ctk.StringVar(value="Present")
                    seg = ctk.CTkSegmentedButton(row_f, values=["Present","Absent"],
                                                 variable=var, width=150,
                                                 selected_color=SUCCESS,
                                                 selected_hover_color="#059669",
                                                 unselected_color=LIGHT_BG,
                                                 font=ctk.CTkFont("Segoe UI", 10, "bold"))
                    seg.pack(side="left", padx=8)
                    t_status_vars[tid] = var
            except pyodbc.Error as e:
                messagebox.showerror("Error", str(e).split("\n")[0], parent=popup)

        def save_all():
            if not t_status_vars:
                messagebox.showwarning("No Data", "Load teachers first.", parent=popup)
                return
            d = date_e.get().strip()
            try:
                self.cursor.execute(
                    "SELECT MAX(CAST(SUBSTRING(AttendanceID,3,LEN(AttendanceID)) AS INT)) FROM dbo.TeacherAttendance")
                max_id = self.cursor.fetchone()[0] or 0
                nxt = max_id + 1
                for tid, var in t_status_vars.items():
                    self.cursor.execute(
                        "SELECT AttendanceID FROM dbo.TeacherAttendance WHERE TeacherID=? AND Date=?",
                        (tid, d))
                    existing = self.cursor.fetchone()
                    if existing:
                        self.cursor.execute(
                            "UPDATE dbo.TeacherAttendance SET Status=? WHERE TeacherID=? AND Date=?",
                            (var.get(), tid, d))
                    else:
                        aid = f"TA{str(nxt).zfill(4)}"
                        nxt += 1
                        self.cursor.execute(
                            "INSERT INTO dbo.TeacherAttendance VALUES (?, ?, ?, ?)",
                            (aid, tid, d, var.get()))
                self.conn.commit()
                messagebox.showinfo("Saved", "Teacher attendance saved.", parent=popup)
                popup.destroy()
            except pyodbc.Error as e:
                messagebox.showerror("Error", str(e).split("\n")[0], parent=popup)

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=8)
        primary_btn(btn_row, "💾  Save Attendance", save_all, width=160).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")

    def _popup_add_result(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Add / Update Results")
        popup.geometry("560x580")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        hdr_bar = ctk.CTkFrame(popup, fg_color=DARK_NAVY, corner_radius=0, height=52)
        hdr_bar.pack(fill="x")
        ctk.CTkLabel(hdr_bar, text="📝  Add / Update Results",
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color="white").pack(pady=14, padx=20, anchor="w")

        filter_card = card_frame(popup)
        filter_card.pack(padx=18, pady=10, fill="x")

        r = ctk.CTkFrame(filter_card, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(r, text="Batch:", width=55, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,6))
        batch_var = ctk.StringVar(value="— Select —")
        ctk.CTkComboBox(r, values=["— Select —"] + self._get_batches(),
                        variable=batch_var, width=140,
                        fg_color=LIGHT_BG, border_color=BORDER, button_color=MID_BLUE,
                        corner_radius=8, state="readonly").pack(side="left", padx=(0,12))

        ctk.CTkLabel(r, text="Test:", width=40, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=(0,6))
        test_var  = ctk.StringVar(value="— Select —")
        test_opts = self._get_tests()
        ctk.CTkComboBox(r, values=["— Select —"] + test_opts,
                        variable=test_var, width=140,
                        fg_color=LIGHT_BG, border_color=BORDER, button_color=MID_BLUE,
                        corner_radius=8, state="readonly").pack(side="left", padx=(0,12))
        primary_btn(r, "Load", lambda: load_results(), width=80).pack(side="left")

        scroll_frame = ctk.CTkFrame(popup, fg_color=CARD_SHADOW, corner_radius=10)
        scroll_frame.pack(padx=18, pady=8, fill="both", expand=True)
        inner = ctk.CTkFrame(scroll_frame, fg_color=CARD_BG, corner_radius=9,
                             border_width=1, border_color=BORDER)
        inner.pack(fill="both", expand=True, padx=1, pady=(0,2))
        scroll = ctk.CTkScrollableFrame(inner, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        mark_vars = {}
        total_ref = [100]

        def load_results():
            for w in scroll.winfo_children():
                w.destroy()
            mark_vars.clear()
            b = batch_var.get()
            t = test_var.get()
            if "Select" in (b, t):
                messagebox.showwarning("Select Filter", "Please select both Batch and Test.", parent=popup)
                return
            try:
                self.cursor.execute("SELECT MaxMarks FROM dbo.Test WHERE TestID=?", (t,))
                row = self.cursor.fetchone()
                if not row:
                    messagebox.showerror("Error", "Test not found.", parent=popup)
                    return
                total = int(row[0])
                total_ref[0] = total

                self.cursor.execute(
                    "SELECT s.StudentID, s.Name, r.ObtainedMarks "
                    "FROM dbo.Student s "
                    "LEFT JOIN dbo.Result r ON s.StudentID=r.StudentID AND r.TestID=? "
                    "WHERE s.BatchID=? ORDER BY s.StudentID", (t, b))
                students = self.cursor.fetchall()

                hdr = ctk.CTkFrame(scroll, fg_color=DARK_NAVY, corner_radius=6)
                hdr.pack(fill="x", pady=(0,4))
                for txt, w in [("Student ID",120),("Name",200),(f"Marks / {total}",120)]:
                    ctk.CTkLabel(hdr, text=txt, width=w, anchor="w",
                                 text_color="white",
                                 font=ctk.CTkFont("Segoe UI", 10, "bold")).pack(side="left", padx=8, pady=6)

                for i, (sid, sname, marks) in enumerate(students):
                    bg = "#F5F8FF" if i % 2 == 0 else CARD_BG
                    row_f = ctk.CTkFrame(scroll, fg_color=bg, corner_radius=4)
                    row_f.pack(fill="x", pady=1)
                    ctk.CTkLabel(row_f, text=sid, width=120, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=8, pady=5)
                    ctk.CTkLabel(row_f, text=sname, width=200, anchor="w",
                                 text_color=TEXT_DARK, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
                    var = ctk.StringVar(value=str(marks) if marks is not None else "")
                    e = ctk.CTkEntry(row_f, textvariable=var, width=100,
                                     fg_color=LIGHT_BG, border_color=BORDER, corner_radius=6)
                    e.pack(side="left", padx=8)
                    mark_vars[sid] = var
            except pyodbc.Error as e:
                messagebox.showerror("Error", str(e).split("\n")[0], parent=popup)

        def save():
            if not mark_vars:
                messagebox.showwarning("No Data", "Load students first.", parent=popup)
                return
            t     = test_var.get()
            total = total_ref[0]
            errors = []
            for sid, var in mark_vars.items():
                val = var.get().strip()
                if not val:
                    continue
                try:
                    m = float(val)
                    if not (0 <= m <= total):
                        errors.append(f"{sid}: must be 0–{total}")
                except ValueError:
                    errors.append(f"{sid}: not a valid number")
            if errors:
                messagebox.showerror("Validation",
                                     "Fix these errors:\n• " + "\n• ".join(errors),
                                     parent=popup)
                return
            try:
                self.cursor.execute(
                    "SELECT MAX(CAST(SUBSTRING(ResultID,2,LEN(ResultID)) AS INT)) FROM dbo.Result")
                nxt = (self.cursor.fetchone()[0] or 0) + 1
                for sid, var in mark_vars.items():
                    val = var.get().strip()
                    if not val: continue
                    marks = float(val)
                    self.cursor.execute(
                        "SELECT ResultID FROM dbo.Result WHERE StudentID=? AND TestID=?", (sid, t))
                    existing = self.cursor.fetchone()
                    if existing:
                        self.cursor.execute(
                            "UPDATE dbo.Result SET ObtainedMarks=? WHERE StudentID=? AND TestID=?",
                            (marks, sid, t))
                    else:
                        rid = f"R{str(nxt).zfill(3)}"
                        nxt += 1
                        self.cursor.execute(
                            "INSERT INTO dbo.Result VALUES (?,?,?,?)", (rid, sid, t, marks))
                self.conn.commit()
                messagebox.showinfo("Saved", "Results saved successfully.", parent=popup)
                popup.destroy()
            except pyodbc.Error as e:
                messagebox.showerror("Error", str(e).split("\n")[0], parent=popup)

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=8)
        primary_btn(btn_row, "💾  Save Results", save, width=150).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Cancel", command=popup.destroy,
                      fg_color="#94A3B8", hover_color="#64748B",
                      corner_radius=8, height=36, width=90,
                      font=ctk.CTkFont("Segoe UI", 11)).pack(side="left")

    def _popup_fee_challan(self):
        popup = ctk.CTkToplevel(self.root)
        popup.title("Fee Challan")
        popup.geometry("460x400")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(fg_color=LIGHT_BG)

        ctk.CTkLabel(popup, text="🧾  Fee Challan",
                     font=ctk.CTkFont("Segoe UI", 16, "bold"),
                     text_color=DARK_NAVY).pack(pady=(18, 8), padx=24, anchor="w")

        card = card_frame(popup)
        card.pack(padx=18, fill="x")

        r = ctk.CTkFrame(card, fg_color="transparent")
        r.pack(fill="x", padx=12, pady=10)
        ctk.CTkLabel(r, text="Student ID / Name:", width=150, anchor="e",
                     text_color=TEXT_MUTED, font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=(0,8))
        search_e = ctk.CTkEntry(r, width=200, fg_color=LIGHT_BG, border_color=BORDER, corner_radius=8)
        search_e.pack(side="left")

        result_frame = ctk.CTkFrame(popup, fg_color="transparent")
        result_frame.pack(padx=18, pady=8, fill="x")

        err = ctk.CTkLabel(popup, text="", font=ctk.CTkFont("Segoe UI", 11), text_color=DANGER)
        err.pack()

        def generate():
            q = search_e.get().strip()
            if not q:
                err.configure(text="Please enter a student ID or name.")
                return
            err.configure(text="")
            try:
                self.cursor.execute(
                    "SELECT StudentID, Name FROM dbo.Student WHERE StudentID LIKE ? OR Name LIKE ?",
                    (f"%{q}%", f"%{q}%"))
                student = self.cursor.fetchone()
                if not student:
                    err.configure(text="Student not found.")
                    return
                sid, sname = student
                self.cursor.execute(
                    "SELECT FeeID, Amount, Discount, DueDate FROM dbo.Fee "
                    "WHERE StudentID=? AND PaidStatus=0", (sid,))
                fees = self.cursor.fetchall()

                for w in result_frame.winfo_children():
                    w.destroy()

                if not fees:
                    ctk.CTkLabel(result_frame, text=f"✅  {sname} has no outstanding fees.",
                                 font=ctk.CTkFont("Segoe UI", 12), text_color=SUCCESS).pack()
                    return

                ctk.CTkLabel(result_frame,
                             text=f"Student: {sname}  ({sid})",
                             font=ctk.CTkFont("Segoe UI", 12, "bold"),
                             text_color=DARK_NAVY).pack(anchor="w", pady=4)
                for fid, amt, disc, due in fees:
                    net = float(amt) - float(disc or 0)
                    ctk.CTkLabel(result_frame,
                                 text=f"  {fid}   Amount: Rs.{amt}   Disc: Rs.{disc or 0}   "
                                      f"Net: Rs.{net:.2f}   Due: {due}",
                                 font=ctk.CTkFont("Segoe UI", 11),
                                 text_color=TEXT_DARK).pack(anchor="w", pady=2)

                def export_challan():
                    rows = [(fid, f"Rs.{amt}", f"Rs.{disc or 0}",
                             f"Rs.{float(amt)-float(disc or 0):.2f}", str(due))
                            for fid, amt, disc, due in fees]
                    export_pdf(f"Fee Challan — {sname}",
                               ("FeeID","Amount","Discount","Net Amount","Due Date"),
                               rows, f"Challan_{sid}.pdf")

                primary_btn(result_frame, "📥  Download PDF", export_challan, width=180).pack(pady=8)
            except pyodbc.Error as e:
                err.configure(text=str(e).split("\n")[0][:100])

        primary_btn(card, "Generate", generate, width=100).pack(padx=12, pady=(0,10), anchor="e")
        search_e.bind("<Return>", lambda e: generate())

    # ── PDF export helpers ────────────────────────────────────────────────

    def _export_student_report(self):
        try:
            self.cursor.execute(
                "SELECT StudentID, Name, Contact, ParentContact, YearOfAdmission, BatchID, ClassID "
                "FROM dbo.Student ORDER BY BatchID, ClassID, StudentID")
            rows = self.cursor.fetchall()
            if not rows:
                messagebox.showinfo("No Data", "No students found to export.")
                return
            export_pdf("Student Report",
                       ("StudentID","Name","Contact","ParentContact","Year","BatchID","ClassID"),
                       rows, "StudentReport.pdf")
        except pyodbc.Error as e:
            messagebox.showerror("Error", str(e).split("\n")[0])

    def _export_teacher_report(self):
        try:
            self.cursor.execute(
                "SELECT TeacherID, Name, Subject, DailySalary FROM dbo.Teacher ORDER BY Name")
            rows = self.cursor.fetchall()
            if not rows:
                messagebox.showinfo("No Data", "No teachers found to export.")
                return
            export_pdf("Teacher Report",
                       ("TeacherID","Name","Subject","Daily Salary"),
                       rows, "TeacherReport.pdf")
        except pyodbc.Error as e:
            messagebox.showerror("Error", str(e).split("\n")[0])

    # ── Dropdown data helpers ─────────────────────────────────────────────

    def _get_batches(self):
        try:
            self.cursor.execute("SELECT BatchID FROM dbo.Batch ORDER BY BatchID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    def _get_students(self):
        try:
            self.cursor.execute("SELECT StudentID FROM dbo.Student ORDER BY StudentID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    def _get_teachers(self):
        try:
            self.cursor.execute("SELECT TeacherID FROM dbo.Teacher ORDER BY TeacherID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    def _get_tests(self):
        try:
            self.cursor.execute("SELECT TestID FROM dbo.Test ORDER BY TestID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    def _get_rooms(self):
        try:
            self.cursor.execute("SELECT RoomID FROM dbo.Room ORDER BY RoomID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    def _get_assets(self):
        try:
            self.cursor.execute("SELECT AssetID FROM dbo.ClassroomAsset ORDER BY AssetID")
            return [r[0] for r in self.cursor.fetchall()] or ["—"]
        except: return ["—"]

    # ── Utility ───────────────────────────────────────────────────────────

    def _clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = ctk.CTk()
    app  = ASKAcademyApp(root)
    root.mainloop()