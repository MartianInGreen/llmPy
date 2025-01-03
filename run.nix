{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python312
    python312Packages.pip
    python312Packages.virtualenv
    python312Packages.numpy
    python312Packages.onnxruntime
    zlib
  ];

  shellHook = ''
    # Create and activate a virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
      python -m venv api
    fi
    source api/bin/activate

    # Install project-specific dependencies
    pip install -r requirements.txt

    # Function to check for git updates and restart Uvicorn
    check_and_update() {
        git fetch
        if [ "$(git rev-parse HEAD)" != "$(git rev-parse @{u})" ]; then
        echo "Update available. Pulling changes and restarting..."
        git pull
        kill $(pgrep -f "uvicorn")
        sleep 10
        uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload &
        fi
    }

    # Start the Uvicorn server without SSL
    uvicorn api.main:app --host 0.0.0.0 --port 5000 --reload &

    # Run the update check every 30 seconds
    while true; do
        sleep 30
        check_and_update
    done
  '';
}
