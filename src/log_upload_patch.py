from __future__ import annotations

import subprocess
import threading
import zipfile
from pathlib import Path

import requests
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
from qfluentwidgets import FluentIcon, PushButton, PrimaryPushButton, BodyLabel, TextEdit


_PATCH_INSTALLED = False


def _normalize_note_filename(note_text: str) -> str:
    note_text = (note_text or "").strip()
    if not note_text:
        return ""

    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        note_text = note_text.replace(char, "_")

    return note_text.strip(" ._")


def _build_logs_zip(note_text: str = ""):
    from ok import og
    from ok.gui.util.Alert import alert_error
    from ok.util.file import get_downloads_folder

    app_name = og.config.get('gui_title')
    downloads_path = Path(get_downloads_folder())
    zip_path = downloads_path / f"{app_name}-log.zip"

    downloads_path.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            note_name = _normalize_note_filename(note_text)
            if note_name:
                zipf.writestr(f"{note_name}.txt", "")

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


def _upload_logs_bg(note_text: str = ""):
    from ok import Logger, og
    from ok.gui.util.Alert import alert_error, alert_info

    upload_api = (og.config.get('log_upload_api') or '').strip()
    if not upload_api:
        alert_error(og.app.tr("Please configure log upload api in config"), tray=True)
        return

    try:
        zip_path = _build_logs_zip(note_text)
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


def _prompt_upload_note() -> str:
    from ok import og

    try:
        from PySide6.QtWidgets import QApplication
        parent = QApplication.activeWindow()
        dlg = QDialog(parent)
        if parent is not None:
            try:
                dlg.setPalette(parent.palette())
                dlg.setAutoFillBackground(True)
                # 如果主窗口使用了样式表，也一并应用
                parent_ss = parent.styleSheet()
                if parent_ss:
                    dlg.setStyleSheet(parent_ss)
            except Exception:
                pass
        dlg.setWindowTitle(og.app.tr("日志上传"))

        # 使用系统/父窗口标题栏（保持原生外观和行为）

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        tip = BodyLabel(og.app.tr("请输入遇到的问题描述（必填）"))
        tip.setWordWrap(True)
        layout.addWidget(tip)

        # 使用项目现有的 TextEdit（qfluentwidgets），以复用深/浅主题和样式
        text_edit = TextEdit()
        text_edit.setPlaceholderText(og.app.tr("例如：进入战斗时崩溃，重现步骤..."))
        text_edit.setMinimumHeight(120)
        layout.addWidget(text_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        send_btn = PrimaryPushButton(og.app.tr("上传"))
        cancel_btn = PushButton(og.app.tr("取消"))
        send_btn.setEnabled(False)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(send_btn)
        layout.addLayout(btn_row)

        def on_text_changed():
            send_btn.setEnabled(bool(text_edit.toPlainText().strip()))

        text_edit.textChanged.connect(on_text_changed)

        send_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)

        accepted = dlg.exec()
        if not accepted:
            return ""

        return text_edit.toPlainText().strip()
    except Exception:
        return ""


def _upload_logs():
    note_text = _prompt_upload_note()
    # 如果未填写说明，则中断上传（不弹窗、不上传）
    if not note_text:
        return

    worker = threading.Thread(target=_upload_logs_bg, args=(note_text,))
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