---
title: Claude Code,|from your phone
highlight: phone
kicker: Free guide
subtitle: A plain-English starter guide. Set it up once, give Claude a real job, and check its work. No laptop required.
promises: No laptop required | Copy-and-paste prompts | Checked against the official docs
author: By CT
version: Version 1.0
date: September 2026
footer: Claude Code from your phone  ·  starter guide
contents_note: Short on time? Do **Part 3** and **Part 4**. That's one setup and one real result in about 25 minutes.
end_kicker: What's next
end_title: You're set up. Now go build something.
end_text: I'm exploring what tools like this can really do, and sharing what I learn on YouTube. | Tell me what you built, or what you want me to try next, in the comments on the video. Every idea helps me decide what to cover next. | If this guide helped, subscribing is the best way to say thanks. It's how the channel grows.
---

# What Claude Code is

Claude Code is Anthropic's coding tool. In the official docs' own words, it's "an agentic coding tool that reads your codebase, edits files, runs commands, and integrates with your development tools."

In plain English: you describe what you want, and Claude does the work a developer would do. It reads the project, makes the changes, runs the checks, and shows you what it did. You stay in charge. Nothing lands in your project until you approve it.

> [!TIP] The mindset
> You're the director. Claude is the crew. Your job is to say what "done" looks like and to check the result. Its job is the typing.

## What "agentic" means

A chatbot answers questions. An agent takes steps toward a goal: it opens files, edits them, runs commands, reads the results, and tries again when something fails. That loop is what lets it finish real tasks instead of handing you code to paste somewhere.

## What it's good for, even as a beginner

- **Understanding** a project you didn't write
- **Fixing** a bug, with a test that proves it's fixed
- **Adding** a small feature or a setting
- **Writing** a README, docs or comments
- **Turning an idea** into a first working version

## Where it runs

The docs put it simply: Claude Code "behaves the same everywhere." What changes is where the work happens.

| Where | Needs a computer? | Good for |
|---|---|---|
| Claude app, **Code** tab | No | Starting, steering and reviewing tasks |
| claude.ai/code in any browser | No | Reading changes on a bigger screen |
| Desktop app | Yes | Point and click, on your own machine |
| Terminal, VS Code, JetBrains | Yes | Full control of your own machine |

This guide is about the first two. They run on Anthropic's cloud, so a task keeps going after you put your phone down.

# What you need

1. **A paid Claude plan.** Claude Code "is included in all paid plans." The Free plan doesn't include it. As of September 2026, Pro is $20 a month billed monthly, or $17 a month billed yearly. Prices change, so check [claude.com/pricing](https://claude.com/pricing).
2. **The Claude app** for iPhone or Android. There's no separate Claude Code app: it lives in the **Code** tab of the regular Claude app.
3. **A free GitHub account.** GitHub is where code projects live online. Cloud sessions work on GitHub repositories, so this is how Claude gets to your project.

That's the whole list. No laptop, no installs, no terminal.

> [!NOTE] Usage limits
> Your chats and your Claude Code work share one usage pool. It resets on a rolling five-hour window, and paid plans add weekly limits on top. If you hit a limit, you can wait for the reset or move to a bigger plan.

> [!NOTE] Don't see the Code tab?
> The docs say your plan or organization may not include it. On Team and Enterprise plans, an Owner has to switch features on first.

# Set it up once

About ten minutes, and you only do it once.

