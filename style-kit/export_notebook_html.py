"""
Export a Jupyter notebook to a standalone HTML file with a nested,
collapsible sidebar table of contents (matching the notebook's own
JupyterLab Light theme colors) and scroll-spy active-section highlighting.

Usage:
    python export_notebook_html.py                          # exports analisis_prensa_chile.ipynb
    python export_notebook_html.py analisis_bts_chile.ipynb  # exports a different notebook
"""

import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup

DEFAULT_NOTEBOOK = "analisis_prensa_chile.ipynb"


def convert_to_html(notebook_path: Path) -> Path:
    subprocess.run(
        [sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", str(notebook_path)],
        check=True,
    )
    return notebook_path.with_suffix(".html")


def add_toc_sidebar(html_path: Path) -> None:
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    headings = soup.select("h1[id], h2[id], h3[id]")

    toc_root = soup.new_tag("ul", **{"class": "toc-list toc-level-1"})
    stack = [(0, toc_root)]  # (level, ul that holds <li> items at that level)

    for h in headings:
        level = int(h.name[1])
        text = h.get_text().replace("\xb6", "").strip()  # strip nbconvert's pilcrow anchor char
        li = soup.new_tag("li", **{"class": f"toc-item toc-h{level}"})
        a = soup.new_tag("a", href=f"#{h['id']}")
        a.string = text
        li.append(a)

        while stack[-1][0] >= level:
            stack.pop()
        parent_ul = stack[-1][1]
        parent_ul.append(li)

        child_ul = soup.new_tag("ul", **{"class": f"toc-list toc-level-{level + 1}"})
        li.append(child_ul)
        stack.append((level, child_ul))

    # Drop empty trailing <ul> children (leaves with no sub-headings)
    for ul in soup.select("ul.toc-list"):
        if not ul.find("li"):
            ul.decompose()

    nav = soup.new_tag("nav", id="toc-sidebar")
    nav_title = soup.new_tag("div", **{"class": "toc-title"})
    nav_title.string = "Contenido"
    nav.append(nav_title)
    nav.append(toc_root)

    toggle = soup.new_tag("button", id="toc-toggle", type="button", title="Mostrar/ocultar índice")
    toggle.string = "☰"

    style = soup.new_tag("style")
    style.string = """
#toc-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  width: 300px;
  height: 100vh;
  overflow-y: auto;
  background: var(--jp-layout-color1, #fff);
  border-right: 1px solid var(--jp-border-color2, #e0e0e0);
  padding: 20px 14px 40px 18px;
  box-sizing: border-box;
  font-family: var(--jp-ui-font-family, -apple-system, sans-serif);
  font-size: 13px;
  z-index: 1000;
  transition: transform 0.2s ease;
}
#toc-sidebar .toc-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--jp-ui-font-color2, #757575);
  margin-bottom: 10px;
}
#toc-sidebar ul.toc-list {
  list-style: none;
  margin: 0;
  padding-left: 0;
}
#toc-sidebar ul.toc-list ul.toc-list {
  padding-left: 14px;
}
#toc-sidebar li.toc-item {
  margin: 2px 0;
}
#toc-sidebar a {
  display: block;
  padding: 3px 8px;
  border-radius: 5px;
  color: var(--jp-content-font-color1, #222);
  text-decoration: none;
  line-height: 1.35;
  border-left: 2px solid transparent;
}
#toc-sidebar li.toc-h1 > a {
  font-weight: 700;
}
#toc-sidebar li.toc-h2 > a {
  font-weight: 600;
}
#toc-sidebar li.toc-h3 > a {
  color: var(--jp-ui-font-color2, #555);
  font-weight: 400;
}
#toc-sidebar a:hover {
  background: var(--jp-brand-color4, #f0f6ff);
}
#toc-sidebar a.active {
  color: var(--jp-brand-color1, #1565c0);
  border-left-color: var(--jp-brand-color1, #1565c0);
  background: var(--jp-brand-color4, #f0f6ff);
}
#toc-toggle {
  display: none;
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 1100;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  border: 1px solid var(--jp-border-color2, #e0e0e0);
  background: var(--jp-layout-color1, #fff);
  cursor: pointer;
  font-size: 16px;
}
body.jp-Notebook {
  padding-left: 300px;
  box-sizing: border-box;
}
@media (max-width: 900px) {
  body.jp-Notebook {
    padding-left: 0;
  }
  #toc-sidebar {
    transform: translateX(-100%);
  }
  #toc-sidebar.open {
    transform: translateX(0);
    box-shadow: 2px 0 12px rgba(0,0,0,0.15);
  }
  #toc-toggle {
    display: block;
  }
}
"""

    script = soup.new_tag("script")
    script.string = """
(function () {
  var sidebar = document.getElementById('toc-sidebar');
  var toggle = document.getElementById('toc-toggle');
  toggle.addEventListener('click', function () {
    sidebar.classList.toggle('open');
  });

  var links = Array.prototype.slice.call(sidebar.querySelectorAll('a'));
  var targets = links.map(function (a) {
    return document.getElementById(decodeURIComponent(a.getAttribute('href').slice(1)));
  });

  function onScroll() {
    var pos = window.scrollY + 80;
    var activeIndex = -1;
    for (var i = 0; i < targets.length; i++) {
      if (targets[i] && targets[i].offsetTop <= pos) {
        activeIndex = i;
      }
    }
    links.forEach(function (a, i) {
      a.classList.toggle('active', i === activeIndex);
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
"""

    soup.head.append(style)
    soup.body.insert(0, toggle)
    soup.body.insert(1, nav)
    soup.body.append(script)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def apply_style_kit_theme(html_path: Path) -> None:
    """Recolor nbconvert's own --jp-* theme variables with the Earthy Academic
    palette from style-kit/, set JetBrains Mono as the type, and add a
    light/dark toggle. Structure and layout stay Jupyter's own."""
    with open(html_path, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    flash_guard = soup.new_tag("script")
    flash_guard.string = (
        "(function(){try{var t=localStorage.getItem('theme');"
        "document.documentElement.setAttribute('data-theme',"
        "t==='dark'||t==='light'?t:'light');}catch(e){"
        "document.documentElement.setAttribute('data-theme','light');}})()"
    )

    font_link = soup.new_tag(
        "link",
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap",
    )

    style = soup.new_tag("style")
    style.string = """
/* Earthy Academic palette (style-kit/) mapped onto JupyterLab's own theme
   variables, so every element that already reads var(--jp-...) repaints
   without touching nbconvert's structural CSS. */
:root {
  --jp-layout-color0: #F5F0E8;
  --jp-layout-color1: #F5F0E8;
  --jp-layout-color2: #EDE4D3;
  --jp-layout-color3: #C8BAA2;
  --jp-layout-color4: #A0876A;

  --jp-content-font-color0: #241A12;
  --jp-content-font-color1: #3D2B1F;
  --jp-content-font-color2: rgba(61, 43, 31, 0.7);
  --jp-content-font-color3: rgba(61, 43, 31, 0.5);
  --jp-content-link-color: #B8541C;

  --jp-ui-font-color0: #241A12;
  --jp-ui-font-color1: #3D2B1F;
  --jp-ui-font-color2: rgba(61, 43, 31, 0.7);
  --jp-ui-font-color3: rgba(61, 43, 31, 0.5);

  --jp-border-color0: #C8BAA2;
  --jp-border-color1: #C8BAA2;
  --jp-border-color2: #DCD0BC;
  --jp-border-color3: #E7DFCE;
  --jp-inverse-border-color: #5E7A6A;

  --jp-brand-color0: #8C3E14;
  --jp-brand-color1: #B8541C;
  --jp-brand-color2: #D98F5F;
  --jp-brand-color3: #EAC3A8;
  --jp-brand-color4: #F0E0CE;
  --jp-accent-color1: #5E7A6A;

  --jp-cell-editor-background: #EDE4D3;
  --jp-cell-editor-border-color: #C8BAA2;
  --jp-cell-editor-active-background: #F5F0E8;
  --jp-cell-editor-active-border-color: #B8541C;
  --jp-cell-inprompt-font-color: #5E7A6A;
  --jp-cell-outprompt-font-color: #5E7A6A;
  --jp-cell-prompt-not-active-font-color: rgba(61, 43, 31, 0.5);

  --jp-input-background: #EDE4D3;
  --jp-input-border-color: #C8BAA2;
  --jp-input-active-background: #F5F0E8;
  --jp-input-hover-background: #F5F0E8;
  --jp-input-active-border-color: #B8541C;

  --jp-rendermime-table-row-background: #EDE4D3;
  --jp-rendermime-table-row-hover-background: #E3D5B8;
  --jp-rendermime-error-background: #F3D9CB;

  --jp-toolbar-background: #F5F0E8;
  --jp-toolbar-border-color: #C8BAA2;

  --jp-mirror-editor-keyword-color: #8C3E14;
  --jp-mirror-editor-atom-color: #5E7A6A;
  --jp-mirror-editor-number-color: #7A5A17;
  --jp-mirror-editor-def-color: #8C3E14;
  --jp-mirror-editor-variable-color: #3D2B1F;
  --jp-mirror-editor-variable-2-color: #8C3E14;
  --jp-mirror-editor-variable-3-color: #5E7A6A;
  --jp-mirror-editor-punctuation-color: #3D2B1F;
  --jp-mirror-editor-property-color: #8C3E14;
  --jp-mirror-editor-operator-color: #B8541C;
  --jp-mirror-editor-comment-color: #6B5940;
  --jp-mirror-editor-string-color: #2F5C3D;
  --jp-mirror-editor-string-2-color: #8C3E14;
  --jp-mirror-editor-meta-color: #5E7A6A;
  --jp-mirror-editor-qualifier-color: rgba(61, 43, 31, 0.7);
  --jp-mirror-editor-builtin-color: #3E6152;
  --jp-mirror-editor-decorator-color: #7A5A17;
  --jp-mirror-editor-bracket-color: #A0876A;
  --jp-mirror-editor-tag-color: #5E7A6A;
  --jp-mirror-editor-attribute-color: #8C3E14;

  --jp-cell-editor-shadow: rgba(61, 43, 31, 0.12);

  --jp-ui-font-family: 'JetBrains Mono', 'Courier New', monospace;
  --jp-content-font-family: 'JetBrains Mono', 'Courier New', monospace;
  --jp-code-font-family: 'JetBrains Mono', 'Courier New', monospace;
  --jp-code-font-family-default: 'JetBrains Mono', 'Courier New', monospace;
}

html[data-theme="dark"] {
  --jp-layout-color0: #1E1510;
  --jp-layout-color1: #1E1510;
  --jp-layout-color2: #281C12;
  --jp-layout-color3: #3E2A1C;
  --jp-layout-color4: #5E4530;

  --jp-content-font-color0: #FBF6EC;
  --jp-content-font-color1: #EDE4D3;
  --jp-content-font-color2: rgba(237, 228, 211, 0.7);
  --jp-content-font-color3: rgba(237, 228, 211, 0.5);
  --jp-content-link-color: #E07A3A;

  --jp-ui-font-color0: #FBF6EC;
  --jp-ui-font-color1: #EDE4D3;
  --jp-ui-font-color2: rgba(237, 228, 211, 0.7);
  --jp-ui-font-color3: rgba(237, 228, 211, 0.5);

  --jp-border-color0: #3E2A1C;
  --jp-border-color1: #3E2A1C;
  --jp-border-color2: #332216;
  --jp-border-color3: #2A1B12;
  --jp-inverse-border-color: #7FA694;

  --jp-brand-color0: #E07A3A;
  --jp-brand-color1: #E07A3A;
  --jp-brand-color2: #B8541C;
  --jp-brand-color3: #5E3319;
  --jp-brand-color4: #3A2415;
  --jp-accent-color1: #7FA694;

  --jp-cell-editor-background: #281C12;
  --jp-cell-editor-border-color: #3E2A1C;
  --jp-cell-editor-active-background: #1E1510;
  --jp-cell-editor-active-border-color: #E07A3A;
  --jp-cell-inprompt-font-color: #7FA694;
  --jp-cell-outprompt-font-color: #7FA694;
  --jp-cell-prompt-not-active-font-color: rgba(237, 228, 211, 0.5);

  --jp-input-background: #281C12;
  --jp-input-border-color: #3E2A1C;
  --jp-input-active-background: #1E1510;
  --jp-input-hover-background: #1E1510;
  --jp-input-active-border-color: #E07A3A;

  --jp-rendermime-table-row-background: #281C12;
  --jp-rendermime-table-row-hover-background: #33221A;
  --jp-rendermime-error-background: #4A2A1E;

  --jp-toolbar-background: #1E1510;
  --jp-toolbar-border-color: #3E2A1C;

  --jp-mirror-editor-keyword-color: #E07A3A;
  --jp-mirror-editor-atom-color: #7FA694;
  --jp-mirror-editor-number-color: #DFB040;
  --jp-mirror-editor-def-color: #E07A3A;
  --jp-mirror-editor-variable-color: #EDE4D3;
  --jp-mirror-editor-variable-2-color: #E07A3A;
  --jp-mirror-editor-variable-3-color: #7FA694;
  --jp-mirror-editor-punctuation-color: #EDE4D3;
  --jp-mirror-editor-property-color: #E07A3A;
  --jp-mirror-editor-operator-color: #E07A3A;
  --jp-mirror-editor-comment-color: #A8998A;
  --jp-mirror-editor-string-color: #5FA871;
  --jp-mirror-editor-string-2-color: #DFB040;
  --jp-mirror-editor-meta-color: #7FA694;
  --jp-mirror-editor-qualifier-color: rgba(237, 228, 211, 0.7);
  --jp-mirror-editor-builtin-color: #7FA694;
  --jp-mirror-editor-decorator-color: #DFB040;
  --jp-mirror-editor-bracket-color: #5E4530;
  --jp-mirror-editor-tag-color: #7FA694;
  --jp-mirror-editor-attribute-color: #E07A3A;

  --jp-cell-editor-shadow: rgba(0, 0, 0, 0.4);
}

/* Code cell style — terracotta accent stripe + rounded corners on the
   input box, sage prompts, and gap-fill rules for pygments classes
   nbconvert's own theme leaves uncolored (builtins, self/cls, decorators,
   def/class names), per the style-kit Python-code-cell mockup. */
.jp-InputArea-editor {
  border-radius: 6px;
  border-left: 3px solid var(--jp-brand-color1);
  box-shadow: 0 1px 3px 0 var(--jp-cell-editor-shadow), 0 1px 2px -1px var(--jp-cell-editor-shadow);
}
.jp-InputPrompt { opacity: 0.85; }
.jp-OutputPrompt { opacity: 0.7; }

.highlight .nb { color: var(--jp-mirror-editor-builtin-color); }
.highlight .bp { color: var(--jp-mirror-editor-builtin-color); font-style: italic; }
.highlight .nd { color: var(--jp-mirror-editor-decorator-color); font-weight: 600; }
.highlight .nf { color: var(--jp-mirror-editor-variable-color); font-weight: 700; }
.highlight .nc { color: var(--jp-mirror-editor-keyword-color); font-weight: 700; }
.highlight .o { color: var(--jp-mirror-editor-punctuation-color); font-weight: normal; }
.highlight .ow { color: var(--jp-mirror-editor-keyword-color); font-weight: bold; }

/* Theme toggle */
#theme-toggle {
  position: fixed;
  top: 10px;
  right: 10px;
  z-index: 1100;
  width: 34px;
  height: 34px;
  border-radius: 6px;
  border: 1px solid var(--jp-border-color2);
  background: var(--jp-layout-color1);
  color: var(--jp-content-font-color1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
#theme-toggle svg { width: 16px; height: 16px; fill: currentColor; }
#theme-toggle .sun-icon { display: none; }
html[data-theme="dark"] #theme-toggle .sun-icon { display: block; }
html[data-theme="dark"] #theme-toggle .moon-icon { display: none; }
"""

    toggle = soup.new_tag(
        "button", id="theme-toggle", type="button", title="Cambiar tema claro/oscuro"
    )
    toggle.append(BeautifulSoup(
        '<svg class="sun-icon" viewBox="0 0 20 20"><path fill-rule="evenodd" clip-rule="evenodd" '
        'd="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 '
        '1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 '
        '11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 '
        '0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 '
        '8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"/>'
        '</svg>',
        "html.parser",
    ))
    toggle.append(BeautifulSoup(
        '<svg class="moon-icon" viewBox="0 0 20 20"><path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 '
        '0 1010.586 10.586z"/></svg>',
        "html.parser",
    ))

    script = soup.new_tag("script")
    script.string = """
(function () {
  var btn = document.getElementById('theme-toggle');
  btn.setAttribute('aria-label',
    document.documentElement.getAttribute('data-theme') === 'dark'
      ? 'Switch to light theme' : 'Switch to dark theme');
  btn.addEventListener('click', function () {
    var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    btn.setAttribute('aria-label', next === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  });
})();
"""

    soup.head.insert(0, flash_guard)
    soup.head.append(font_link)
    soup.head.append(style)
    soup.body.insert(0, toggle)
    soup.body.append(script)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def main() -> None:
    notebook_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_NOTEBOOK
    notebook_path = Path(notebook_name)

    if not notebook_path.exists():
        sys.exit(f"Notebook not found: {notebook_path}")

    print(f"Converting {notebook_path} to HTML...")
    html_path = convert_to_html(notebook_path)

    print("Adding sidebar table of contents...")
    add_toc_sidebar(html_path)

    print("Applying style-kit Earthy Academic theme...")
    apply_style_kit_theme(html_path)

    print(f"Done: {html_path}")


if __name__ == "__main__":
    main()
