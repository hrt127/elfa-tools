# Auto-activate venv when entering a folder with .venv or venv
# Add this to your ~/.bashrc

cd() {
  builtin cd "$@" || return
  
  # Check for .venv first (preferred), then venv
  local venv_path=""
  if [ -f "./.venv/bin/activate" ]; then
    venv_path="$(realpath ./.venv)"
  elif [ -f "./venv/bin/activate" ]; then
    venv_path="$(realpath ./venv)"
  fi
  
  # If we found a venv in current directory
  if [ -n "$venv_path" ]; then
    # Only activate if not already activated, or if activated to a different venv
    if [ -z "$VIRTUAL_ENV" ] || [ "$VIRTUAL_ENV" != "$venv_path" ]; then
      source "$venv_path/bin/activate"
      echo "✅ Activated venv: $venv_path"
    fi
  else
    # No venv in current directory
    # Only deactivate if we're in a venv AND it's not a parent directory's venv
    if [ -n "$VIRTUAL_ENV" ]; then
      # Check if current directory is inside the venv directory
      local venv_parent="$(dirname "$VIRTUAL_ENV")"
      if [[ "$PWD" != "$venv_parent"* ]]; then
        # We've left the venv's directory tree, deactivate
        deactivate
        echo "🔴 Deactivated venv"
      fi
    fi
  fi
}

