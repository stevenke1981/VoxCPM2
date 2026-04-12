"""VoxCPM2 Studio — entry point."""

from __future__ import annotations

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-22s  %(levelname)-8s  %(message)s",
    stream=sys.stdout,
)


def main() -> None:
    from app.utils.config_manager import ConfigManager
    from app.utils.i18n import init as i18n_init

    # Read language from persisted config before building any UI widgets.
    cfg = ConfigManager()
    i18n_init(cfg.get("language", "zh-TW"))

    from app.ui.main_window import MainWindow

    app = MainWindow(config=cfg)
    app.mainloop()


if __name__ == "__main__":
    main()
