import logging
import time
import typing as t
from pathlib import Path

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class SingleFileModifiedHandler(PatternMatchingEventHandler):

    def __init__(
        self,
        *args,
        action: t.Union[t.Callable, None] = None,
        **kwargs,
    ):
        self.action = action
        super().__init__(*args, **kwargs)

    def on_modified(self, event: FileSystemEvent) -> None:
        super().on_modified(event)
        logger.info(f"File was modified: {event.src_path}")
        try:
            self.action and self.action()
            logger.debug(f"File processed successfully: {event.src_path}")
        except Exception:
            logger.exception(f"Processing file failed: {event.src_path}")


def watchdog_service(path: Path, action: t.Union[t.Callable, None] = None) -> None:
    """
    https://python-watchdog.readthedocs.io/en/stable/quickstart.html
    """

    import_file = Path(path).absolute()
    import_path = import_file.parent

    event_handler = SingleFileModifiedHandler(action=action, patterns=[import_file.name], ignore_directories=True)
    observer = Observer()
    observer.schedule(event_handler, str(import_path), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
