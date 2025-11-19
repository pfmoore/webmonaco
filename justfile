server:
    uv run --with-requirements requirements.txt flask -A app.webmonaco run

update version:
    py get_assets.py {{version}}
    git add app/bin
    git commit -m "Monaco {{version}}"
    git push
    fly deploy
    py -m webbrowser https://webmonaco.fly.dev

