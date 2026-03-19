import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from autoscaler.scaling import start as start_scaling_loop
from autoscaler.app import app

if __name__ == "__main__":
    import os
    start_scaling_loop()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)), debug=False)
