# Fix for Auto-Activate Venv in .bashrc

## The Problem

Your current `cd()` function deactivates the venv whenever you navigate to any directory that doesn't have a `.venv` folder, even if you're still within the project.

## The Solution

Replace your current `cd()` function in `~/.bashrc` with this improved version:

```bash
# Auto-activate venv when entering a folder with .venv or venv
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
    fi
  else
    # No venv in current directory
    # Only deactivate if we've left the project directory entirely
    if [ -n "$VIRTUAL_ENV" ]; then
      # Get the project root (parent of venv directory)
      local venv_dir="$(dirname "$VIRTUAL_ENV")"
      local project_root="$(dirname "$venv_dir")"
      
      # Check if current directory is still within the project
      if [[ "$PWD" != "$project_root"* ]] && [[ "$PWD" != "$venv_dir"* ]]; then
        # We've left the project directory, deactivate
        deactivate 2>/dev/null
      fi
    fi
  fi
}
```

## Key Improvements

1. **Supports both `.venv` and `venv`** - Checks for both directory names
2. **Smarter deactivation** - Only deactivates when you've actually left the project directory
3. **Better path handling** - Uses `realpath` for consistent path comparison
4. **Silent deactivation** - Suppresses error messages if venv is already deactivated

## How to Apply

1. Open `~/.bashrc`:
   ```bash
   nano ~/.bashrc
   ```

2. Find your current `cd()` function (should be at the bottom)

3. Replace it with the improved version above

4. Save and reload:
   ```bash
   source ~/.bashrc
   ```

## Testing

After applying the fix:

```bash
# Should activate venv
cd ~/projects/elfa-tools
echo $VIRTUAL_ENV  # Should show the venv path

# Should stay activated (you're still in the project)
cd tests
echo $VIRTUAL_ENV  # Should still show the venv path

# Should stay activated (you're still in the project)
cd ..
echo $VIRTUAL_ENV  # Should still show the venv path

# Should deactivate (you've left the project)
cd ~
echo $VIRTUAL_ENV  # Should be empty
```

## Alternative: Simpler Version (Less Aggressive)

If you want the venv to stay active even when leaving the project directory, use this simpler version:

```bash
# Auto-activate venv when entering a folder with .venv or venv
# Never auto-deactivate (you can manually deactivate with 'deactivate')
cd() {
  builtin cd "$@" || return
  
  # Check for .venv first (preferred), then venv
  if [ -f "./.venv/bin/activate" ]; then
    if [ -z "$VIRTUAL_ENV" ] || [ "$VIRTUAL_ENV" != "$(realpath ./.venv)" ]; then
      source ./.venv/bin/activate
    fi
  elif [ -f "./venv/bin/activate" ]; then
    if [ -z "$VIRTUAL_ENV" ] || [ "$VIRTUAL_ENV" != "$(realpath ./venv)" ]; then
      source ./venv/bin/activate
    fi
  fi
  # Note: We don't auto-deactivate here - you can manually run 'deactivate' if needed
}
```

This version will:
- ✅ Auto-activate when entering a directory with `.venv` or `venv`
- ✅ Switch venvs if you enter a different project
- ❌ Never auto-deactivate (you stay in venv until you manually deactivate)

Choose the version that works best for your workflow!