1. **Make a GitHub account** at [github.com](https://github.com) if you don't have one. The free plan is plenty.
2. **Upgrade Claude** to a paid plan. Pro is enough to start.
3. **Install the Claude app**, sign in, and tap **Code**. You can also open [claude.ai/code](https://claude.ai/code) in your phone's browser.
4. **Connect GitHub.** The first time, Claude walks you through signing in with GitHub.
5. **Install the Claude GitHub App** on the repositories you want Claude to work in. Without it, a session can still clone any public repository, but it can only work in a private repository where the app is installed. You choose which repositories it can reach.
6. **Keep the Default environment** that setup creates. It uses "Trusted" network access: sessions can reach common package registries and a list of allowed sites, and nothing else.

> [!TIP] Skipped the GitHub App?
> No problem. Install it later from [github.com/apps/claude](https://github.com/apps/claude/installations/new) on any account whose private repositories you want to use.

# Your first win

Fifteen minutes, start to finish: Claude explains a project, improves one thing, and hands you a pull request.

## Pick a project

- **Start fresh:** open [github.com/new](https://github.com/new), name it something like `my-first-claude-project`, tick **Add a README**, and create it.
- **Or borrow one:** open an open source project you like on GitHub and tap **Fork** to make your own copy. That's what I did in the video, with a free PDF maker.

## Run your first session

1. In the **Code** tab, tap the repository picker and choose your repository. Leave the branch as it is.
2. Set the mode to **Plan**. Claude will propose an approach and wait for your OK before it edits anything.
3. Send the first prompt below, then read the answer. Ask about anything that doesn't make sense.
4. Send the second prompt and let it work. You can close the app: the session keeps running, and it's waiting for you on any device you sign in on, including claude.ai/code on a computer.
5. When it's done, tap the changes indicator (it looks like `+42 -18`) to open the diff. Read it. Tap a line to leave a comment if you want something changed.
6. Tap **Create PR** at the top of the diff view. A draft is fine.
7. Happy with it? Merge the pull request on GitHub. Not happy? Close it. Your main code doesn't change until you merge.

```prompt
Read this repository and explain it to me like I'm new to coding: what it does, how to run it, and anything that looks broken or confusing. Don't change any files yet.
```

```prompt
Pick the most useful small improvement from your list and make it. Keep the change small and match the existing style. Run whatever checks exist (tests, a build, or the app itself) and show me the output.
```

Started fresh with an empty repository? Use this one instead of the second prompt:

```prompt
Build a small, useful tool in this repository: [describe it in one sentence]. Keep it to as few files as possible, add a README that explains how to use it, and run it once to prove it works. Show me the output.
```

> [!NOTE] What's a pull request?
> A pull request (PR) is a proposal: "here are my changes, do you want them?" It shows every line that changed. Nothing touches your main code until you merge it.

# How to ask

The official best practices come down to five habits.

### 1. Be specific

Name the file or function. Paste the error message. Describe what should happen, not just what's wrong. "Fix the failing test in `tests/test_login.py`" beats "fix the tests."

### 2. Give it a way to check its work

In the docs' words: "Give Claude a check it can run: tests, a build, a screenshot to compare. It's the difference between a session you watch and one you walk away from."

### 3. Explore, then plan, then build

For anything bigger than a small fix, start in **Plan** mode. Claude reads the code and proposes a plan, and nothing changes until you approve it.

### 4. Ask for proof

Don't settle for "done." Ask for the test output, the command it ran, or a screenshot of the result.

### 5. One task per session

Each task gets its own session and its own branch, so you can run a few at once without them stepping on each other.

## Prompts to copy

```prompt
Explain [file or folder] like I'm new to coding. What does each part do, and how do the parts connect?
```

```prompt
Figure out how to run this project, then run it. Tell me exactly what you ran and what happened.
```

```prompt
Review this project for bugs a first-time user would hit. List them from most to least painful, with the file and line for each.
```

```prompt
Fix [the bug]. First write a test that fails because of it, then fix it and show me the test passing.
```

```prompt
I want to add [feature]. Don't write code yet: propose a plan, list the files you'd change, and point out anything risky.
```

```prompt
Rewrite the README for someone who has never used a terminal: what this is, how to install it, and how to use it, with an example.
```

```prompt
Walk me through every change you made and why. Point out anything I should double-check before I merge.
```

```prompt
Undo the change to [file] but keep everything else. Then [your new instruction].
```

# Stay in control

- **Read the diff before you merge.** You're the one shipping it. Ask Claude to explain anything you don't follow.
- **Choose the mode on purpose.** Cloud sessions offer **Plan** (proposes, then waits for your OK), **Accept edits** (makes changes without stopping) and **Auto** (a classifier reviews each action instead of asking you, where your account allows it).
- **Never paste passwords or API keys into a prompt.** If a project needs a key, keep it in your cloud environment's settings. On Pro and Max you can store API credentials that sessions use without Claude ever seeing the key.
- **Be careful with code from strangers.** Files and web pages can hide instructions written to trick an AI. It's called prompt injection. Work on projects you trust, and review what changes.
- **Know your undo button.** Cloud work happens on its own branch. Don't like the result? Close the pull request and delete the branch, and your main code is exactly as it was.

> [!WARNING] It can be wrong
> Claude is very capable, and it still makes mistakes. The security docs say it plainly: "no system is completely immune to all attacks." Treat every change like a new teammate's work: read it, test it, then merge it.

# When you want more

## Use it on a computer

The same Claude Code runs in a terminal. On macOS, Linux or WSL, install it with one line:

```bash
$ curl -fsSL https://claude.ai/install.sh | bash
```

On Windows, in PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

Then open a terminal in your project folder, run `claude`, and sign in. You need macOS 13 or later, Windows 10 1809 or later, or Ubuntu 20.04 or later, with at least 4 GB of RAM.

## Steer your computer from your phone

Remote Control connects the Claude app to a Claude Code session running on your own machine. Start one with `claude remote-control`, or type `/remote-control` in a session that's already open, then scan the QR code with your phone. The work and your files stay on your computer while you steer from anywhere. It's available on Pro, Max, Team and Enterprise plans.

## Give Claude a memory

CLAUDE.md is a file Claude reads at the start of every conversation: how to run your project, your style rules, the gotchas. In a terminal, `/init` writes a starter one. From your phone, just ask:

```prompt
Create a short CLAUDE.md for this repository: how to install, run and test it, plus any gotchas you ran into today. Keep it under 30 lines.
```

The docs' rule of thumb for what stays in it: for each line, ask "Would removing this cause Claude to make mistakes?" If not, cut it.

## Terminal commands worth knowing

| Command | What it does |
|---|---|
| `/init` | Writes a starter CLAUDE.md for your project |
| `/help` | Shows the commands you can use |
| `/clear` | Starts a fresh conversation |
| `/rewind` | Rolls the conversation or the code back to an earlier point. Pressing Esc twice does the same. |
| `/diff` | Shows the changes Claude has made |
| `/usage` | Shows your usage and plan limits |

Two keys to remember: **Esc** stops Claude mid-step so you can redirect it, and **Shift+Tab** switches between permission modes.

# Your 7-day plan

One small step a day. Tick them off.

- [ ] **Day 1.** Set up: paid plan, Claude app, GitHub connected.
- [ ] **Day 2.** Fork a project you like and ask Claude to explain it.
- [ ] **Day 3.** Improve one small thing and open your first pull request.
- [ ] **Day 4.** Add a test or rewrite the README, then merge it.
- [ ] **Day 5.** Build a tiny tool for your own life: a budget calculator, a photo renamer, a PDF maker.
- [ ] **Day 6.** Read a whole diff line by line, and ask about anything you don't get.
- [ ] **Day 7.** Share what you made, and tell me about it in the comments.

> [!TRY] Stuck on an idea?
> Ask Claude: "I'm new to coding. Suggest five small tools I could build in an afternoon that would save me time every week. Ask me three questions about my routine first."

# Words you'll hear

| Word | What it means |
|---|---|
| Repository (repo) | A project folder on GitHub, with its full history |
| Fork | Your own copy of someone else's repository |
| Branch | A parallel version of the code where changes happen safely |
| Commit | One saved set of changes, with a note saying what changed |
| Diff | The before and after of a change, line by line |
| Pull request (PR) | A proposal to merge a branch's changes into the main code |
| Merge | Accepting a pull request, so its changes join the main code |
| Session | One conversation with Claude Code about one task |
| Plan mode | Claude reads and proposes, and changes nothing until you approve |
| CLAUDE.md | A file of standing instructions Claude reads every conversation |
| Terminal | The text window where you type commands on a computer |

## Official links

- Overview: [code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview)
- On your phone: [code.claude.com/docs/en/mobile](https://code.claude.com/docs/en/mobile)
- Cloud sessions quickstart: [code.claude.com/docs/en/web-quickstart](https://code.claude.com/docs/en/web-quickstart)
- Best practices: [code.claude.com/docs/en/best-practices](https://code.claude.com/docs/en/best-practices)
- Plans and pricing: [claude.com/pricing](https://claude.com/pricing)

> [!NOTE] About this guide
> Made by CT with Claude Code, from a phone, and checked against Anthropic's documentation on September 28, 2026. Features change fast: when this guide and the docs disagree, the docs win. This is an independent guide, not affiliated with or endorsed by Anthropic. Built with a free, open source PDF maker.
