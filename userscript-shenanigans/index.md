# Large userscript shenanigans

<kbd>rust</kbd> <kbd>js/ts</kbd> <kbd>decision-making hell</kbd>

Over the course of a year, I have (on the side) been working on an TurboWarp extension to integrate a Git workflow - no, not a [extension for TurboWarp](https://docs.turbowarp.org/development/extensions/introduction) but an [extension of TurboWarp](https://en.wikipedia.org/wiki/Userscript), that also connects with a local server. Here's what I have learned, in phases.

(It has been pretty cool)

# The frontend

The userscript for the longest time used plain JavaScript and HTML string templates because it just worked. I also found this "hack" for VSCode that allowed me to have Emmet and autocomplete for zero runtime cost:

```js
// basically just imitating Lit
const html = (string) => string;

const string = html`<p>hello world</p>`;

document.querySelector(BUTTON_ROW).innerHTML += html`&nbsp;
<div class="menu-bar_account-info-group_uqH-z">
    <div class="menu-bar_menu-bar-item_hHpQG">
    <div id="push-status">
        <span>Push project</span>
    </div>
    </div>
</div>`;
```

# The server

I've applied this sort of localized server thing in the past to avoid having to buy or host a server for workloads, but here, the benefits of creating a server on the user's computer to manage Git outweigh making a single server by a *ton*:

- I can't be held liable for data concerns (it would be especially questionable to steal data from a program mainly for kids LOL)
- I don't have to make an authentication system to know which user is accessing which repos or commits
- I don't have to host anything

Initially, I wrote the server to manage Git projects and other things using Python and Flask (HTTP). Sounds fine, right? It actually was for all the time it existed; it had all the basic features needed to fetch changed sprites, make commits (albeit, the process I used to make them was still pretty broken), and store project data in folders and modify it automatically.

Only problem is that Scratchers were probably too lazy to install Python, so I was starting to consider using a compiled language. Python was also starting to get boring after like, using it for everything I have written, so I settled on the most sane language I knew and was faster than Python:

<br><br><br><br><br><br><br><br>

You probably know what it could be.

Anyways, Rust was initially painful to adopt because of all the weird Python things I couldn't port over correctly:

```py
@no_type_check
def _modify_merge(costume_map):
    for i, _ in enumerate(merged.copy()):
        merged[i] = list(merged[i])
        merged[i][1] = list(merged[i][1])
        merged[i][1][0] = costume_map[merged[i][1][1]]
        merged[i][1] = tuple(merged[i][1])
        merged[i] = tuple(merged[i])

...

for sprite, (path, name) in added.copy():
    costume_map_add[name] = path
    added_no_path.append((sprite, (None, name)))
```

*(I was going to harm myself over this, not knowing that this could've easily been fixed by replacing `None` with `name`)*

Not to mention, global variables and the indomitable borrow checker. Once I got that stuff out of the way, adding new features was nothing short of a breeze and just satisfying.

# TL;DR

- Use a bundler from the start - there's practically no cons to using browser-friendly Node modules

- Integrate a JS mini-framework so you don't lose your mind if you want to move to TypeScript

- If you must use a server to communicate, use a WebSocket server for better performance and a lighter build/runs

- If there's a proper way to modify/extend an application, use that method. Userscripts are pretty difficult to maintain once they devolve into a whole module
