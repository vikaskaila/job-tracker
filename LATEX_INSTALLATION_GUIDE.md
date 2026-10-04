# LaTeX Installation Guide

## Overview
Your Job Tracker uses LaTeX to generate professional tailored resumes in PDF format. LaTeX is **NOT** included in Python - it must be installed separately on your system.

## Prerequisites
- Python 3.9+ (already configured)
- Virtual environment with required packages (already set up)
- LaTeX distribution (needs installation)

---

## Installation Instructions

### **Windows** (Recommended: MiKTeX)

1. **Download MiKTeX**
   - Visit: https://miktex.org/download
   - Download the Windows installer (latest version)

2. **Run the Installer**
   - Launch the `.exe` file
   - Choose "Install MiKTeX for all users" (recommended)
   - Accept default installation path
   - Enable "Install missing packages on the fly" (important!)

3. **Verify Installation**
   ```powershell
   pdflatex --version
   xlatex --version
   ```
   You should see version information for both commands.

4. **Restart Your Computer** (Important!)
   - The PATH environment variables need to be reloaded

---

### **macOS** (Recommended: MacTeX)

1. **Install via Homebrew** (recommended)
   ```bash
   brew install mactex
   ```
   
   OR download from:
   - https://www.tug.org/mactex/mactex-download.html

2. **Verify Installation**
   ```bash
   pdflatex --version
   xlatex --version
   ```

3. **Update PATH** (if needed)
   ```bash
   export PATH="/usr/local/texlive/*/bin:$PATH"
   ```

---

### **Linux** (Recommended: texlive)

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra
```

**Fedora/RHEL:**
```bash
sudo dnf install texlive texlive-latex texlive-fonts
```

**Arch:**
```bash
sudo pacman -S texlive-most texlive-lang
```

**Verify Installation:**
```bash
pdflatex --version
xlatex --version
```

---

## Troubleshooting

### Issue: "pdflatex not found" or "xlatex not found"

**Solution 1: Check Installation**
```powershell
# Windows PowerShell
Get-Command pdflatex    # Should show path if installed
Get-Command xlatex      # Should show path if installed
```

**Solution 2: Restart Computer**
- Environment variables don't load until reboot

**Solution 3: Manual PATH Setup**

**Windows:**
- Control Panel → System → Advanced System Settings → Environment Variables
- Add MiKTeX bin directory to PATH:
  - Typical path: `C:\Program Files\MiKTeX\miktex\bin\x64`

**macOS/Linux:**
```bash
# Add to ~/.bash_profile or ~/.zshrc
export PATH="/usr/local/texlive/2024/bin/x86_64-linux:$PATH"  # Linux example
export PATH="/usr/local/texlive/2024/bin:$PATH"  # macOS example
```

### Issue: "LaTeX compilation failed" or "PDF not generated"

**Possible Causes:**
1. LaTeX tools not properly installed
2. LaTeX content has syntax errors
3. Missing LaTeX packages

**Solutions:**
1. Restart the application
2. Check the application logs: `{DATA_DIR}/app.log`
3. Verify LaTeX syntax in the log file (will show compilation errors)

### Issue: Unicode or encoding errors in LaTeX

The app tries `xlatex` first (handles Unicode better), then falls back to `pdflatex`.

**Solution:** Ensure you have UTF-8 support:
```bash
# Windows PowerShell
chcp 65001  # Set to UTF-8

# Then reinstall MiKTeX or texlive
```

---

## Quick Test

After installation, test your setup:

```powershell
# Create a simple LaTeX file
echo '\documentclass{article}
\begin{document}
Hello LaTeX World!
\end{document}' | Out-File test.tex -Encoding UTF8

# Try to compile
pdflatex -interaction=nonstopmode test.tex

# If test.pdf exists, LaTeX is working!
```

---

## How the Application Uses LaTeX

1. **Job Scraping**: Collects job descriptions from Indeed and LinkedIn
2. **Language Detection**: Detects if description is German/other language
3. **Translation**: Converts to English if needed (using Groq AI)
4. **Resume Tailoring**: Uses Groq AI to customize your resume for the job
5. **LaTeX Generation**: Groq AI creates a formatted LaTeX resume
6. **PDF Compilation**: `pdflatex` or `xlatex` compiles the LaTeX → PDF
7. **Storage**: PDF saved to `{GENERATED_DIR}/resume_[job_id].pdf`

---

## Performance Tips

1. **Install Optional Packages in Advance** (MiKTeX)
   - MiKTeX can download packages on-demand (slower first time)
   - Pre-install: `miktex` → Update → Check for updates

2. **Use SSD Storage**
   - LaTeX compilation is I/O intensive
   - Faster SSDs = faster compilation

3. **Close Other LaTeX Editors**
   - PDF viewers can lock files during compilation
   - Close PDF viewer before regenerating

4. **Monitor Storage**
   - LaTeX temporary files can accumulate
   - Regular cleanup recommended

---

## Support

If you continue to have issues:

1. **Check Logs**
   - Look at `{DATA_DIR}/app.log` for detailed errors
   - Search for "LaTeX" or "compilation" keywords

2. **Verify Each Step**
   - Test `pdflatex --version`
   - Test `xlatex --version`
   - Test compilation with sample LaTeX file

3. **Common Paths**
   - Windows MiKTeX: `C:\Program Files\MiKTeX\miktex\bin\x64`
   - macOS texlive: `/usr/local/texlive/2024/bin`
   - Linux: `/usr/bin/` (varies by distro)

---

## Environment Variables Used

The application automatically:
- Looks for `pdflatex` and `xlatex` in your system PATH
- Uses `-interaction=nonstopmode` for non-interactive compilation
- Sets working directory to temp folder for compilation
- Copies PDF to `{GENERATED_DIR}/` after generation

No additional configuration needed once LaTeX tools are installed!
