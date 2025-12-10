class BusinessError(Exception):
    def __init__(self, code: int, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class ErrorCode:
    MISSING_PARAMS = BusinessError(1001, "missing params")
    REQUEST_ERROR = BusinessError(1002, "request error")
    USER_NOT_FOUND = BusinessError(1003, "user not found")
    RATE_LIMIT = BusinessError(1004, "rate limit")
    SMS_CODE_ERROR = BusinessError(1005, "sms code error")
    USERNAME_EXISTS = BusinessError(1006, "username exists")
    CREDENTIALS_ERROR = BusinessError(1007, "credentials error")
    PERMISSION_DENIED = BusinessError(1008, "permission denied")
    USER_NOT_FOUND_OR_NO_HISTORY = BusinessError(1009, "user not found or no history")
    NO_PLANNED_DATA = BusinessError(1010, "no planned data")
    UNSUPPORTED_DATA_TYPE = BusinessError(1011, "unsupported data type")
    MENTOR_NOT_FOUND = BusinessError(1012, "mentor not found")
    NO_PROJECTS = BusinessError(1013, "no_projects")
    NO_MATCH = BusinessError(1014, "no_match")
    PAYMENT_FAILED = BusinessError(1015, "payment failed")
    GOAL_NOT_FOUND = BusinessError(1016, "goal notfound")
    JOB_PROFILE_NOT_FOUND = BusinessError(1017, "job profile not found")
    USER_INFO_INCOMPLETE = BusinessError(1018, "user info incomplete")
    TARGET_NOT_FOUND = BusinessError(1019, "target not found")
    SCHOOL_NOT_FOUND = BusinessError(1020, "school not found")
    RESUME_NOT_FOUND = BusinessError(1021, "resume_not_found")
    SESSION_NOT_FOUND = BusinessError(1022, "session_not_found")
    DEFAULT_NOT_DELETABLE = BusinessError(1023, "default not deletable")
    FORMAT_NOT_SUPPORTED = BusinessError(1024, "format_not_supported")
    FILE_TOO_LARGE = BusinessError(1025, "file_too_large")
    PARSE_FAILED = BusinessError(1026, "parse_failed")
