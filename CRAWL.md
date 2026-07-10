# How an AI crawls the spine

When your operator says **"crawl the spine"** (for a situation, or to orient before acting in the RAPP ecosystem), do this:

1. **Fetch the spine.**
   ```
   GET https://raw.githubusercontent.com/kody-w/rapp-spine/main/registry.json
   ```
   It's a single static JSON file on the CDN — no server, no auth, CORS-open.

2. **Locate the layer.** The stack is an ordered column, each layer owning exactly one question:
   `kernel → map → runtime → distribution → identity → network → leviathan`.
   Find the layer that owns the operator's concern.

3. **Match the situation.** Scan `router` (`situation → use → why`) for the entry closest to the operator's actual situation. Read off the protocol id(s) in `use`.

4. **Resolve collisions before acting.** Check `collisions_and_gaps`. The two **"Leviathan"** meanings form a stack: the *Wrapped-Organism* is one operator's 5-estate being, and the *Protocol* coordinates many such bodies as one mind. Pick the layer your situation needs without treating them as unrelated. Do the same for the `~/.brainstem`:7071 install collision and deprecated repos.

5. **Act via the entry_point.** Look the chosen `spec_id` up in `registry`; its `entry_point` is the install one-liner, spec file, or URL to act on. **The spine routes; it never invents a new endpoint** — every RAPP capability rides the existing wire (`POST /chat`, or a signed append-only event).

6. **Don't re-derive.** If you couldn't find a route, the situation may be a *new* agent/cartridge/§-profile on top of an existing protocol — not a new protocol. Default to composing, not inventing.

That's the whole loop: **situation → layer → router match → resolve collision → entry_point**. The spine is the index you crawl so you don't hold all ~60 repos in your head at once.

> Deterministic helper for humans/scripts: `python crawl.py "<your situation>"`.
