# Build Scripts

## hard-reset.js

**Purpose**: Clean all build artifacts and caches to fix path corruption issues.

### When to Use

Run `npm run hard-reset` when you encounter:

- "Module not found" errors despite files existing
- Path corruption from switching between WSL and Windows
- Mixed paths like `/mnt/e/...` and `E:\...` in error messages
- Cache-related build failures
- After major dependency updates

### What It Does

The hard reset script performs 5 steps:

1. **Delete `.docusaurus/` cache** - Removes build cache (corrupted paths)
2. **Delete `node_modules/`** - Removes all installed packages
3. **Delete `build/` directory** - Removes production build artifacts
4. **Delete `package-lock.json`** - Removes dependency lock file
5. **Run `npm install`** - Reinstalls clean dependencies

### Usage

```bash
# Run from project root
npm run hard-reset
```

### Output Example

```
╔════════════════════════════════════════════╗
║   Docusaurus Hard Reset Script            ║
║   Cleaning cache and reinstalling deps    ║
╚════════════════════════════════════════════╝

Project root: /mnt/e/M.Y/GIAIC-Hackathons/Humanoid-Robots-Book

[STEP 1] Deleting .docusaurus cache...
✓ Deleted: .docusaurus

[STEP 2] Deleting node_modules...
✓ Deleted: node_modules

[STEP 3] Deleting build directory...
✓ Deleted: build

[STEP 4] Deleting package-lock.json...
✓ Deleted: package-lock.json

[STEP 5] Running npm install...
[npm install progress...]
✓ npm install completed successfully

╔════════════════════════════════════════════╗
║   Hard Reset Complete!                     ║
║   Your project is ready to build.          ║
╚════════════════════════════════════════════╝

Next steps:
  • Run: npm start (for development)
  • Run: npm run build (for production)
```

### Technical Details

- **Language**: Node.js (requires Node >=20.0)
- **File Size**: ~4.3KB
- **Dependencies**: None (uses built-in Node.js modules)
- **Exit Codes**: 
  - `0` = Success
  - `1` = Failure (check error messages)

### Safety

- ✅ Only deletes build artifacts (not source code)
- ✅ Handles missing files/directories gracefully
- ✅ Shows detailed progress with color-coded output
- ✅ Cross-platform compatible (Windows, WSL, macOS, Linux)

### Troubleshooting

**Issue**: "Cannot find module" error when running script
- **Solution**: Ensure you're in the project root directory

**Issue**: Permission denied errors
- **Solution**: Run with appropriate permissions or use `sudo` (not recommended)

**Issue**: npm install fails
- **Solution**: Check internet connection and npm registry access

**Issue**: Script hangs during npm install
- **Solution**: Press Ctrl+C to cancel, check npm logs, try again

### Alternative Manual Cleanup

If the script fails, you can manually perform the same steps:

```bash
# On Linux/WSL/macOS
rm -rf .docusaurus node_modules build package-lock.json
npm install

# On Windows (PowerShell)
Remove-Item -Recurse -Force .docusaurus, node_modules, build, package-lock.json -ErrorAction SilentlyContinue
npm install
```

### Root Cause: Path Corruption

**Why this happens**:
Docusaurus caches absolute file paths in the `.docusaurus/` folder. When you switch between:

- **WSL**: Paths like `/mnt/e/M.Y/GIAIC-Hackathons/Humanoid-Robots-Book/...`
- **Windows**: Paths like `E:\M.Y\GIAIC-Hackathons\Humanoid-Robots-Book\...`

The cached paths become invalid, causing "Module not found" errors.

**Prevention**:
- Always build in the same environment (either always WSL or always Windows)
- Run `npm run hard-reset` when switching environments
