# llmPy
Python API for Large-Language-Models

## Setup
1. Build the docker image in `backend/interpreter`
2. Copy `.env.example` to `.env` and set SHA256 of admin key
3. Create 3 Plugins (from js 1 to 3 and specs 1 to 3) in TM
4. Create Agent with 3 plugins and prompt
5. Run main.py after installing requierements (or use the nix run)