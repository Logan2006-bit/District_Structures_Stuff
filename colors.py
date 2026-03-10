RESET = "\033[0m"

COLORS = {
    "orange": "\033[38;5;208m",  # bright orange
    "blue":   "\033[38;5;33m",   # bright blue
}

def colorize(text: str, color: str) -> str:
    return f"{COLORS.get(color, '')}{text}{RESET}"
