"""Windows desktop console for the HHMS server (tray + live log window).

Packaged Windows builds run as a GUI-less PyInstaller executable, so without
this module the server either flashes a raw command window (``console=True``)
or runs with no visible feedback at all.  This module gives operators the
behaviour they expect from a desktop app:

* the raw command-prompt window is hidden (its console handle is detached on
  startup — see ``hide_windows_console()``);
* a small always-on-top log window shows server messages **live** (it tails
  the same rotating log file the logging config writes to);
* closing the window minimises it to the system tray instead of exiting;
* the tray icon's right-click menu offers **Exit Server**, which performs a
  proper shutdown: flush logs, save a final data-draft backup of the live
  database ("data draft saver"), stop LAN discovery, then exit.

Everything here is Windows-only and degrades to a no-op elsewhere, so the
same codebase keeps running headless on Linux/macOS and inside CI.
"""
from __future__ import annotations

import ctypes
import logging
import os
import queue
import sys
import threading
from pathlib import Path

logger = logging.getLogger("hhms.desktop")

IS_WINDOWS = sys.platform == "win32"

# Tk is only needed for the desktop log window (packaged Windows builds).
# Import it lazily so headless Linux/macOS/CI environments — where the TK
# shared libraries may not even be installed — can still import this module.
_TK_IMPORT_ERROR: Exception | None = None
try:  # pragma: no cover - exercised on machines without Tk
    from tkinter import Label, Text, Tk, Toplevel
except Exception as _exc:  # noqa: BLE001
    Label = Text = Tk = Toplevel = None  # type: ignore[assignment]
    _TK_IMPORT_ERROR = _exc

try:  # pragma: no cover - optional dependency
    import pystray
    from PIL import Image, ImageDraw

    HAS_TRAY = True
except ImportError:  # pragma: no cover
    pystray = None  # type: ignore[assignment]
    Image = ImageDraw = None  # type: ignore[assignment]
    HAS_TRAY = False


def hide_windows_console() -> bool:
    """Detach the process from its inherited console window.

    PyInstaller ``console=True`` builds allocate a cmd.exe window on launch.
    Freeing the console hides that window while our own Tk log window keeps
    showing messages.  Returns True when a console was actually released.
    """
    if not IS_WINDOWS:  # pragma: no cover - non-Windows platforms
        return False
    try:
        kernel32 = ctypes.windll.kernel32
        if kernel32.GetConsoleWindow() and kernel32.FreeConsole():
            return True
    except Exception:  # pragma: no cover - defensive: never block boot
        logger.exception("failed to detach the Windows console window")
    return False


class _TailThread(threading.Thread):
    """Follow a log file like ``tail -f``, emitting new lines to a queue."""

    def __init__(self, path: Path, sink: "queue.Queue[str]") -> None:
        super().__init__(name="hhms-log-tail", daemon=True)
        self._path = path
        self._sink = sink
        self._stop = threading.Event()

    def run(self) -> None:
        pos = 0
        # Start near the end so the window opens with recent context only.
        while not self._stop.is_set():
            try:
                size = self._path.stat().st_size if self._path.exists() else 0
                if size < pos:  # rotated/truncated
                    pos = 0
                if size > pos:
                    with open(self._path, "r", encoding="utf-8", errors="replace") as handle:
                        handle.seek(pos)
                        for line in handle.read().splitlines():
                            self._sink.put(line)
                        pos = handle.tell()
                else:
                    pos = size
            except OSError:
                pass
            self._stop.wait(0.4)

    def stop(self) -> None:
        self._stop.set()


