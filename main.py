from src.config import config
from src.log_upload_patch import install_log_upload_patch

if __name__ == '__main__':
    config = config
    install_log_upload_patch()
    import ok
    ok = ok.OK(config)
    ok.start()
