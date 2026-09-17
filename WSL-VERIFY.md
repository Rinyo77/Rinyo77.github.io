# Verify Rinyo's site in WSL Ubuntu

The site is **not complete** until real Hugo builds, real browser captures, and
manual visual/keyboard review pass. All installation commands below are for your
own WSL distribution; they have not been run in the authoring workspace.

## 1. Prerequisites

- WSL 2 with Ubuntu 24.04 LTS, using an ordinary non-root Linux account.
- For the setup commands below: x86-64/amd64 architecture (`uname -m` reports
  `x86_64`). Stop if it reports `aarch64`; do not install amd64 packages on ARM.
- Python 3.11 or newer; the verifier uses only the standard library, including
  `tomllib`. No pip packages, virtual environment, Node.js, or npm are needed.
- Hugo **0.166.0**, standard Linux edition, matching this handoff's verifier.
- A Linux Chrome or Chromium executable with working browser sandbox support.
  A Windows `chrome.exe` is not a drop-in replacement for the script's Linux
  paths, profile directories, and local browser server.
- Network access to Ubuntu packages, the official Hugo release assets, and
  Google's Chrome download if these tools are not already installed.
- Permission to bind a loopback port. No GitHub login, token, domain purchase,
  background service, or public inbound port is required.

Headless captures do not require a desktop session or WSLg. For the separate
manual review you may use a Windows browser via localhost, or Linux Chrome with
WSLg if that is configured.

## 2. Extract the handoff

Export both `rinyo-site-handoff.zip` and `rinyo-site-handoff.zip.sha256` from the
authoring workspace. Put them together in your chosen WSL working directory.
Use a fresh destination so extraction does not overwrite your own edits.

```bash
sha256sum --check rinyo-site-handoff.zip.sha256
python3 -m zipfile -e rinyo-site-handoff.zip rinyo-handoff
cd rinyo-handoff/website
```

Prefer a directory in your Linux home filesystem. All remaining commands are run
from the extracted `website/` directory. The checksum detects transfer mismatch;
it is not an independent signature of the archive's publisher.

## 3. Install prerequisites, only if missing

These commands install packages in your WSL distribution. Read them before
running. The Chrome package also configures Google's update repository. Skip
the Chrome installation if you already have a working Linux Chrome/Chromium.

```bash
set -euo pipefail
test "$(uname -m)" = x86_64
sudo apt update
sudo apt install -y ca-certificates curl python3
python3 -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11+ required"'
mkdir -p .cache/hugo .cache/downloads
```

Download the pinned Hugo binary and verify its release checksum:

```bash
set -euo pipefail
HUGO_VERSION=0.166.0
archive="hugo_${HUGO_VERSION}_linux-amd64.tar.gz"
release="https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}"
(
  cd .cache/hugo
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --retry 3 --output "$archive" "$release/$archive"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --retry 3 --output checksums.txt "$release/hugo_${HUGO_VERSION}_checksums.txt"
  awk -v name="$archive" '$2 == name { print; found = 1 } END { if (!found) exit 1 }' checksums.txt | sha256sum --check --strict -
  tar -xzf "$archive" hugo
)
.cache/hugo/hugo version
```

The checksum comes from the same release as the archive: it detects download
mismatch but does not independently defend against a compromised publisher.
Do not assume Ubuntu's `apt install hugo` provides the pinned version.

Install Google's Linux Chrome package if needed:

```bash
set -euo pipefail
curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 --retry 3 \
  --output .cache/downloads/google-chrome-stable_current_amd64.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./.cache/downloads/google-chrome-stable_current_amd64.deb
google-chrome --version
```

Use a maintained Chrome/Chromium release; the verifier records the exact browser
version that you run rather than requiring an old fixed browser version.

## 4. Exact verification command

With the Hugo binary in `.cache/hugo/` and Chrome/Chromium on PATH:

```bash
bash tools/verify-wsl.sh
```

That is equivalent to invoking the full verifier with logging and pipeline
failure propagation. It does not install tools or deploy anything.

For explicit existing tool paths, relative to the `website/` directory:

```bash
HUGO_BIN=.cache/hugo/hugo CHROME_BIN=google-chrome bash tools/verify-wsl.sh
```

