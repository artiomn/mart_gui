import logging
from io import StringIO


LOG_FORMAT = '| %(asctime)s | %(name)s-%(levelname)s:  %(message)s '
FORMATTER = logging.Formatter(LOG_FORMAT)

main_handler = logging.StreamHandler()
main_handler.setLevel(logging.INFO)
main_handler.setFormatter(FORMATTER)

streamer = StringIO()
stream_handler = logging.StreamHandler(stream=streamer)
stream_handler.setFormatter(FORMATTER)

# Root Logger
logging.basicConfig(level=main_handler.level, handlers=[main_handler, stream_handler])
