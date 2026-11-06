# Set up Carrel on your own

Use this guide if no one is helping you set up Carrel. It takes about 30 minutes, including a 10-minute conversation with Claude about your research.

You need [Claude Desktop](https://claude.ai/download) on macOS, Windows or Linux. If you do not see the **Code** tab in Claude Desktop, turn on Claude Code in **Settings** > **Features**.

## Step 1: install Carrel

You can install Carrel with or without a terminal.

### Without a terminal

1. Open Claude Desktop and select the **Code** tab.
2. Select **+** next to the plugin tabs, then **Add marketplace**.
3. Enter `linxule/carrel` and select **Sync**.
4. Find Carrel in the plugin list and turn it on.

You will install the Carrel command-line tools in step 3.

### With a terminal

Use this route on a new computer. The script installs Git, Node.js, uv, the GitHub command-line tool, Claude Code, the Carrel plugin and the Carrel command-line tools. It takes about 10 minutes and is safe to run again.

On macOS or Linux, open Terminal and run:

```bash
curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
```

On Windows, open PowerShell as an administrator and run:

```powershell
irm https://raw.githubusercontent.com/linxule/carrel/main/install.ps1 | iex
```

You do not need a GitHub account. Carrel is public.

If someone gave you the script file, run `bash install.sh` on macOS or Linux, or `.\install.ps1` in PowerShell on Windows.

## Step 2: create your research folder

Create a folder for your research vault, such as `Documents/Research`. Put it wherever feels natural to you.

## Step 3: open the folder in Claude Desktop

1. Open Claude Desktop and select the **Code** tab.
2. Select your research folder as the project.
3. If Claude shows "Carrel CLI not found", type `Install the Carrel CLI for me`. Claude asks your permission before each step.

## Step 4: run the setup

Type `/carrel-setup`, or say "I'd like to set up my research environment".

Claude then:

1. Talks with you about your research and what you need, for about 10 minutes.
2. Checks which tools are on your computer.
3. Proposes a setup plan for you to approve.
4. Creates your vault and installs your tools.
5. Writes a personal reference card.

## Step 5: install Obsidian

Obsidian is the app you use to browse your research vault. Claude will remind you to install it.

- on Mac, Claude may offer to install it, or you can download it from [the Obsidian website](https://obsidian.md)
- on Windows, run `winget install Obsidian.Obsidian`, or download it from [the Obsidian website](https://obsidian.md)
- on Linux, download the AppImage from [the Obsidian download page](https://obsidian.md/download)

Then open Obsidian, select **Open folder as vault**, choose your research folder and select **Open**.

## Step 6: install the Web Clipper (optional)

The Obsidian Web Clipper saves web articles from your browser straight into your vault. Search for "Obsidian Web Clipper" in the Chrome Web Store, Firefox Add-ons or Safari Extensions.

## Start using Carrel

Your reference card is at `_meta/cheat_sheet.md` in your vault. Open it in Obsidian to see everything you can do.

To start a new session, open Claude Desktop, select your research folder and start chatting.

## Fix problems

- Carrel does not seem active: in Claude Desktop, check that Carrel is turned on in the plugin list.
- "Failed to add marketplace": check your internet connection, then try again.
- "Carrel CLI not found": type `Install the Carrel CLI for me`, or run `uv tool install git+https://github.com/linxule/carrel.git` in a terminal.
- The plugin installed but no commands appear: quit Claude Desktop completely, then open it again.
- Claude cannot find files in your vault: check that you opened your research folder as the project.
- Obsidian shows an empty vault: check that Obsidian points at the same folder. Look for folders such as `papers/`, `notes/` and `inbox/`.

For anything else, tell Claude what is not working and ask for help.
