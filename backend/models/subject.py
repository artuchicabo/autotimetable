class Subject:
    def __init__(self, subject_id, subject_name, theory, practice, credit):
        self.subject_id = subject_id
        self.subject_name = subject_name
        self.theory = int(theory)
        self.practice = int(practice)
        self.credit = int(credit)

    def total_hours(self):
        return self.theory + self.practice

    def to_dict(self):
        return {
            "subject_id": self.subject_id,
            "subject_name": self.subject_name,
            "theory": self.theory,
            "practice": self.practice,
            "credit": self.credit
        }
