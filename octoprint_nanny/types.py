from dataclasses import dataclass

@dataclass
class Image:
    height: int
    width: int
    data: bytes
