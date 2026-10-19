from dataclasses import asdict, dataclass, field


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str] = field(default_factory=list)
    author_url: str | None = None

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("El texto de la cita no puede estar vacío")
        if not self.author.strip():
            raise ValueError("El autor de la cita no puede estar vacío")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Author:
    name: str
    url: str
    born_date: str | None = None
    born_location: str | None = None
    description: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
