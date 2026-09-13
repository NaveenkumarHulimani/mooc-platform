import requests

PISTON_BASE_URL = "http://localhost:2000/api/v2"

# language key used across this app -> Piston's (language, version, filename)
LANGUAGE_CONFIG = {
    "python": {"language": "python", "version": "3.12.0", "filename": "main.py"},
    "java": {"language": "java", "version": "15.0.2", "filename": "Main.java"},
    "c": {"language": "c", "version": "10.2.0", "filename": "main.c"},
    "javascript": {"language": "javascript", "version": "20.11.1", "filename": "main.js"},
}


class ExecutionError(Exception):
    pass


def run_code(source_code: str, stdin: str, language: str = "python", timeout_seconds: float = 20.0) -> dict:
    """Submit code to a locally self-hosted Piston instance and return its raw result dict."""
    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        raise ExecutionError(f"Unsupported language: {language}")

    try:
        resp = requests.post(
            f"{PISTON_BASE_URL}/execute",
            json={
                "language": config["language"],
                "version": config["version"],
                "files": [{"name": config["filename"], "content": source_code}],
                "stdin": stdin,
            },
            timeout=timeout_seconds,
        )
    except requests.exceptions.ConnectionError as exc:
        raise ExecutionError(
            "Could not reach the local Piston code-execution service at "
            f"{PISTON_BASE_URL}. Make sure the piston_api Docker container is running "
            "(docker start piston_api)."
        ) from exc
    except requests.exceptions.Timeout as exc:
        raise ExecutionError("Timed out waiting for Piston to execute the code.") from exc

    if resp.status_code >= 400:
        raise ExecutionError(f"Piston execution failed ({resp.status_code}): {resp.text}")

    return resp.json()


def evaluate_against_test_cases(source_code: str, test_cases: list[dict], language: str = "python") -> dict:
    """Runs source_code against each test case and returns a verdict summary."""
    results = []
    for i, case in enumerate(test_cases):
        expected = (case.get("expected_output") or "").strip()
        piston_result = run_code(source_code, case.get("input", ""), language=language)

        compile_stage = piston_result.get("compile") or {}
        run_stage = piston_result.get("run") or {}

        compile_output = ""
        if compile_stage.get("code") not in (None, 0):
            compile_output = compile_stage.get("stderr") or compile_stage.get("output") or "Compile error"
            status_description = "Compile Error"
        elif run_stage.get("signal"):
            status_description = f"Runtime Error (signal {run_stage['signal']})"
        elif run_stage.get("code") not in (None, 0):
            status_description = "Runtime Error"
        else:
            status_description = "Accepted"

        stdout = (run_stage.get("stdout") or "").strip()
        stderr = run_stage.get("stderr") or ""

        passed = status_description == "Accepted" and stdout == expected
        results.append(
            {
                "case_index": i,
                "passed": passed,
                "status": status_description,
                "expected_output": expected,
                "actual_output": stdout,
                "stderr": stderr,
                "compile_output": compile_output,
            }
        )

    all_passed = all(r["passed"] for r in results) if results else False
    passed_count = sum(1 for r in results if r["passed"])
    score = round((passed_count / len(results)) * 100) if results else 0

    return {
        "verdict": "PASS" if all_passed else "FAIL",
        "score": score,
        "passed_count": passed_count,
        "total_count": len(results),
        "cases": results,
    }
