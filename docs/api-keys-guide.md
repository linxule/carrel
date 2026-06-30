# Setting Up API Keys for Optional Tools

Some Carrel tools need API keys to work. These are **optional** — your basic setup works without them.

## What Are API Keys?

An API key is like a password that lets Claude use a specific service. You get the key from the service's website and tell Claude where to find it.

## MineRU (Complex PDF Conversion)

MineRU converts complex PDFs (with tables, figures, formulas) more accurately than the default converter.

**When you need it:** Only if you regularly work with PDFs that have complex tables or scanned content.

**How to get a key:**
1. Go to [mineru.net](https://mineru.net)
2. Create an account
3. Find your API key in your account settings
4. Free tier quotas change over time; check your MinerU account dashboard before relying on a daily page limit.

**How to set it up:**
Tell Claude: *"I have a MineRU API key. Help me set it up."*

Claude will add it to your project configuration. The key stays on your computer.

**Privacy note:** MineRU is a cloud service. Your documents are sent to their servers for processing. If you work with sensitive data (interview transcripts, IRB-protected materials), use the default local converter instead.

## Mistral OCR (Scanned PDF Conversion)

Mistral OCR converts scanned or layout-heavy PDFs to Markdown through Mistral's cloud OCR service.

**When you need it:** When a PDF is image-only, scanned, or has layout that the local converter cannot preserve.

**How to get a key:**
1. Go to [console.mistral.ai](https://console.mistral.ai)
2. Create or open a workspace
3. Create an API key
4. Store it as `MISTRAL_API_KEY`

**How to use it:**
Tell Claude: *"Use Mistral OCR for this PDF."*

Claude should run the conversion with `--tool mistral_ocr` only when sensitivity policy allows cloud processing.

**Privacy note:** Mistral OCR is a cloud service. Your PDF is uploaded to Mistral for processing. Do not use it for high-sensitivity vaults or protected materials unless your research governance explicitly allows it.

## Zotero (Reference Library)

Connects Claude to your Zotero reference library so it can search your papers, read annotations, and help with citations.

**When you need it:** If you use Zotero to manage your academic references.

**How to get a key:**
1. Go to [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
2. Click "Create new private key"
3. Give it a name (e.g., "Carrel")
4. Enable "Allow library access"
5. Copy the key

**You also need your Library ID:**
- Go to [zotero.org/settings/keys](https://www.zotero.org/settings/keys)
- Your library ID is the number shown at the top

**How to set it up:**
Tell Claude: *"I have my Zotero API key and library ID. Help me connect Zotero."*

**Privacy note:** This accesses your Zotero library via their web API. Your library data is already on Zotero's servers if you use Zotero sync.

## Vox (Multi-Model Access)

Gives Claude access to other AI models — Gemini, GPT, Grok, DeepSeek, and more. Useful for getting a second opinion, using models with special strengths (e.g., Gemini's 1M token context), or cross-checking arguments.

**When you need it:** If you want to ask things like "Check this with Gemini" or "What does GPT think about this argument?"

**Three options, from simplest to most flexible:**

### Option 1: OpenRouter (One Key, Many Models)

The simplest way to access many models with a single account.

1. Go to [openrouter.ai](https://openrouter.ai)
2. Create an account
3. Go to Keys → Create Key
4. Copy the key
5. Tell Claude: *"I have an OpenRouter API key. Help me set up Vox."*

**Pricing:** Pay-per-use. Most models cost fractions of a cent per message. Add credit as you go.

### Option 2: Google Gemini (Free Tier)

Google's Gemini models have a generous free tier — good for trying things out.

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API key" → "Create API key"
4. Copy the key
5. Tell Claude: *"I have a Gemini API key. Help me set up Vox."*

**Pricing:** Free tier is generous (enough for regular research use). Paid tier for heavy use.

### Option 3: Multiple Providers

If you already have API keys from other AI services (OpenAI, xAI, DeepSeek, etc.), you can add them all. Each unlocks that provider's models.

Tell Claude: *"I have API keys for [list providers]. Help me set up Vox with all of them."*

| Provider | Where to get a key | Env variable |
|----------|-------------------|--------------|
| OpenRouter | [openrouter.ai](https://openrouter.ai) | `OPENROUTER_API_KEY` |
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) | `GEMINI_API_KEY` |
| OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `OPENAI_API_KEY` |
| xAI (Grok) | [console.x.ai](https://console.x.ai) | `XAI_API_KEY` |
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | `DEEPSEEK_API_KEY` |

### How Claude Stores Your Keys

When you give Claude an API key, it saves it to your computer's configuration so it persists across sessions. The key should stay local at rest, but prompts, URLs, documents, or excerpts are sent to the selected provider when you use that provider.

If you're on a **shared computer**, tell Claude: *"Store this key in my shell profile instead of the project config."* This keeps the key tied to your user account rather than the project folder.

## Need Help?

If you get stuck with any of these, just ask Claude:
*"Help me set up [MineRU / Zotero / Vox]. I'm not sure what to do."*

Claude can walk you through each step.
