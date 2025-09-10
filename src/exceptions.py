from fastapi import HTTPException, status

class DeviceConnectionError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)

class DeviceTimeoutError(DeviceConnectionError):
    def __init__(self, detail: str):
        super().__init__(detail=detail)

class DeviceAuthenticationError(DeviceConnectionError):
    def __init__(self, detail: str):
        super().__init__(detail=detail)

class DeviceError(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(status_code=status_code, detail=detail)

class DeviceUnreachableError(DeviceConnectionError):
    def __init__(self, detail: str):
        super().__init__(detail=detail)

class UnsupportedDeviceTypeError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)