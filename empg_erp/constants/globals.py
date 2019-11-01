
MONTHLY_ATTENDANCE_DATE = 20
MONTHLY_ATTENDANCE_START_DATE = 21
PAGE_SIZE = 20

LINE_MANAGER = 'Line Manager'
HR_USER = 'HR User'
HR_MANAGER = 'HR Manager'
ADMINISTRATOR = 'Administrator'
USER = 'User'
USER_BULK_UPDATE_RESTRICTED_FIELDS = ['email']
EMPLOYEE = 'Employee'
EMPLOYEE_BULK_UPDATE_RESTRICTED_FIELDS = ['employee_number']
ATTENDANCE_MANAGER = 'Attendance Manager'
SYSTEM_MANAGER = 'System Manager'

SITE_MODULES_PATH = {
    "MUSTANG_SITE_NAME" : "mustang",
    "EXPLORER_SITE_NAME" : "explorer"
}

MONTH_COUNT_MAP = {
    'One Month': 1,
    'Two Months': 2,
    'Three Months': 3
}
LINE_MANAGER_GUIDES = 'Line Manager Guides'


CASUAL_LEAVE_TYPE = "Casual Leave"
EARNED_LEAVE_TYPE = "Earned Leave"
EMPLOYMENT_TYPE_PERMANENT = "Permanent"
ROSTER_STATUS_OFF = "Off"
ROSTER_STATUS_ON = "On"
ROSTER_STATUS_FLEXIBLE = "Flexible Timings"
ATTENDANCE_STATUS_PRESENT = "Present"
ATTENDANCE_STATUS_ABSENT = "Absent"
ATTENDANCE_STATUS_ON_LEAVE = "On Leave"
ROSTER_STATUS_HOLIDAY = "Holiday"
ATTENDANCE_STATUS_HALF_DAY_LEAVE = "Half Day"
ATTENDANCE_STATUS_HOURLY_LEAVE = "Hourly"

#TODO: rename used statuses of leaves with generic names
LEAVE_STATUS_OPEN = STATUS_OPEN = "Open"
LEAVE_STATUS_APPROVED = STATUS_APPROVED = "Approved"
LEAVE_STATUS_REJECTED = STATUS_REJECTED = "Rejected"
LEAVE_STATUS_CANCELLED = STATUS_CANCELLED = "Cancelled"

STATUS_DRAFT = "Draft" 
STATUS_REFUSED = "Refused"
STATUS_COMPLETED = "Completed"
STATUS_READY_TO_REVIEW = "Ready to Review"

LEAVE_STATUS_COLOR = {
    "Open": "#d2f1ff",
    "Approved": "#cef6d1",
    "Rejected": "#ffd7d7",
    "Cancelled": "#ffd19c",
}

BLOCK_BULK_UPDATE = ["Appraisal"]

LINE_MANAGER_ROLES = ["Line Manager", "Leave Approver"]

EXPORT_DATA_COUNT = '100000'

DOCUMENTS_ICONS = {
    "pdf"   : "fa fa-file-pdf-o pdf-red",
    "xlsx"  : "fa fa-file-excel-o xls-green",
    "image" : "fa fa-file-image-o image-purple",
    "ppt"   : "fa fa-file-powerpoint-o ppt-orange",
    "txt"   : "fa fa-file-text-o",
    "mp4"   : "fa fa-file-video-o",
    "docx"  : "fa fa-file-word-o doc-blue"
}
DOCUMENTS_EXT_ICONS = {
    ".xls" : DOCUMENTS_ICONS['xlsx'],
    ".xlsx": DOCUMENTS_ICONS['xlsx'],
    ".csv" : DOCUMENTS_ICONS['xlsx'],
    ".ods" : DOCUMENTS_ICONS['xlsx'],
    ".pdf" : DOCUMENTS_ICONS['pdf'],
    ".ppt" : DOCUMENTS_ICONS['ppt'],
    ".pptx" : DOCUMENTS_ICONS['ppt'],
    ".jpg" : DOCUMENTS_ICONS["image"],
    ".png" : DOCUMENTS_ICONS["image"],
    ".gif" : DOCUMENTS_ICONS["image"],
    ".jpeg": DOCUMENTS_ICONS["image"],
    ".doc" : DOCUMENTS_ICONS["docx"],
    ".docx": DOCUMENTS_ICONS["docx"],
    ".rtf" : DOCUMENTS_ICONS["docx"],
    ".txt" : DOCUMENTS_ICONS["txt"],
    ".mp4" : DOCUMENTS_ICONS["mp4"],
    ".mov" : DOCUMENTS_ICONS["mp4"],
    ".wmv" : DOCUMENTS_ICONS["mp4"],
    ".flv" : DOCUMENTS_ICONS["mp4"],
    ".avi" : DOCUMENTS_ICONS["mp4"]
}

POLICY_TYPE_PENALTY = "penalty"
POLICY_TYPE_REWARD = "reward"

DOC_LIST_CONDITIONS = {
    "equals" : "=",
    "not equals" : "!=",
    "like" : "like",
    "not like" : "not like",
    "in" : "in",
    "not in" : "not in",
    ">" : ">",
    "<" : "<",
    ">=" : ">=",
    "<=" : "<=",
    "is" : "=",
    "=" : "="
}

DOC_LIST_TYPES = ["Role", "IDs"]

WORKING_DAYS_IN_A_MONTH = 30