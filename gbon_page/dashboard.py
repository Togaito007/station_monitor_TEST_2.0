from pathlib import Path


def render_dashboard_html() -> str:
    base = Path(__file__).resolve().parent
    html = (base / "index.html").read_text(encoding="utf-8")
    css = (base / "styles.css").read_text(encoding="utf-8")
    js = (base / "script.js").read_text(encoding="utf-8")
    return html.replace("<!--CSS-->", css).replace("<!--JS-->", js)


if __name__ == "__main__":
    print(render_dashboard_html())
