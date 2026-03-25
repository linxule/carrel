# Setting Up Carrel Without a Facilitator

If you're setting up Carrel on your own (no one guiding you in person), here's what to do.

## Before You Start

You need:
- **Claude Desktop** installed on your computer ([download here](https://claude.ai/download))
- **Claude Code** enabled in Claude Desktop (check Settings → Features)
- The **Carrel plugin** installed (see below)

## Step 1: Install the Carrel Plugin

**If Carrel is on the public marketplace:**
Open Claude Desktop → click the **+** button → **Plugins** → **Discover** tab → search for "Carrel" → **Install**. Choose "User" scope.

**If you received a GitHub invitation:**
Open Claude Desktop → start a Claude Code session → type:
```
/plugin marketplace add linxule/carrel
/plugin install carrel@linxule
```

**If someone gave you the plugin files:**
Ask them where the files are on your computer, then in a Claude Code session:
```
/plugin install --local /path/to/carrel
```

## Step 2: Create Your Research Folder

Using Finder (Mac) or File Explorer (Windows), create a new folder where you want your research vault to live. Good locations:

- `Documents/Research`
- `Desktop/My Research`
- Wherever feels natural to you

## Step 3: Open the Folder in Claude Desktop

1. Open Claude Desktop
2. Start a new **Claude Code** session
3. Select your research folder as the project
4. You should see a welcome message from Carrel

## Step 4: Run the Setup

Type: **"I'd like to set up my research environment"**

Claude will:
1. Have a conversation about your research and needs (~10 min)
2. Check what tools are on your computer (~30 sec, silent)
3. Propose a configuration plan
4. Set up your vault structure and tools
5. Generate a personalized reference card

## Step 5: Install Obsidian

Claude will tell you to install Obsidian — it's the app you'll use to browse your research vault.

- **Mac**: Claude may offer to install it for you, or download from [obsidian.md](https://obsidian.md)
- **Windows**: Download from [obsidian.md](https://obsidian.md)

After installing:
1. Open Obsidian
2. Choose "Open folder as vault"
3. Navigate to your research folder
4. Click Open

## Step 6: Install Web Clipper (Optional)

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

**Claude can't find files in my vault:**
Make sure you opened the research folder as your project in Claude Desktop.

**Obsidian shows an empty vault:**
Make sure you pointed Obsidian at the same folder Claude set up. Look for folders like `papers/`, `notes/`, `inbox/`.

**Something else isn't working:**
Tell Claude: "Something isn't working with [describe the problem]. Can you help?"
