from PySide6.QtCore import QThread, Signal


class CallableWorker(QThread):
    """
    Worker tổng quát: nhận bất kỳ callable và chạy trong background thread.
    Phù hợp để wrap các tác vụ blocking (ADB calls, file I/O, v.v.) mà không đơ UI.

    Sử dụng:
        worker = CallableWorker(lambda: adb.fix_connection())
        worker.finished.connect(lambda result: print(result))
        worker.error.connect(lambda err: print(err))
        worker.start()
    """
    finished = Signal(object)  # Kết quả trả về từ callable (bất kỳ type)
    error = Signal(str)        # Thông báo lỗi nếu có exception

    def __init__(self, fn, *args, **kwargs):
        """
        Args:
            fn: Callable cần chạy trong background
            *args: Positional arguments cho fn
            **kwargs: Keyword arguments cho fn
        """
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
