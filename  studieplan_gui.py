import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

#  Tkinter GUI for studieplan

class Model:
    def __init__(self):
        self.courses = []  # {id, kode, semester, stp}
        self._next_id = 1
        self.plan = [[] for _ in range(6)]  # 6 semestre, holder course_id

    def term_for_semester_index(self, idx):
        return "høst" if idx in (0, 2, 4) else "vår"

    def add_course(self, kode: str, semester: str, stp: int):
        if any(c["kode"].lower() == kode.lower() for c in self.courses):
            raise ValueError(f"Emnekode '{kode}' finnes allerede.")
        if semester not in ("høst", "vår"):
            raise ValueError("Semester må være 'høst' eller 'vår'.")
        if not isinstance(stp, int) or stp <= 0 or stp > 30:
            raise ValueError("Studiepoeng må være heltall mellom 1 og 30.")
        c = {"id": self._next_id, "kode": kode, "semester": semester, "stp": int(stp)}
        self._next_id += 1
        self.courses.append(c)
        return c

    def delete_course(self, cid: int):
        """Frivillig 9: Slett et emne. Fjerner også fra studieplanen hvis tilstede."""
        course = self.get_course(cid)
        if not course:
            raise ValueError("Fant ikke emnet.")
        # Fjern fra alle semestre
        for i in range(6):
            if cid in self.plan[i]:
                self.plan[i] = [x for x in self.plan[i] if x != cid]
        # Fjern fra emnelista
        self.courses = [c for c in self.courses if c["id"] != cid]

    def get_course(self, cid):
        return next((c for c in self.courses if c["id"] == cid), None)

    def course_in_plan(self, cid):
        return any(cid in sem for sem in self.plan)

    def total_credits(self, sem_idx):
        return sum(self.get_course(cid)["stp"] for cid in self.plan[sem_idx])

    def add_course_to_semester(self, cid, sem_idx):
        c = self.get_course(cid)
        if not c:
            raise ValueError("Ugyldig emne.")
        if self.course_in_plan(cid):
            raise ValueError("Emnet er allerede i studieplanen.")
        riktig_term = self.term_for_semester_index(sem_idx)
        if c["semester"] != riktig_term:
            allowed = "1/3/5" if c["semester"] == "høst" else "2/4/6"
            raise ValueError(f"{c['kode']} er et {c['semester']}-emne og kan bare ligge i semester {allowed}.")
        if self.total_credits(sem_idx) + c["stp"] > 30:
            raise ValueError(f"Ikke plass i semester {sem_idx+1} (maks 30 stp).")
        self.plan[sem_idx].append(cid)

    def remove_course_from_semester(self, cid, sem_idx):
        if cid in self.plan[sem_idx]:
            self.plan[sem_idx].remove(cid)

    def clear_semester(self, sem_idx):
        self.plan[sem_idx].clear()

    def validate_plan(self):
        invalid = []
        for i in range(6):
            tot = self.total_credits(i)
            if tot != 30:
                invalid.append((i, tot))
        return invalid

    def to_json(self):
        return {"next_id": self._next_id, "courses": self.courses, "plan": self.plan}

    def load_json(self, data):
        # next_id
        try:
            self._next_id = int(data.get("next_id", 1))
        except Exception:
            self._next_id = 1
        # courses (valider felt)
        new_courses = []
        seen_codes = set()
        for c in data.get("courses", []):
            try:
                cid = int(c.get("id"))
                kode = str(c.get("kode")).strip()
                sem = c.get("semester")
                stp = int(c.get("stp"))
                if not kode or sem not in ("høst", "vår") or stp < 1 or stp > 30:
                    continue
                if kode.lower() in seen_codes:
                    continue
                new_courses.append({"id": cid, "kode": kode, "semester": sem, "stp": stp})
                seen_codes.add(kode.lower())
            except Exception:
                continue
        self.courses = new_courses
        # plan
        new_plan = [[] for _ in range(6)]
        raw_plan = data.get("plan", [[] for _ in range(6)])
        valid_ids = {c["id"] for c in self.courses}
        for i in range(6):
            try:
                ids = [int(x) for x in raw_plan[i]] if i < len(raw_plan) else []
            except Exception:
                ids = []
            # filtrer til gyldige id-er
            new_plan[i] = [cid for cid in ids if cid in valid_ids]
        self.plan = new_plan