For Chromium, change `CHROME_BIN` to the working Linux executable name, such as
`chromium`. You can also point these variables to existing relative executable
paths. Do not run verification with `sudo` and do not add `--no-sandbox`.

The command:

1. Checks source identity/configuration and records the tool versions.
2. Builds actual Hugo output for both the account-root and project-subpath URL
   layouts, with warnings treated as fatal.
3. Checks generated pages, local links/fragments, author/display names, local CSS
   integrity, script-blocking CSP, RSS, and sitemap XML.
4. Serves the output on loopback, loads real pages in headless Chrome/Chromium,
   captures desktop and mobile images, and examines the browser's DOM.
5. Returns a nonzero exit on missing tools, failed builds, browser errors, bad
   screenshot dimensions, or failed checks. There is no simulated rendering.

With the included samples, captures cover the homepage, an article, Topics, an
individual topic, Archive, About, and the 404 page, at 1440×1050 and 390×844.
These are viewport screenshots, not full-page captures or physical-device tests.

Outputs, all excluded from Git:

- `.verification/wsl-verification.log` — commands' output and tool versions.
- `.verification/automatic-status.json` — actual automated stage results.
- `.verification/screenshots/` — browser-generated PNGs.

An exit code of zero and both `hugo_builds_passed` and
`browser_captures_passed` set to `true` mean the requested automated stages
passed. They do not mean the site is complete. `site_complete` remains `false`
and `manual_visual_review` remains `pending` until a human reviews the evidence.
Do not rely on old screenshots after a failed rerun; check the current log and
status first.

## 5. Required manual browser review

Inspect the generated images, then start a normal local preview without drafts:

```bash
.cache/hugo/hugo server --bind 127.0.0.1 --port 1313 --disableLiveReload
```

If Hugo is on PATH instead, use `hugo server` with the same options. Keep that
terminal running. Open `http://localhost:1313/` in your Windows browser, or in
Linux Chrome through WSLg. Stop the server afterward with Ctrl+C. Live reload
stays disabled because the site's CSP intentionally blocks scripts.

Check all of the following before signing off:

- The only public display name is **Rinyo**, including titles and accessible
  labels. The account name may exist in production destination URLs, not labels.
- Desktop and mobile layouts are readable, without clipped titles or unwanted
  page-wide horizontal scrolling. Test enlarged text and browser zoom too.
- Tab navigation shows visible focus; the skip link moves focus to main content.
- Homepage, article, Topics, individual topic, Archive, About, tags, adjacent
  entries, RSS, and 404 links behave as intended.
- Long articles, code blocks, and tables scroll/read correctly, including areas
  below the screenshot viewport.
- Browser developer tools show no unexpected external resource requests or
  CSP-blocked required resources. The page makes no tracking requests.

Demo mode does not prevent deployment or hide committed source. Keep unreviewed
changes off `main`. Record the date, tool versions, command exit status, and manual
findings in `VERIFICATION.md`. If anything fails, retain the log, fix the issue,
and rerun verification before changing the completion status.

## Troubleshooting without weakening security

- **Hugo version mismatch:** use the pinned binary from step 3.
- **Python cannot import tomllib:** use Python 3.11+; do not add a substitute
  dependency just to work around an older interpreter.
- **Browser sandbox error:** verify a supported, updated WSL 2 setup and working
  Linux browser installation under a normal user. Do not disable the sandbox or
  change system-wide security controls to force a pass.
- **Incorrect screenshot dimensions:** keep the failure; the browser did not
  reproduce the requested viewport. Share the browser version and log for review.
- **Proxy/download failure:** do not run with certificate verification disabled
  and do not substitute an untrusted mirror. Supply trusted existing tools or
  correct the network configuration.
- **Missing source files:** re-extract the handoff into a fresh directory instead
  of replacing your edited working copy or treating absent templates as valid.

Official references used for these instructions:

- Hugo Linux installation: `https://gohugo.io/installation/linux/`
- Pinned release: `https://github.com/gohugoio/hugo/releases/tag/v0.166.0`
- Chrome Headless: `https://developer.chrome.com/docs/automation-and-testing/headless`
- Microsoft WSL Linux apps: `https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps`
- Microsoft WSL localhost access: `https://learn.microsoft.com/en-us/windows/wsl/networking`
