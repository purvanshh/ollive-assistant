import pytest
import time
from backend.app.tools.code_execution import run_python_code

def test_run_python_code_success():
    code = "print('Hello world!')\nprint(123 + 456)"
    stdout, stderr = run_python_code(code)
    assert "Hello world!" in stdout
    assert "579" in stdout
    assert stderr == ""

def test_run_python_code_error():
    code = "import undefined_module"
    stdout, stderr = run_python_code(code)
    assert stdout == ""
    assert "ModuleNotFoundError" in stderr

def test_run_python_code_timeout():
    # Test strict 5-second timeout
    code = "import time\nprint('Starting...')\ntime.sleep(10)\nprint('Done!')"
    start_time = time.time()
    stdout, stderr = run_python_code(code)
    elapsed = time.time() - start_time
    
    # Verify execution finished in ~5-6 seconds, not 10
    assert elapsed < 7.5
    assert "TimeoutExpired" in stderr
    assert "Starting..." in stdout
    assert "Done!" not in stdout

def test_run_python_code_sanitization():
    code = "import sys\nprint(sys.argv[0])"
    stdout, stderr = run_python_code(code)
    # The absolute path should be sanitized to "sandbox.py"
    assert "sandbox.py" in stdout