# ---------- GUI ----------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Studieplan")
        self.geometry("1200x760")
        self.minsize(1100, 660)
        self.model = Model()
        self.theme = "dark"  
        self._dirty = False   # spor om det finnes ulagrede endringer
        self.current_file = None

        self.palettes = {
            "light": {
                "bg": "#f8fafc",
                "panel": "#ffffff",
                "muted": "#e5e7eb",
                "border": "#d1d5db",
                "primary": "#2563eb",
                "primary_fg": "#ffffff",
                "success": "#16a34a",
                "warning": "#d97706",
                "danger": "#dc2626",
                "text": "#0f172a",
                "subtle": "#475569",
                "table_bg": "#ffffff",
                "table_alt": "#f3f4f6",
                "table_fg": "#0f172a",
                "table_head_bg": "#e5e7eb",
            },
            "dark": {
                "bg": "#0b1220",
                "panel": "#111827",
                "muted": "#1f2937",
                "border": "#374151",
                "primary": "#60a5fa",
                "primary_fg": "#0b1220",
                "success": "#22c55e",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "text": "#e5e7eb",
                "subtle": "#9ca3af",
                "table_bg": "#0f172a",
                "table_alt": "#111827",
                "table_fg": "#e5e7eb",
                "table_head_bg": "#1f2937",
            }
        }
        self._setup_style()
        self._build_ui()
        self._bind_shortcuts()
        self._seed_examples()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ----- Styling -----
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        p = self.palettes[self.theme]

        # Root
        self.configure(bg=p["bg"])  # vinduets bakgrunn

        # Basestiler
        style.configure("TFrame", background=p["bg"])
        style.configure("Panel.TFrame", background=p["panel"], relief="flat", borderwidth=0)
        style.configure("Toolbar.TFrame", background=p["panel"], relief="flat")

        style.configure("Header.TLabel", background=p["bg"], foreground=p["text"], font=("Segoe UI", 16, "bold"))
        style.configure("Subheader.TLabel", background=p["panel"], foreground=p["subtle"], font=("Segoe UI", 10))
        style.configure("TLabel", background=p["panel"], foreground=p["text"])  # labels på paneler

        style.configure("TLabelframe", background=p["panel"], relief="flat")
        style.configure("TLabelframe.Label", background=p["panel"], foreground=p["subtle"], font=("Segoe UI", 10, "bold"))

        # Knappestiler
        style.configure("TButton", padding=8, background=p["muted"], foreground=p["text"])
        style.map("TButton", background=[("active", p["border"])])
        style.configure("Primary.TButton", padding=8, background=p["primary"], foreground=p["primary_fg"])
        style.map("Primary.TButton", background=[("active", p["primary"])], foreground=[("active", p["primary_fg"])])

        # Treeview (tabell)
        style.configure("Treeview",
                        background=p["table_bg"],
                        fieldbackground=p["table_bg"],
                        bordercolor=p["border"],
                        foreground=p["table_fg"],
                        rowheight=26)
        style.configure("Treeview.Heading",
                        background=p["table_head_bg"],
                        foreground=p["text"],
                        font=("Segoe UI", 10, "bold"))

        # Progressbar
        style.configure("Credit.Horizontal.TProgressbar", thickness=10)

    def _apply_runtime_colors(self):
        p = self.palettes[self.theme]
        if hasattr(self, "status"):
            self.status.configure(bg=p["panel"], fg=p["subtle"], bd=1)

    # ----- Layout -----
    def _build_ui(self):
        # Menylinje
        self._build_menubar()

        # Header
        header = ttk.Frame(self, style="TFrame")
        header.pack(side=tk.TOP, fill=tk.X)
        self.title_label = ttk.Label(header, text="Studieplan", style="Header.TLabel")
        self.title_label.pack(side=tk.LEFT, padx=16, pady=(14, 6))
        self.subtitle_label = ttk.Label(header, text="Administrer emner og plan – mørk/lys modus", style="Subheader.TLabel")
        self.subtitle_label.pack(side=tk.LEFT, padx=(8, 16), pady=(18, 6))

        # Toolbar
        toolbar = ttk.Frame(self, style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=12, pady=6)
        ttk.Button(toolbar, text="➕ Nytt emne (Ctrl+N)", command=self.open_add_course_dialog, style="Primary.TButton").pack(side=tk.LEFT, padx=(4, 6))
        ttk.Button(toolbar, text="📥 Legg i semester", command=self.add_selected_course_to_selected_sem).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="🗑️ Slett emne", command=self.delete_selected_course).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="✅ Valider (F5)", command=self.validate_plan).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="💾 Lagre (Ctrl+S)", command=self.save_to_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="📂 Åpne (Ctrl+O)", command=self.load_from_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="🚪 Avslutt", command=self.on_close).pack(side=tk.RIGHT, padx=(6, 4))
        # Theme toggle
        self.theme_btn = ttk.Button(toolbar, text="🌙 Mørk", command=self.toggle_theme)
        self.theme_btn.pack(side=tk.RIGHT, padx=(6, 4))

        # Content area split
        content = ttk.Frame(self)
        content.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # Left panel (courses)
        left = ttk.Frame(content, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        ttk.Label(left, text="Registrerte emner", style="Subheader.TLabel").pack(anchor="w", padx=12, pady=(12, 0))

        self.course_tree = ttk.Treeview(left, columns=("kode", "semester", "stp"), show="headings")
        self.course_tree.heading("kode", text="Emnekode")
        self.course_tree.heading("semester", text="Semester")
        self.course_tree.heading("stp", text="Stp")
        self.course_tree.column("kode", width=160, anchor="w")
        self.course_tree.column("semester", width=90, anchor="center")
        self.course_tree.column("stp", width=60, anchor="e")
        self.course_tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Right panel (semesters)
        right = ttk.Frame(content)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure((0, 1, 2), weight=1)
        right.rowconfigure((0, 1), weight=1)

        self.sem_widgets = []  # list of dicts per semester: {frame, tree, progress, label}
        for i in range(6):
            r = i // 3
            c = i % 3
            sem_frame = ttk.Labelframe(right, text=f"Semester {i+1} – {self.model.term_for_semester_index(i)}", style="TLabelframe")
            sem_frame.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            sem_frame.columnconfigure(0, weight=1)
            sem_frame.rowconfigure(0, weight=1)

            tree = ttk.Treeview(sem_frame, columns=("kode", "stp"), show="headings", height=6)
            tree.heading("kode", text="Emnekode")
            tree.heading("stp", text="Stp")
            tree.column("kode", anchor="w")
            tree.column("stp", width=60, anchor="e")
            tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

            pb = ttk.Progressbar(sem_frame, style="Credit.Horizontal.TProgressbar", orient="horizontal", mode="determinate", maximum=30)
            pb.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 4))

            info = ttk.Label(sem_frame, text="0/30 stp", style="Subheader.TLabel")
            info.grid(row=2, column=0, sticky="e", padx=8, pady=(0, 8))

            rowf = ttk.Frame(sem_frame, style="Panel.TFrame")
            rowf.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))
            rowf.columnconfigure((0, 1), weight=1)
            ttk.Button(rowf, text="➖ Fjern valgt", command=lambda idx=i: self.remove_selected_from_semester(idx)).grid(row=0, column=0, sticky="ew", padx=(0, 4))
            ttk.Button(rowf, text="🧹 Tøm", command=lambda idx=i: self.clear_semester(idx)).grid(row=0, column=1, sticky="ew", padx=(4, 0))

            self.sem_widgets.append({"frame": sem_frame, "tree": tree, "progress": pb, "label": info})

        # Status bar
        self.status = tk.Label(self, text="Klar", anchor="w")
        self.status.pack(side=tk.BOTTOM, fill=tk.X)
        self._apply_runtime_colors()

        self.refresh_all()

    def _build_menubar(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Ny", command=self.new_file)
        filemenu.add_separator()
        filemenu.add_command(label="Åpne...", accelerator="Ctrl+O", command=self.load_from_file)
        filemenu.add_command(label="Lagre", accelerator="Ctrl+S", command=self.save_to_file)
        filemenu.add_separator()
        filemenu.add_command(label="Avslutt", command=self.on_close)
        menubar.add_cascade(label="Fil", menu=filemenu)
        self.config(menu=menubar)

    # ----- Shortcuts -----
    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self.open_add_course_dialog())
        self.bind_all("<Control-s>", lambda e: self.save_to_file())
        self.bind_all("<Control-o>", lambda e: self.load_from_file())
        self.bind_all("<F5>", lambda e: self.validate_plan())

    # ----- Data helpers -----
    def refresh_courses(self):
        self.course_tree.delete(*self.course_tree.get_children())
        for c in self.model.courses:
            self.course_tree.insert("", "end", iid=str(c["id"]), values=(c["kode"], c["semester"], c["stp"]))

    def refresh_semester(self, idx):
        w = self.sem_widgets[idx]
        tree = w["tree"]
        tree.delete(*tree.get_children())
        total = 0
        for cid in self.model.plan[idx]:
            c = self.model.get_course(cid)
            if c:
                tree.insert("", "end", iid=f"{idx}-{cid}", values=(c["kode"], c["stp"]))
                total += c["stp"]
        w["progress"]["value"] = total
        w["label"].configure(text=f"{total}/30 stp")

    def refresh_all(self):
        self.refresh_courses()
        for i in range(6):
            self.refresh_semester(i)

    def get_selected_course_id(self):
        sel = self.course_tree.selection()
        if not sel:
            return None
        return int(sel[0])

    def get_focused_semester_index(self):
        focus_widget = self.focus_get()
        for i, w in enumerate(self.sem_widgets):
            if focus_widget in (w["tree"],):
                return i
        return None

    # ----- Theme Toggle -----
    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._setup_style()
        self._apply_runtime_colors()
        self.title_label.configure(style="Header.TLabel")
        self.subtitle_label.configure(style="Subheader.TLabel")
        self.theme_btn.configure(text="🌙 Mørk" if self.theme == "light" else "☀️ Lys")
        self.refresh_all()

    # ----- Actions -----
    def open_add_course_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Nytt emne")
        dlg.transient(self)
        dlg.grab_set()

        frm = ttk.Frame(dlg, style="Panel.TFrame")
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Emnekode").grid(row=0, column=0, sticky="w", pady=4)
        kode_var = tk.StringVar()
        ttk.Entry(frm, textvariable=kode_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Semester").grid(row=1, column=0, sticky="w", pady=4)
        sem_var = tk.StringVar(value="høst")
        ttk.Combobox(frm, textvariable=sem_var, values=["høst", "vår"], state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Studiepoeng").grid(row=2, column=0, sticky="w", pady=4)
        stp_var = tk.StringVar(value="10")

        # Valider kun heltall 1–30 i inputfelt
        def _validate_stp(P):  # P = proposed value
            if P == "":
                return True
            if not P.isdigit():
                return False
            v = int(P)
            return 1 <= v <= 30
        vcmd = (self.register(_validate_stp), '%P')
        ttk.Entry(frm, textvariable=stp_var, validate='key', validatecommand=vcmd).grid(row=2, column=1, sticky="ew", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Avbryt", command=dlg.destroy).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btns, text="Lagre", style="Primary.TButton", command=lambda: self._submit_new_course(dlg, kode_var, sem_var, stp_var)).pack(side=tk.RIGHT)

        dlg.wait_window(dlg)

    def _submit_new_course(self, dlg, kode_var, sem_var, stp_var):
        try:
            kode = kode_var.get().strip()
            sem = sem_var.get().strip()
            stp_str = stp_var.get().strip()
            if not kode:
                raise ValueError("Emnekode kan ikke være tom.")
            if not stp_str.isdigit():
                raise ValueError("Studiepoeng må være et heltall (1–30).")
            stp = int(stp_str)
            self.model.add_course(kode, sem, stp)
            self.refresh_courses()
            self._set_status("Emne lagt til", kind="success")
            self._dirty = True
            dlg.destroy()
        except Exception as e:
            messagebox.showerror("Kunne ikke opprette emne", str(e), parent=dlg)
            self._set_status(str(e), kind="danger")

    def add_selected_course_to_selected_sem(self):
        cid = self.get_selected_course_id()
        if not cid:
            messagebox.showinfo("Velg emne", "Marker et emne i lista først.")
            return
        sem_idx = self.get_focused_semester_index()
        if sem_idx is None:
            sem_idx = self._ask_semester()
            if sem_idx is None:
                return
        try:
            self.model.add_course_to_semester(cid, sem_idx)
            self.refresh_semester(sem_idx)
            self._set_status(f"La til emne i semester {sem_idx+1}", kind="success")
            self._dirty = True
        except Exception as e:
            messagebox.showerror("Kan ikke legge til emne", str(e))
            self._set_status(str(e), kind="danger")

    def delete_selected_course(self):
        cid = self.get_selected_course_id()
        if not cid:
            messagebox.showinfo("Velg emne", "Marker et emne i lista først.")
            return
        c = self.model.get_course(cid)
        if not c:
            return
        if not messagebox.askyesno("Slett emne", f"Vil du slette {c['kode']}? Emnet fjernes også fra studieplanen."):
            return
        try:
            self.model.delete_course(cid)
            self.refresh_all()
            self._set_status(f"Slettet emne {c['kode']}", kind="warning")
            self._dirty = True
        except Exception as e:
            messagebox.showerror("Feil ved sletting", str(e))
            self._set_status(str(e), kind="danger")

    def remove_selected_from_semester(self, sem_idx):
        tree = self.sem_widgets[sem_idx]["tree"]
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        try:
            cid = int(iid.split("-")[1])
        except Exception:
            return
        self.model.remove_course_from_semester(cid, sem_idx)
        self.refresh_semester(sem_idx)
        self._set_status(f"Fjernet emne fra semester {sem_idx+1}", kind="warning")
        self._dirty = True

    def clear_semester(self, sem_idx):
        if messagebox.askyesno("Tøm semester", f"Vil du fjerne alle emner fra semester {sem_idx+1}?"):
            self.model.clear_semester(sem_idx)
            self.refresh_semester(sem_idx)
            self._set_status(f"Tømte semester {sem_idx+1}", kind="warning")
            self._dirty = True

    def validate_plan(self):
        invalid = self.model.validate_plan()
        if not invalid:
            messagebox.showinfo("Gyldig plan", "Alle semestre har 30 stp. Flott!")
            self._set_status("Planen er gyldig", kind="success")
        else:
            lines = [f"- Semester {i+1} ({self.model.term_for_semester_index(i)}): {tot} stp" for i, tot in invalid]
            messagebox.showwarning("Ugyldig plan", "Disse semestrene er ikke 30 stp:\n" + "\n".join(lines))
            self._set_status("Planen er ikke gyldig", kind="danger")

    # ----- Filoperasjoner -----
    def save_to_file(self):
        path = filedialog.asksaveasfilename(title="Lagre studieplan", defaultextension=".json", filetypes=[("JSON", "*.json"), ("Alle filer", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.model.to_json(), f, ensure_ascii=False, indent=2)
            self._set_status(f"Lagret til {path}", kind="success")
            self._dirty = False
            self.current_file = path
        except Exception as e:
            messagebox.showerror("Feil ved lagring", str(e))
            self._set_status(str(e), kind="danger")

    def load_from_file(self):
        path = filedialog.askopenfilename(title="Åpne studieplan", filetypes=[("JSON", "*.json"), ("Alle filer", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.model.load_json(data)
            self.refresh_all()
            self._set_status(f"Lest fra {path}", kind="success")
            self._dirty = False
            self.current_file = path
        except Exception as e:
            messagebox.showerror("Feil ved lesing", str(e))
            self._set_status(str(e), kind="danger")

    def new_file(self):
        if self._dirty:
            if not messagebox.askyesno("Ny", "Ulagrede endringer vil gå tapt. Fortsette?"):
                return
        self.model = Model()
        self.refresh_all()
        self._set_status("Ny plan opprettet", kind="info")
        self._dirty = False
        self.current_file = None

    def on_close(self):
        if self._dirty:
            if not messagebox.askyesno("Avslutt", "Du har ulagrede endringer. Avslutte likevel?"):
                return
        self.destroy()

    def _ask_semester(self):
        dlg = tk.Toplevel(self)
        dlg.title("Velg semester")
        dlg.transient(self)
        dlg.grab_set()
        frm = ttk.Frame(dlg, style="Panel.TFrame")
        frm.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        ttk.Label(frm, text="Velg semester (1–6)").pack(anchor="w")
        var = tk.IntVar(value=1)
        cb = ttk.Combobox(frm, textvariable=var, values=[1, 2, 3, 4, 5, 6], state="readonly", width=6)
        cb.pack(anchor="w", pady=8)
        ttk.Button(frm, text="OK", command=dlg.destroy, style="Primary.TButton").pack(anchor="e")
        self.wait_window(dlg)
        val = var.get()
        return val - 1 if 1 <= val <= 6 else None

    def _set_status(self, text, kind="info"):
        p = self.palettes[self.theme]
        colors = {
            "info": p["subtle"],
            "success": p["success"],
            "warning": p["warning"],
            "danger": p["danger"],
        }
        self.status.configure(text=text, fg=colors.get(kind, p["subtle"]))

    def _seed_examples(self):
        try:
            self.model.add_course("MAT100", "høst", 10)
            self.model.add_course("DAT120", "høst", 10)
            self.model.add_course("FYS102", "høst", 5)
            self.model.add_course("KJE101", "høst", 5)
            self.model.add_course("ELE100", "høst", 10)
            self.model.add_course("MAT200", "vår", 10)
            self.model.add_course("DAT130", "vår", 10)
            self.model.add_course("ELE130", "vår", 10)
            self.model.add_course("ELE140", "vår", 10)
            self.model.add_course("BIO110", "vår", 10)
            self.model.add_course("DAT200", "høst", 10)
            self.model.add_course("DAT250", "høst", 10)
            self.model.add_course("DAT320", "høst", 10)
            self.model.add_course("MTE200", "høst", 10)
            self.model.add_course("MTE210", "høst", 10)

            self.refresh_all()
        except Exception:
            pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
