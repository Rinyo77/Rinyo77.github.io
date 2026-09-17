# Rinyo

A small, English-language notebook with warm paper, aubergine headings, and
orange accents. Rinyo is the only public display name. The GitHub account name
is used only for repository ownership and deployment, not as visible UI text.

**Status: incomplete; no actual Hugo build or rendered browser verification has
passed in the authoring environment.** See `WSL-VERIFY.md` for exact WSL setup and
verification commands, and `VERIFICATION.md` for the evidence and remaining work.

The standalone `rinyo-site-handoff.zip` export contains this website directory,
including layouts, CSS, verification tools, and hidden deployment files. Export
it before leaving the workspace: earlier files were found missing or reverted
between turns, and workspace persistence is not confirmed. The compiler project
and Git history are intentionally excluded.

The website lives here independently of the compiler project in the parent
directory. No parent project files belong in the website's publishing repository.

## Included

- Journal homepage, individual articles, six topics, tag pages, yearly archive,
  About page, 404 page, and an RSS feed containing the latest 30 entries.
- Responsive layouts, keyboard focus styles, a skip link, and print styles.
- Markdown writing with TOML front matter; new entries default to drafts.
- Local CSS and an original SVG favicon. No theme download, npm, remote fonts,
  browser JavaScript, analytics, comments, database, or CMS.
- A GitHub Pages workflow with separate build/deploy permissions, pinned action
  commits, and a versioned Hugo download checked against its release checksums.

## Local preview

Use Hugo **0.166.0**, matching the deployment workflow and verification tool.
The standard edition is enough; Node.js, Go, and Sass are not required.

From the parent workspace:

```sh
cd website
hugo server --bind 127.0.0.1 --disableLiveReload --buildDrafts
```

Open the local address printed by Hugo. Keep the preview bound to loopback.
Live reload is deliberately disabled because the site's content security policy
does not allow scripts or network connections initiated by scripts.

To check a production build from this directory:

```sh
hugo --gc --minify --panicOnWarning
```

Output goes into `public/`, which is ignored by Git. Do not edit generated HTML.

## Make it yours

1. Keep `title` and `params.author` as `Rinyo` in `hugo.toml`; customize the intro
   and description if desired.
2. Expand the introduction in `content/about.md` using only Rinyo as the public
   name. Do not derive visible labels from the deployment account name.
3. Delete the six sample articles, set them to `draft = true`, or rewrite them
   and remove `sample = true`. Do not present the samples as your own history.
4. Write at least one real entry and preview the site.
5. Set `params.demo = false` in `hugo.toml` once the starter is ready.

Demo mode displays a starter notice and adds `noindex, nofollow` to HTML pages.
The deployment workflow skips publication while demo mode is enabled or any
non-draft sample entry remains. This is an accidental-publication guard, not
access control or a privacy guarantee. It cannot remove an already published site.

## Write an entry

From this directory:

```sh
hugo new content journal/my-first-note.md
```

Edit the generated Markdown file:

```toml
+++
title = 'A small thing I learned'
date = 2026-09-16T12:00:00Z
description = 'One sentence about this entry.'
topics = ['Learning Notes']
tags = ['linux', 'learning']
draft = true
+++
```

Write your English text below the closing `+++`. Use the real date of the entry,
not the sample date above. Pick one main topic and any number of optional tags.

| Topic | Intended use |
| --- | --- |
| Journal | Everyday observations and updates |
| Security Notes | Authorized experiments and careful write-ups |
| Learning Notes | Explanations, exercises, and open questions |
| Rants | Opinions and frustrations |
| Thoughts | Loose ideas and reflections |
| Reading Notes | Responses to books and other reading |

Use ordinary Markdown headings, lists, links, and fenced code blocks. Raw HTML
is disabled. For images, use a page bundle such as
`content/journal/my-first-note/index.md` with the image alongside it, and write
`![A useful description](diagram.png)`. Avoid external image embeds.

Review the content and attachments, then set `draft = false`. Production builds
exclude drafts, future-dated entries, and expired entries. When committing,
stage only the reviewed files; do not blindly stage the parent workspace.

## Publish without publishing the compiler project

1. Create a **new, empty public repository** owned by `Rinyo77` for this website.
   The preset assumes an account site named `Rinyo77.github.io`; a different
   repository name requires a project-site base URL.
2. Copy **the contents of this directory**, including `.github/` and `.gitignore`,
   into the new repository root. Do not copy the parent directory or its Git
   history. Do not upload private notes even as drafts.
3. Confirm `baseURL` in `hugo.toml`: `https://rinyo77.github.io/` for the account
   site, or `https://rinyo77.github.io/REPOSITORY/` for a project site, including
   the trailing slash. The address is not a public display-name label.
4. In the repository's **Settings → Pages**, select **GitHub Actions** as Source.
5. Push the reviewed website files to `main`. The workflow builds the site; it
   publishes only when the readiness guard passes. If needed, run it manually
   from the Actions tab after configuring Pages.
6. Check the deployed homepage, a topic, an article, Archive, and `index.xml`.
   Verify mobile and keyboard navigation. Enable **Enforce HTTPS** in Pages
   settings if the option is available and not already enforced.

The workflow intentionally lives inside this standalone website directory, not
the parent repository's workflow directory. It becomes active only after copying
the website contents to the new repository root as described above.

The workflow derives the deployment base URL from Pages, including project-site
subpaths. Your local `baseURL` still matters for local production builds. This
starter does not create a repository, push commits, buy a domain, or publish
anything from the current workspace.

## Safety boundaries

- Static publishing reduces the components you maintain; it does not make an
  account, build pipeline, hosting provider, or public text invulnerable.
- Keep secrets, sensitive screenshots, private diaries, and unredacted logs out
  of the repository entirely. Draft flags, `.gitignore`, and `noindex` do not
  hide anything already committed or publicly served.
- Use account two-factor authentication and review workflow changes. No personal
  access token is required by the provided Pages workflow.
- The HTML CSP allows only same-origin styles, images, and fonts and blocks
  scripts, forms, embeds, and script-initiated connections. Hugo template
  escaping and disabled raw Markdown HTML are additional boundaries, not a
  general sanitizer for untrusted contributors. Review all source changes.
- A meta CSP cannot enforce `frame-ancestors`; this starter does not claim full
  HTTP security-header control on GitHub Pages. The host can still keep logs.
- Release checksums fetched from the same release detect download mismatch;
  they do not independently protect against a compromised release publisher.
- Action pins correspond to checkout 4.2.2, configure-pages 5.0.0,
  upload-pages-artifact 3.0.1, and deploy-pages 4.0.5. These are fixed versions,
  not an assertion that they are the newest. Review updates periodically and
  re-pin reviewed commits rather than tracking a moving branch.

## Validation status in this workspace

Hugo and Chrome/Chromium are not installed in the supplied workspace. No
dependencies or Python virtual environments were installed. Source checks do not
establish that templates compile or render correctly. Run `bash tools/verify-wsl.sh`
from this directory after following `WSL-VERIFY.md`, then complete its manual
visual and keyboard checklist. Missing tools or failed checks return a nonzero
exit status; no output is fabricated and no local command deploys the site.