class BaseWindow:
    id: int
    priority: int
    # title: str
    # classes: list[str]
    # pid: int
    # geometry: list[int] # x, y, w, h
    # flags: list[str]

    # def get_geometry_str(self) -> str:
    #     return f"{self.geometry[0]}x{self.geometry[1]}+{-1 * self.geometry[2]},{-1 * self.geometry[3]}"
    def get_geometry_str(self) -> str:
        raise NotImplementedError()

    def serialize(self) -> dict:
        return {
            "id": hex(self.id),
            "priority": self.priority,
            "title": self.get_title(),
            "classes": self.get_classes(),
            "pid": self.get_pid(),
            "geom": self.get_geometry(),
            "flags": self.get_flags(),
        }

    def get_title(self, *args) -> str:
        raise NotImplementedError()

    def get_classes(self) -> list:
        raise NotImplementedError()

    def get_pid(self) -> int:
        raise NotImplementedError()

    def get_flags(self) -> list[str]:
        raise NotImplementedError()

    def get_geometry(self) -> dict[str, int]:
        raise NotImplementedError()
