# Orbit Browser

A small desktop browser with a Chrome-inspired interface, built on Electron's
Chromium engine. Unlike the HTML mockup, this app renders websites in isolated
Chromium web contents rather than embedding them in an iframe.

## Run on macOS

Install Node.js 26 LTS or later, then from this directory run:

```sh
npm install
npm start
```

The app supports tabs, address/search, back/forward/reload, and session
bookmarks. Website JavaScript runs with Node integration disabled and context
isolation enabled. Browser permission requests are denied by default.
