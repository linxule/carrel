# Setting Up Carrel Without a Facilitator

If you're setting up Carrel on your own (no one guiding you in person), here's what to do.

## Before You Start

You need:
- **Claude Desktop** installed on your computer ([download here](https://claude.ai/download))
- **Claude Code** enabled in Claude Desktop (check Settings → Features)
- **GitHub access** to the Carrel repo (you should have received an invitation email)

## Step 1: Run the Install Script

Open Terminal (find it in Applications → Utilities, or press Cmd+Space and type "Terminal") and paste:

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/linxule/carrel/main/install.sh | bash
```

**Windows (PowerShell as Administrator):**
```powershell
irm https://raw.githubusercontent.com/linxule/carrel/main/install.ps1 | iex
```

This takes about 10 minutes. It installs developer tools, GitHub CLI, and Claude Code. It will ask you to sign in to GitHub — use the account that received the repo invitation.

If someone gave you the script file directly:
```bash
bash install.sh            # macOS/Linux
.\install.ps1              # Windows PowerShell
```

## Step 2: Install the Carrel Plugin

Still in Terminal, run:

```bash
claude --dangerously-skip-permissions
```

Then type this message to Claude:

> Install the Carrel plugin from linxule/carrel and verify it works.

Claude will handle the marketplace registration and installation. If anything goes wrong, it will diagnose and fix the issue.

Alternatively, if you prefer to run the commands yourself:
```bash
claude plugin marketplace add linxule/carrel
claude plugin install carrel@carrel --scope user
```

## Step 3: Create Your Research Folder

Using Finder, create a new folder where you want your research vault to live. Good locations:

- `Documents/Research`
- `Desktop/My Research`
- Wherever feels natural to you

## Step 4: Open the Folder in Claude Desktop

1. Open Claude Desktop
2. Start a new **Claude Code** session (the **Code** tab)
3. Select your research folder as the project
4. You should see a welcome message from Carrel

## Step 5: Run the Setup

Type: **"I'd like to set up my research environment"**

Claude will:
1. Have a conversation about your research and needs (~10 min)
2. Check what tools are on your computer (~30 sec, silent)
3. Propose a configuration plan
4. Set up your vault structure and tools
5. Generate a personalized reference card

## Step 6: Install Obsidian

Claude will tell you to install Obsidian — it's the app you'll use to browse your research vault.

- **Mac**: Claude may offer to install it for you, or download from [obsidian.md](https://obsidian.md)
- **Windows**: Install with `winget install Obsidian.Obsidian`, or download from [obsidian.md](https://obsidian.md)
- **Linux**: Download the AppImage from [obsidian.md](https://obsidian.md/download)

After installing:
1. Open Obsidian
2. Choose "Open folder as vault"
3. Navigate to your research folder
4. Click Open

## Step 7: Install Web Clipper (Optional)

The Obsidian Web Clipper lets you save web articles directly to your vault from your browser:
- Chrome: Search "Obsidian Web Clipper" in Chrome Web Store
- Firefox: Search in Firefox Add-ons
- Safari: Available in Safari Extensions

## You're Done!

Your cheat sheet is at `_meta/cheat_sheet.md` in your vault — open it in Obsidian for a quick reference of everything you can do.

**To start future sessions:** Open Claude Desktop → select your research folder → start chatting.

## Troubleshooting

**Carrel doesn't seem to be active:**
Check that the plugin is installed and enabled: Claude Desktop → Plugins → look for "Carrel".

**"Failed to add marketplace":**
This usually means GitHub authentication isn't set up. Open Terminal and run:
```bash
gh auth login
```
Then retry the plugin install.

**Plugin installed but commands don't appear:**
Restart Claude Desktop completely (Cmd+Q, then reopen). Commands, agents, and skills are auto-discovered on startup.

**Claude can't find files in my vault:**
Make sure you opened the research folder as your project in Claude Desktop.

**Obsidian shows an empty vault:**
Make sure you pointed Obsidian at the same folder Claude set up. Look for folders like `papers/`, `notes/`, `inbox/`.

**Something else isn't working:**
Tell Claude: "Something isn't working with [describe the problem]. Can you help?"
