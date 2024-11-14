from typing import Literal
from config import config


def embedding_device(device: str = None) -> Literal["cuda", "mps", "cpu"]:
    device = device or config.device
    if device not in ["cuda", "mps", "cpu"]:
        device = "cpu"
    return device


def average_split(data: list, step: int) -> list:
    return [
        data[start: start+step]
        for start in range(len(data))[::step]
    ]