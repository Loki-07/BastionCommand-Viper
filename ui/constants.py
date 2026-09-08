"""Shared dropdown value lists, centralized so field options stay consistent across
tabs and match the legacy model's documented choices (see backend/models.py comments
in the reference app)."""

STATUS_OPTIONS = ["Detection", "Containment", "Communication", "Recovery", "Closed"]
EVENT_TYPES = ["detection", "containment", "compromise", "communication", "recovery"]
ASSET_TYPES = ["Server", "Workstation", "Network Device", "Database", "Cloud Storage", "Other"]
SYSTEM_STATUS_OPTIONS = ["Investigating", "Compromised", "Patched", "Quarantined", "Recovered", "Clean"]
IOC_TYPES = ["IP", "Hash", "Domain", "Email", "Phone", "Hashtag","URL", "File Path", "Registry Key", "Process Name", "Certificate", "File Name","Other"]  
DUE_OUT_PRIORITIES = ["Low", "Medium", "High", "Critical"]
DUE_OUT_STATUSES = ["Pending", "In Progress", "Completed"]
POC_STATUS_OPTIONS = ["Employee", "Contractor", "Vendor", "Consultant"]
COMMUNICATION_TYPES = [
    "Vendor",
    "SA Deconfliction",
    "Final CAN",
    "CAN",
    "CCIR",
    "CTM",
    "Legal Request",
]
VENDOR_EMPLOYEE_OPTIONS = ["Employee", "Vendor", "Contractor","Partner"]

# Color coding, matching the legacy app's DESIGN_LANGUAGE_GUIDE.md palette and its
# Timeline.jsx TYPE_COLORS / DueOuts.jsx getPriorityColor mappings.
TIMELINE_TYPE_COLORS = {
    "detection": "#00d4ff",
    "containment": "#ffff00",
    "compromise": "#ff4444",
    "communication": "#00ff00",
    "recovery": "#00ccff",
}
DUE_OUT_PRIORITY_COLORS = {
    "Critical": "#ff4444",
    "High": "#ffbb33",
    "Medium": "#00d4ff",
    "Low": "#00d4ff",
}
