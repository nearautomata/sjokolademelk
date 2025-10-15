import json

# -----------------------------------------------------
# Studieplan – Terminalversjon
# 6 semestre, 30 stp per semester,
#   høst: sem 1/3/5, vår: sem 2/4/6, emner kan kun legges én gang
# - Lagrer/leser JSON (studieplan.json default)
# -----------------------------------------------------

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
        if stp <= 0 or stp > 30:
            raise ValueError("Studiepoeng må være mellom 1 og 30.")
        c = {"id": self._next_id, "kode": kode.strip(), "semester": semester.strip(), "stp": int(stp)}
        self._next_id += 1
        self.courses.append(c)
        return c

    def get_course(self, cid):
        return next((c for c in self.courses if c["id"] == cid), None)

    def find_course_by_code(self, kode):
        return next((c for c in self.courses if c["kode"].lower() == kode.lower()), None)

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
        self._next_id = int(data.get("next_id", 1))
        self.courses = list(data.get("courses", []))
        self.plan = [list(s) for s in data.get("plan", [[] for _ in range(6)])]
        valid_ids = {c["id"] for c in self.courses}
        for i in range(6):
            self.plan[i] = [cid for cid in self.plan[i] if cid in valid_ids]


# ---------------- Terminal UI ----------------

def print_header():
    print("\n=== STUDIEPLAN (terminal) ===")

def list_courses(model: Model):
    if not model.courses:
        print("(ingen emner registrert)")
        return
    print("\nEmner:")
    for c in model.courses:
        print(f"- {c['kode']}  ({c['semester']}, {c['stp']} stp)")

def list_plan(model: Model):
    print("\nStudieplan:")
    for i, sem in enumerate(model.plan):
        term = model.term_for_semester_index(i)
        total = model.total_credits(i)
        print(f"Semester {i+1} ({term}) – {total}/30 stp")
        if not sem:
            print("  (tomt)")
        else:
            for cid in sem:
                c = model.get_course(cid)
                if c:
                    print(f"  - {c['kode']} ({c['stp']} stp)")

def add_course_flow(model: Model):
    try:
        kode = input("Emnekode: ").strip()
        semester = input("Semester (høst/vår): ").strip().lower()
        stp = int(input("Studiepoeng: ").strip())
        model.add_course(kode, semester, stp)
        print("✅ Emne lagt til!")
    except Exception as e:
        print("❌", e)

def add_to_plan_flow(model: Model):
    if not model.courses:
        print("Ingen emner registrert. Legg til emner først.")
        return
    kode = input("Emnekode som skal legges i plan: ").strip()
    course = model.find_course_by_code(kode)
    if not course:
        print("❌ Emne ikke funnet.")
        return
    try:
        sem = int(input("Semester (1–6): ").strip()) - 1
        if sem < 0 or sem > 5:
            print("❌ Ugyldig semester.")
            return
        model.add_course_to_semester(course["id"], sem)
        print(f"✅ La {course['kode']} i semester {sem+1}.")
    except Exception as e:
        print("❌", e)

def validate_flow(model: Model):
    invalid = model.validate_plan()
    if not invalid:
        print("✅ Studieplanen er gyldig: 30 stp i alle semestre.")
    else:
        print("⚠️  Ikke gyldig. Disse semestrene mangler/overskrider 30 stp:")
        for i, tot in invalid:
            print(f"  - Semester {i+1} ({model.term_for_semester_index(i)}): {tot} stp")

def save_flow(model: Model):
    path = input("Filnavn (default: studieplan.json): ").strip() or "studieplan.json"
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(model.to_json(), f, ensure_ascii=False, indent=2)
        print(f"💾 Lagret til {path}")
    except Exception as e:
        print("❌", e)

def load_flow(model: Model):
    path = input("Filnavn (default: studieplan.json): ").strip() or "studieplan.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        model.load_json(data)
        print(f"📂 Lest fra {path}")
    except FileNotFoundError:
        print("❌ Fant ikke filen.")
    except Exception as e:
        print("❌", e)


def main():
    model = Model()

    # Eksempeldata (kan fjernes)
    try:
        model.add_course("MAT100", "høst", 10)
        model.add_course("DAT120", "høst", 10)
        model.add_course("FYS102", "høst", 5)
        model.add_course("KJE101", "høst", 5)
        model.add_course("MAT200", "vår", 10)
        model.add_course("DAT130", "vår", 10)
        model.add_course("ELE130", "vår", 10)
    except Exception:
        pass

    while True:
        print_header()
        print("1. Lag nytt emne")
        print("2. Legg til et emne i studieplanen")
        print("3. Skriv ut alle registrerte emner")
        print("4. Skriv ut studieplanen")
        print("5. Sjekk om studieplanen er gyldig")
        print("6. Lagre emnene og studieplanen til fil")
        print("7. Les inn emnene og studieplanen fra fil")
        print("8. Avslutt")
        choice = input("\nVelg: ").strip()

        if choice == "1":
            add_course_flow(model)
        elif choice == "2":
            add_to_plan_flow(model)
        elif choice == "3":
            list_courses(model)
        elif choice == "4":
            list_plan(model)
        elif choice == "5":
            validate_flow(model)
        elif choice == "6":
            save_flow(model)
        elif choice == "7":
            load_flow(model)
        elif choice == "8":
            print("Ha det!")
            break
        else:
            print("Ugyldig valg.")

if __name__ == "__main__":
    main()