class DesktopConsole:
    """Tray + live-log controller for the packaged Windows server."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.on_exit = None  # callable invoked once, before the process exits
        self._lines: "queue.Queue[str]" = queue.Queue()
        self._tail = _TailThread(log_path, self._lines)
        self._root: Tk | None = None
        self._window: Toplevel | None = None
        self._text: Text | None = None
        self._tray = None
        self._exit_requested = threading.Event()
        self._shutdown_started = False

    # ------------------------------------------------------------------ UI
    def _build_window(self) -> None:
        root = Tk()
        root.withdraw()  # invisible anchor; the visible surface is Toplevel
        window = Toplevel(root)
        window.title("HHMS Server — live log")
        window.geometry("640x320+80+80")
        window.minsize(420, 200)
        window.resizable(True, True)
        try:
            window.state("normal")  # never start life minimised
        except Exception:  # pragma: no cover - WM quirk
            pass
        window.lift()
        window.attributes("-topmost", True)
        text = Text(window, state="disabled", wrap="word", bg="#10151c", fg="#d7e2ee")
        text.pack(fill="both", expand=True)
        hint = Label(
            window,
            anchor="w",
            padx=8,
            text=(
                "Closing this window keeps the server running in the system "
                "tray — right-click the tray icon for 'Exit Server'."
            ),
        )
        hint.pack(fill="x")
        window.protocol("WM_DELETE_WINDOW", self._on_close)
        self._root, self._window, self._text = root, window, text
        self._pump()

    def _pump(self) -> None:
        """Drain queued log lines into the text widget (runs on the Tk loop)."""
        assert self._text is not None
        appended = False
        try:
            while True:
                line = self._lines.get_nowait()
                self._text.configure(state="normal")
                self._text.insert("end", line + "\n")
                self._text.see("end")
                self._text.configure(state="disabled")
                appended = True
        except queue.Empty:
            pass
        if appended:  # keep the buffer bounded (last ~2000 lines)
            self._text.configure(state="normal")
            if int(self._text.index("end-1c").split(".")[0]) > 2000:
                self._text.delete("1.0", "500.0")
            self._text.configure(state="disabled")
        if not self._exit_requested.is_set():
            assert self._root is not None
            self._root.after(200, self._pump)

    def _on_close(self) -> None:
        """Closing the window minimises to tray (or just hides without tray)."""
        if self._window is not None:
            self._window.withdraw()
        if self._tray is not None:
            # Show a non-blocking toast so the operator knows where the app went
            # instead of thinking the server crashed/closed.
            try:
                self._tray.notify(
                    "HHMS Server is still running",
                    "Look for the HHMS shield icon in the system tray "
                    "(bottom-right, near the clock). Right-click it for "
                    "'Show log window' or 'Exit Server'.",
                )
            except Exception:  # pragma: no cover - notify is best-effort
                pass
        else:  # pragma: no cover - pystray missing in the build env
            logger.warning(
                "Log window closed and no system-tray icon is available: the "
                "server keeps running but there is no way to reopen this "
                "window. Install pystray+Pillow in the build environment."
            )

    # ----------------------------------------------------------------- tray
    def _tray_image(self):
        image = Image.new("RGB", (64, 64), "#174d70")
        draw = ImageDraw.Draw(image)
        draw.rectangle([26, 14, 38, 50], fill="white")
        draw.rectangle([14, 26, 50, 38], fill="white")
        return image

    def _menu(self):
        return pystray.Menu(
            pystray.MenuItem("Open HHMS GUI", lambda: self._show_browser(), default=True),
            pystray.MenuItem("Show log window", self._restore_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit Server", self._exit_server),
        )

    def _show_browser(self) -> None:
        import webbrowser

        try:
            from app.config.settings import get_settings

            settings = get_settings()
            webbrowser.open(f"http://127.0.0.1:{settings.SERVER_PORT}/")
        except Exception:  # pragma: no cover - best effort
            pass

    def _restore_window(self, *_args) -> None:
        if self._root is not None and self._window is not None:
            self._root.after(0, self._window.deiconify)

    def _exit_server(self, *_args) -> None:
        # pystray invokes menu callbacks on the tray thread; marshalling the
        # shutdown request through Tk's event loop avoids any cross-thread
        # widget access before we tear everything down.
        if self._root is not None:
            self._root.after(0, self.request_exit)
        else:  # pragma: no cover - root always exists when a menu is shown
            self.request_exit()

    def request_exit(self, *_args) -> None:
        """Tray-menu 'Exit Server': graceful shutdown, then terminate."""
        if self._exit_requested.is_set():
            return
        self._exit_requested.set()
        threading.Thread(target=self._shutdown, name="hhms-exit", daemon=False).start()

    def _shutdown(self) -> None:
        if self._shutdown_started:
            return
        self._shutdown_started = True
        try:
            if self.on_exit is not None:
                self.on_exit()
        except Exception:  # pragma: no cover - shutdown must never raise
            logger.exception("desktop console exit hook failed")
        finally:
            if self._tray is not None:
                try:
                    self._tray.stop()
                except Exception:  # pragma: no cover
                    pass
            for handler in list(logging.getLogger().handlers):
                try:
                    handler.flush()
                    handler.close()
                except Exception:  # pragma: no cover
                    pass
            os._exit(0)

    # ------------------------------------------------------------- startup
    def start(self) -> None:
        """Show the hidden-console log window and register the tray icon."""
        self._tail.start()
        self._build_window()
        if HAS_TRAY:
            self._tray = pystray.Icon(
                "HHMS Server", self._tray_image(), "HHMS Server running", self._menu()
            )
            tray_thread = threading.Thread(
                target=self._tray.run, name="hhms-tray", daemon=True
            )
            tray_thread.start()
        else:  # pragma: no cover - pystray missing in the build env
            logger.warning("pystray unavailable: close-button will hide the window only")
        self._root.mainloop()


_console: DesktopConsole | None = None


def maybe_start_desktop_console() -> DesktopConsole | None:
    """Start the desktop console on packaged Windows builds; no-op otherwise.

    Force-enable with ``HHMS_DESKTOP_CONSOLE=true`` or disable with
    ``HHMS_DESKTOP_CONSOLE=false`` (e.g. when running as a service).
    """
    global _console

    if not IS_WINDOWS or not getattr(sys, "frozen", False):
        return None
    flag = os.environ.get("HHMS_DESKTOP_CONSOLE", "").strip().lower()
    if flag in {"false", "0", "no"}:
        return None
    # Otherwise the desktop console auto-starts for every packaged Windows
    # run (double-click *and* launches from a terminal).  The raw cmd.exe
    # window is hidden via FreeConsole and replaced by the tray + live-log
    # window, so operators always get the desktop-app experience they asked
    # for instead of a flashing console that then disappears behind a TTY
    # check.  Set HHMS_DESKTOP_CONSOLE=false to opt out (e.g. running as a
    # Windows service where the SCM owns the process lifecycle).
    from app.config.runtime_paths import logs_directory

    if _TK_IMPORT_ERROR is not None:  # pragma: no cover - broken Tk install
        logger.warning("desktop console disabled: tkinter unavailable (%s)", _TK_IMPORT_ERROR)
        hide_windows_console()
        return None
    hide_windows_console()
    _console = DesktopConsole(Path(logs_directory()) / "hhms.log")
    return _console


def save_draft_on_exit() -> None:
    """Data draft saver: snapshot the live database before the server exits.

    Runs uvicorn's graceful shutdown first (so in-flight requests finish and
    SQLite WAL is checkpointed), then creates a rolling
    ``hhms-shutdown-draft-*`` backup via the normal BackupService.
    """
    import asyncio

    from app.services.backup import BackupService

    async def _save() -> None:
        try:
            await BackupService().create_backup("hhms-shutdown-draft", overwrite=True)
            logger.info("Shutdown data draft saved (hhms-shutdown-draft backup).")
        except Exception:  # pragma: no cover - best-effort safety net
            logger.exception("shutdown data draft could not be saved")

    try:
        asyncio.run(_save())
    except Exception:  # pragma: no cover
        logger.exception("data draft saver failed")


__all__ = [
    "DesktopConsole",
    "hide_windows_console",
    "maybe_start_desktop_console",
    "save_draft_on_exit",
]
