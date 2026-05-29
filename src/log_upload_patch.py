from __future__ import annotations

import subprocess
import threading
import zipfile
from pathlib import Path

import requests
from qfluentwidgets import FluentIcon, PushButton


_PATCH_INSTALLED = False


def _build_logs_zip():
    from ok import og
    from ok.gui.util.Alert import alert_error
    from ok.util.file import get_downloads_folder

    app_name = og.config.get('gui_title')
    downloads_path = Path(get_downloads_folder())
    zip_path = downloads_path / f"{app_name}-log.zip"

    downloads_path.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for folder in ["screenshots", "logs"]:
                source_dir = Path.cwd() / folder
                if not source_dir.is_dir():
                    continue
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        zipf.write(file_path, file_path.relative_to(Path.cwd()))
    except Exception as exc:
        alert_error(f"{og.app.tr('Export failed')}: {exc}", tray=True)
        from ok import Logger

        Logger.get_logger(__name__).error('export_logs exception', exc)
        raise

    return zip_path


def _export_logs():
    try:
        zip_path = _build_logs_zip()
        subprocess.run(["explorer", f"/select,{zip_path}"])
    except Exception:
        return


def _upload_logs_bg():
    from ok import Logger, og
    from ok.gui.util.Alert import alert_error, alert_info

    upload_api = (og.config.get('log_upload_api') or '').strip()
    if not upload_api:
        alert_error(og.app.tr("Please configure log upload api in config"), tray=True)
        return

    try:
        zip_path = _build_logs_zip()
        with open(zip_path, 'rb') as file_handle:
            response = requests.post(
                upload_api,
                files={'file': (zip_path.name, file_handle, 'application/zip')},
                data={'app_name': og.config.get('gui_title')},
                timeout=60,
            )
        response.raise_for_status()
        alert_info(og.app.tr("Upload succeeded"), tray=True)
    except Exception as exc:
        alert_error(f"{og.app.tr('Upload failed')}: {exc}", tray=True)
        Logger.get_logger(__name__).error('upload_logs exception', exc)


def _upload_logs():
    worker = threading.Thread(target=_upload_logs_bg)
    worker.daemon = True
    worker.start()


def install_log_upload_patch():
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return

    from ok.gui.start.StartTab import StartTab

    original_init = StartTab.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        try:
            from ok import og
            label = og.app.tr("Upload Logs")
        except Exception:
            label = self.tr("Upload Logs")

        self.upload_log_button = PushButton(FluentIcon.SEND, label)
        self.upload_log_button.clicked.connect(_upload_logs)

        try:
            self.debug_layout.insertWidget(1, self.upload_log_button)
        except Exception:
            self.debug_layout.addWidget(self.upload_log_button)

    StartTab.__init__ = patched_init
    StartTab.export_logs = staticmethod(_export_logs)
    StartTab.upload_logs = staticmethod(_upload_logs)
    StartTab._build_logs_zip = staticmethod(_build_logs_zip)

    _PATCH_INSTALLED = True