class Timeslot:
    def __init__(self, timeslot_id, day, period, start, end):
        self.timeslot_id = timeslot_id
        self.day = day
        self.period = int(period)
        self.start = start
        self.end = end

    def to_dict(self):
        return {
            "timeslot_id": self.timeslot_id,
            "day": self.day,
            "period": self.period,
            "start": self.start,
            "end": self.end
        }
