"""Exercise the real subprocess boundary without network or model generation."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from src.codex_cli import CodexCLI
from src.debate_graph import DebateOrchestrator
from src.models import DebateInput, DebateOutput


class CodexCLITests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="test-debate-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.calls_file = self.root / "calls.json"
        self.executable = self.root / "fake codex"
        self.executable.write_text(
            f"#!{sys.executable}\n" + r'''
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
record = Path(os.environ["FAKE_CODEX_CALLS"])
calls = json.loads(record.read_text()) if record.exists() else []
calls.append({
    "args": args,
    "prompt": sys.stdin.read(),
    "api_keys_present": [key for key in
                         ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY")
                         if key in os.environ],
})
record.write_text(json.dumps(calls))
print("CLI progress: this must never enter the debate transcript")
print("CLI diagnostic", file=sys.stderr)
mode = os.environ.get("FAKE_CODEX_MODE", "success")
if mode == "failure":
    sys.exit(17)
output = Path(args[args.index("--output-last-message") + 1])
if mode == "missing":
    sys.exit(0)
if mode == "empty":
    output.write_text(" \n\t")
elif len(calls) == 9:
    output.write_text("JUDGMENT: Supported conclusion\n\nREASONING: Both sides considered.\n\nCONFIDENCE: 0.85\n")
else:
    output.write_text(f"  Argument {len(calls)}: café\n")
''', encoding="utf-8")
        self.executable.chmod(0o700)
        self.environment = patch.dict(os.environ, {"FAKE_CODEX_CALLS": str(self.calls_file)})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY", "FAKE_CODEX_MODE"):
            os.environ.pop(key, None)

    def calls(self):
        return json.loads(self.calls_file.read_text(encoding="utf-8"))

    def assert_outputs_cleaned(self):
        for call in self.calls():
            args = call["args"]
            output = Path(args[args.index("--output-last-message") + 1])
            self.assertFalse(output.parent.exists())

    def test_complete_keyless_debate_preserves_all_turns_and_history(self):
        sentinel = self.root / "shell-was-executed"
        question = f'Is this safe? $(touch "{sentinel}") `touch "{sentinel}";\n雪'
        context = 'Literal context: "$HOME"; \'quoted\' & <data>'
        result = DebateOrchestrator(codex_executable=str(self.executable)).run_debate(
            DebateInput(question=question, context=context)
        )
        self.assertIsInstance(result, DebateOutput)
        self.assertEqual(result.final_judgment, "Supported conclusion")
        self.assertEqual(result.reasoning, "Both sides considered.")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(len(result.debate_log), 8)
        self.assertEqual([m.message for m in result.debate_log],
                         [f"Argument {i}: café" for i in range(1, 9)])
        self.assertEqual([m.agent for m in result.debate_log],
                         ["Agent 1 (Analytical)", "Agent 2 (Philosophical)"] * 4)
        # Preserve the existing graph's round numbering, including the final round 5.
        self.assertEqual([m.round for m in result.debate_log], [1, 1, 2, 2, 3, 3, 4, 5])
        calls = self.calls()
        self.assertEqual(len(calls), 9)
        for index, call in enumerate(calls):
            args, prompt = call["args"], call["prompt"]
            self.assertEqual(args[0], "exec")
            self.assertEqual(args[-1], "-")
            self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
            self.assertNotIn("--model", args)
            self.assertNotIn("claude", " ".join(args).lower())
            self.assertNotIn(question, args)
            self.assertIn(question, prompt)
            self.assertIn(context, prompt)
            if index < 8:
                self.assertTrue(prompt.startswith(f"You are Agent {index % 2 + 1} "))
            else:
                self.assertTrue(prompt.startswith("You are an impartial judge"))
            for prior in range(1, index + 1):
                self.assertIn(f"Argument {prior}: café", prompt)
            self.assertNotIn(f"Argument {index + 1}: café", prompt)
            self.assertNotIn("CLI progress", prompt)
        self.assertFalse(sentinel.exists())
        self.assert_outputs_cleaned()

    def test_optional_codex_model_is_a_single_argument(self):
        model = "test-model; literal"
        result = CodexCLI(str(self.executable), model=model).invoke("test prompt")
        self.assertEqual(result, "Argument 1: café")
        args = self.calls()[0]["args"]
        self.assertEqual(args[args.index("--model") + 1], model)
        self.assert_outputs_cleaned()

    def test_example_entry_point_runs_keyless_and_saves_judgment(self):
        project_root = Path(__file__).resolve().parent.parent
        # Keep the script-relative output entirely inside test-owned storage.
        script = self.root / "examples" / "run_debate.py"
        script.parent.mkdir()
        shutil.copyfile(project_root / "examples" / "run_debate.py", script)
        (self.root / "codex").symlink_to(self.executable)
        environment = os.environ.copy()
        environment.update({
            "PATH": str(self.root) + os.pathsep + environment.get("PATH", ""),
            "PYTHONPATH": str(project_root),
            "PYTHONIOENCODING": "utf-8",
            "PYTHON_DOTENV_DISABLED": "1",
        })
        completed = subprocess.run(
            [sys.executable, str(script)], cwd=self.root, env=environment,
            capture_output=True, text=True, encoding="utf-8", check=True,
            timeout=30,
        )
        calls = self.calls()
        self.assertEqual(len(calls), 9)
        self.assertTrue(all(call["api_keys_present"] == [] for call in calls))
        self.assertIn("Is blockchain technology essential", calls[0]["prompt"])
        self.assertTrue(calls[-1]["prompt"].startswith("You are an impartial judge"))

        saved_path = script.parent / "debate_output.json"
        saved = json.loads(saved_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["final_judgment"], "Supported conclusion")
        self.assertEqual(saved["reasoning"], "Both sides considered.")
        self.assertEqual(saved["confidence"], 0.85)
        self.assertEqual(len(saved["debate_log"]), 8)
        self.assertIn("DEBATE TRANSCRIPT", completed.stdout)
        for index, message in enumerate(saved["debate_log"], start=1):
            self.assertEqual(message["message"], f"Argument {index}: café")
            self.assertIn(f'{message["agent"]}:\n{message["message"]}', completed.stdout)
        self.assertIn("FINAL JUDGMENT", completed.stdout)
        self.assertIn("DECISION: Supported conclusion", completed.stdout)
        self.assertIn("REASONING:\nBoth sides considered.", completed.stdout)
        self.assertIn("CONFIDENCE: 0.85", completed.stdout)
        self.assertIn(f"Full output saved to: {saved_path}", completed.stdout)
        self.assertNotIn("CLI progress", completed.stdout)
        self.assert_outputs_cleaned()

    def test_default_executable_is_found_on_path(self):
        executable = self.root / "codex"
        executable.symlink_to(self.executable)
        with patch.dict(os.environ, {"PATH": str(self.root) + os.pathsep + os.environ.get("PATH", "")}):
            self.assertEqual(CodexCLI().invoke("test"), "Argument 1: café")

    def test_empty_or_missing_final_message_stops_debate(self):
        for mode in ("empty", "missing"):
            with self.subTest(mode=mode):
                self.calls_file.write_text("[]")
                with patch.dict(os.environ, {"FAKE_CODEX_MODE": mode}):
                    with self.assertRaisesRegex(ValueError, "final assistant message"):
                        DebateOrchestrator(codex_executable=str(self.executable)).run_debate(
                            {"question": "test"}
                        )
                self.assertEqual(len(self.calls()), 1)
                self.assert_outputs_cleaned()

    def test_nonzero_exit_does_not_become_a_debate_message(self):
        with patch.dict(os.environ, {"FAKE_CODEX_MODE": "failure"}):
            with self.assertRaises(subprocess.CalledProcessError) as error:
                DebateOrchestrator(codex_executable=str(self.executable)).run_debate(
                    {"question": "test"}
                )
        self.assertEqual(error.exception.returncode, 17)
        self.assertEqual(len(self.calls()), 1)
        self.assert_outputs_cleaned()


if __name__ == "__main__":
    unittest.main()
