# Scripts Directory

Utility scripts for the Smart Cities project.

## Available Scripts

### commands_linux.sh
Basic conda environment commands for Linux/WSL environments.

```bash
# Source the script or run directly
source commands_linux.sh
```

## Adding New Scripts

Scripts in this directory should:
- Be executable (`chmod +x script.sh`)
- Have clear usage documentation
- Follow naming convention: `action_target.sh` (e.g., `setup_environment.sh`)

## Suggested Future Scripts

- `run_simulation.sh` - Execute SUMO simulation
- `import_data.sh` - Run the XML importer
- `run_analysis.sh` - Execute PySpark notebooks
- `setup_all.sh` - Full environment setup
