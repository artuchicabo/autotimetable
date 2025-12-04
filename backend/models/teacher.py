class Teacher:
    def __init__(self, teacher_id, teacher_name, password="12345", role="teacher"):
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.password = str(password)
        self.role = role

    def to_dict(self):
        return {
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher_name,
            "role": self.role
        }

