# IC design tools — student usage notes

Use this repository to set up an IC design environment on **Ubuntu 24.04**. It installs prebuilt tools and the **IHP SG13G2 process design kit (PDK)**; you do not need to build the tools yourself.

| Tool | Purpose |
| --- | --- |
| Xschem | Draw schematics and generate netlists |
| ngspice | Simulate circuits |
| OpenVAF | Compile Verilog-A models |
| VACASK | Simulate circuits with Verilog-A models |

## 1. Get the repository

Use an Ubuntu 24.04 machine or VM with internet access, permission to use `sudo`, and enough free disk space for the tools and PDK. Xschem needs a graphical desktop.

```sh
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/Mario-Auer-TUG/icdesign-tools-ubuntu24.04.git
cd icdesign-tools-ubuntu24.04
```


## 2. Install the environment

From the repository directory, run:

```sh
./setup/setup.sh
```

Run this as your normal user account; the script requests `sudo` when needed. It installs:

- Basic Ubuntu utilities and development packages.
- Node.js 24 and the `uv` Python tool manager.
- IC design packages from the configured download site.
- The pinned IHP SG13G2 PDK, using `ciel`, and compiled Verilog-A models.

Installation can take some time and requires downloads. Wait for **“Setup completed successfully.”** If `uv` is not found afterward, close and reopen your terminal.

### If you only need the tools

```sh
./setup/install-icd-tools.sh
```

This installs every package listed in the published manifest but does not install the PDK or the other setup prerequisites. The download site hosts `.deb` files, not an apt repository.

## 3. Make the tools available in your terminal

The tools are installed under `/opt/icdesign/tools`. Add these lines to your `~/.bashrc` once:

```sh
export PATH="/opt/icdesign/tools/bin:$PATH"
export PDK_ROOT="/opt/icdesign/pdks"
```

Then reload your shell settings:

```sh
source ~/.bashrc
command -v xschem ngspice openvaf vacask
```

The command should print a path for each installed tool. Check the simulator and compiler:

```sh
ngspice --version
openvaf --help
```

## 4. Start working

Keep your coursework in a separate directory, rather than editing the installation scripts:

```sh
mkdir -p ~/icdesign/work
cd ~/icdesign/work
xschem
```

To open an existing schematic, use `xschem circuit.sch`. To simulate an ngspice netlist interactively, use `ngspice circuit.cir`. Replace these paths with your own files.

The default PDK location is:

```text
/opt/icdesign/pdks/ihp-sg13g2
```

## Configuration and updates

All setup scripts read **`setup/.env`**, even when run from another directory. It contains the course defaults for `PDK_FAMILY`, `PDK_VERSION`, `PDK_ROOT`, `TOOLS_DIR`, and `ICDESIGN_PACKAGES_URL`. There should be no need to change those values.

This file is executed as Bash code: use only a trusted copy and do not put secrets in it. The repository-root `.env` is not loaded. Command-line options override exported environment variables, which override `setup/.env` defaults. These settings configure the scripts, not your interactive shell.

To reinstall the PDK or see its options (requires `uv` and `pipx`):

```sh
./setup/install-pdk.sh --help
./setup/install-pdk.sh
```

To install the currently published tool packages again:

```sh
./setup/install-icd-tools.sh
```

Use the download URL provided by your instructor. Switching Git branches does not change the download site unless that branch changes `setup/.env`.

## Troubleshooting

- **`command not found`:** Check the `PATH` settings above and reopen your terminal. Try `/opt/icdesign/tools/bin/xschem` to launch Xschem directly.
- **Xschem cannot open a display:** Run it from a graphical Ubuntu session. Remote sessions need a working graphical display connection.
- **PDK symbols or models are missing:** Check that the PDK installation completed and that your project's Xschem/model configuration points to the installed PDK. Check that the `xschemrc` file for this PDK is present.
- **Downloads fail:** Check your internet connection and `ICDESIGN_PACKAGES_URL`. The site must provide `manifest.json` and the listed packages.
- **Installation fails:** Read the first error in the terminal output. Correct the problem before rerunning the relevant script; do not continue with a partially installed environment.

**Warning:** If Ubuntu asks to install one of these packages (such as `xschem`), decline the installation (say no). Those binaries are not up to date.

## Optional: build packages locally

Most students can skip this section. Local builds require Docker, Python 3, network access, and substantial disk space and time, especially for VACASK.

```sh
python3 scripts/build.py --list                 # packages enabled in build-control.json
make build                                     # build enabled packages into dist/
python3 scripts/build.py --package ngspice --jobs 4
make all                                       # build all four packages
./setup/install-icd-tools.sh --local dist        # install locally built packages
make test                                      # run repository tests
```

Package source pins and dependencies are in `packages/<name>/dependencies.json`. You do not need to change them for normal course use.
