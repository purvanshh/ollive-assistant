import os
import sys
import tempfile
import subprocess
from typing import Tuple

def run_python_code(code: str) -> Tuple[str, str]:
    """
    Execute python code safely in a sandbox using E2B if configured,
    or a secure local subprocess execution fallback with a 5-second timeout.
    """
    e2b_key = os.getenv("E2B_API_KEY")
    if e2b_key:
        try:
            from e2b_code_interpreter import Sandbox
            with Sandbox(api_key=e2b_key) as sandbox:
                execution = sandbox.run_code(code)
                return execution.stdout or "", execution.stderr or ""
        except Exception as e:
            # Fall back to local execution if E2B fails
            print(f"E2B Sandbox execution failed: {e}. Falling back to local execution.")

    # Local fallback execution
    f_name = None
    try:
        # Create a temp python file containing the code
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            f_name = f.name

        # Execute using the current python interpreter
        # Timeout strictly at 5.0 seconds
        # -u: force unbuffered stdout and stderr
        res = subprocess.run(
            [sys.executable, "-u", f_name],
            capture_output=True,
            text=True,
            timeout=5.0
        )
        
        stdout = res.stdout or ""
        stderr = res.stderr or ""
        
        # Clean up temp file
        try:
            os.unlink(f_name)
        except Exception:
            pass
            
        # Sanitize path references to keep outputs clean
        stdout = stdout.replace(f_name, "sandbox.py")
        stderr = stderr.replace(f_name, "sandbox.py")
        
        return stdout, stderr

    except subprocess.TimeoutExpired as te:
        try:
            if f_name:
                os.unlink(f_name)
        except Exception:
            pass
        stdout_str = te.stdout.decode("utf-8", errors="ignore") if isinstance(te.stdout, bytes) else (te.stdout or "")
        stderr_str = te.stderr.decode("utf-8", errors="ignore") if isinstance(te.stderr, bytes) else (te.stderr or "")
        return stdout_str, stderr_str + "\nTimeoutExpired: Code execution exceeded the limit of 5.0 seconds."
    except Exception as e:
        try:
            if f_name:
                os.unlink(f_name)
        except Exception:
            pass
        return "", f"Execution Error: {e}"

if __name__ == "__main__":
    test_code = "print('Hello from sandbox!')\nimport sys\nprint('Python:', sys.version)"
    out, err = run_python_code(test_code)
    print("STDOUT:", out)
    print("STDERR:", err)
