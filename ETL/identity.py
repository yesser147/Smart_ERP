"""
Generated identities. The sources are anonymous (the IBM file has no names,
the resumes are anonymised), but the app needs names, emails and phone
numbers to be usable. They are drawn from fixed lists with a fixed seed, so
every run produces the same people. They are identifiers only: no analysis
uses them.
"""

import numpy as np

FIRST_NAMES = {
    "Male": ["James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph", "Thomas",
             "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "Joshua",
             "Kevin", "Brian", "George", "Timothy", "Ryan", "Jacob", "Nicholas", "Eric", "Jonathan",
             "Samuel", "Omar", "Youssef", "Karim", "Mehdi", "Ahmed", "Luca", "Mateo", "Hugo", "Lucas",
             "Noah", "Ethan", "Adam", "Rayan", "Ivan", "Hiroshi", "Arjun", "Wei", "Diego", "Tariq",
             "Felix", "Victor", "Oscar"],
    "Female": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica",
               "Sarah", "Karen", "Lisa", "Nancy", "Sandra", "Ashley", "Emily", "Michelle", "Amanda",
               "Melissa", "Laura", "Rebecca", "Sharon", "Cynthia", "Amy", "Anna", "Nicole", "Emma",
               "Olivia", "Sophia", "Chloe", "Ines", "Yasmine", "Salma", "Amira", "Lina", "Sara",
               "Nour", "Camille", "Lea", "Manon", "Julia", "Elena", "Aiko", "Priya", "Mei", "Lucia",
               "Fatima", "Hana", "Clara", "Alice", "Zoe"],
}
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
              "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Clark", "Lewis",
              "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
              "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
              "Mitchell", "Carter", "Roberts", "Ben Ali", "Trabelsi", "Haddad", "Mansour", "Khalil",
              "Dubois", "Moreau", "Laurent", "Fontaine", "Rossi", "Russo", "Schmidt", "Muller",
              "Tanaka", "Sato", "Kim", "Park", "Chen", "Wang", "Patel", "Shah", "Singh", "Ivanov",
              "Novak", "Kowalski", "Silva", "Santos", "Costa", "Oliveira", "Jensen", "Larsen",
              "Nielsen", "O'Brien", "Murphy"]


class IdentityFactory:
    def __init__(self, seed: int, domain: str):
        self.rng = np.random.default_rng(seed)
        self.domain = domain
        self._used_emails = set()

    def name(self, gender: str | None = None) -> tuple[str, str]:
        if gender not in FIRST_NAMES:
            gender = "Male" if self.rng.random() < 0.5 else "Female"
        return str(self.rng.choice(FIRST_NAMES[gender])), str(self.rng.choice(LAST_NAMES))

    def email(self, first: str, last: str, domain: str | None = None) -> str:
        base = f"{first}.{last}".lower().replace(" ", "").replace("'", "")
        domain = domain or self.domain
        email, n = f"{base}@{domain}", 1
        while email in self._used_emails:
            n += 1
            email = f"{base}{n}@{domain}"
        self._used_emails.add(email)
        return email

    def phone(self) -> str:
        return f"+1-{self.rng.integers(200, 999)}-{self.rng.integers(200, 999)}-{self.rng.integers(1000, 9999)}"
