# Setup for VS Code

This folder contains VS Code configuration for the autonomous-agent project.

## Quick start

1. Install recommended extensions:
   - Open the Extensions view and search for `@recommended`
   - Install all recommended extensions

2. Create and activate the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run tests:
   - Press `Ctrl+Shift+D` (or `Cmd+Shift+D` on macOS) to open Debug view
   - Select "Run Tests" from the dropdown
   - Press `F5` or click the Run button

4. Run the agent:
   - Select "Run Agent" from the Debug dropdown
   - Press `F5`

5. Debug the agent:
   - Select "Debug Agent" from the Debug dropdown
   - Set breakpoints by clicking on line numbers
   - Press `F5`

## Configuration

- `settings.json`: Python formatter, linter, and editor settings
- `launch.json`: Debug configurations for running and testing
- `extensions.json`: Recommended extensions for the project

## Keyboard shortcuts

- `F5`: Start debugging / Run selected configuration
- `Ctrl+Shift+D`: Open Debug view
- `Ctrl+Shift+```: Open integrated terminal
- `Shift+Alt+F`: Format document (if Black is installed)

## Environment

All debug configurations use a safe set of environment variables. Edit them in `launch.json` to customize:

```json
"env": {
  "AUTO_AGENT_ALLOWED_DOMAINS": "example.com",
  "AUTO_AGENT_MAX_PER_CYCLE": "5",
  "AUTO_AGENT_FETCH_BUDGET_PER_DAY": "100",
  "AUTO_AGENT_TOKEN_BUDGET_PER_DAY": "200000"
}
```
