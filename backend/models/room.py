class Room:
    def __init__(self, room_id, room_name):
        self.room_id = room_id
        self.room_name = room_name

    def to_dict(self):
        return {
            "room_id": self.room_id,
            "room_name": self.room_name
        }
