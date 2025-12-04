class StudentGroup:
    def __init__(self, group_id, group_name, student_count, advisor):
        self.group_id = group_id
        self.group_name = group_name
        self.student_count = int(student_count)
        self.advisor = advisor

    def to_dict(self):
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "student_count": self.student_count,
            "advisor": self.advisor
        }
