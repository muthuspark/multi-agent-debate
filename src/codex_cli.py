"""Noninteractive inference using the user's authenticated Codex CLI."""

from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory


class CodexCLI:
    """Return final assistant text, excluding CLI progress and diagnostics."""

    def __init__(self, executable: str = "codex", model: str | None = None):
        self.executable = executable
        self.model = model

    def invoke(self, prompt: str) -> str:
        with TemporaryDirectory(prefix="debate-codex-") as directory:
            output = Path(directory) / "final.txt"
            command = [
                self.executable, "exec", "--sandbox", "read-only",
                "--skip-git-repo-check", "--output-last-message", str(output),
            ]
            if self.model is not None:
                command.extend(["--model", self.model])
            command.append("-")
            # Never interpolate debate text into a command or parse CLI stdout.
            subprocess.run(
                command, input=prompt, text=True, encoding="utf-8",
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                check=True, timeout=300,
            )
            if not output.is_file():
                raise ValueError("Codex CLI did not produce a final assistant message")
            message = output.read_text(encoding="utf-8").strip()
            if not message:
                raise ValueError("Codex CLI returned an empty final assistant message")
            return message
