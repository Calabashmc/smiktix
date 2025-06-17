from app import create_app
from app.model import db
from app.model.lookup_tables import (
    AppDefaults, BenefitsLookup, BudgetBucketsLookup, ChangeFreezeReasonLookup,
    ChangeTypeLookup, ChangeWindowLookup, Compliance, DeliveryMethodLookup,
    HostingLookup, ImpactLookup, Importance, KBATypesLookup, LikelihoodLookup,
    LocationLookup, ModelLookup, OfficeHours, PauseReasons, PlatformLookup,
    PriorityLookup, ResolutionLookup, RiskLookup, StatusLookup, SupportTypeLookup
)
from app.model.model_category import Category, Subcategory
from app.model.model_change import ChangeReasons
from app.model.model_cmdb import OperatingSystem
from app.model.model_interaction import Source
from app.model.model_release import ReleaseTypesLookup
from app.model.model_user import Role, Department, Team, User


def seed_lookup_table(model, unique_fields, data):
    """
    Seed a lookup table with the given data if entries do not already exist.

    Args:
        model: SQLAlchemy model class.
        unique_fields: List of field names to use for uniqueness check.
        data: List of dicts containing row data.
    """
    for row in data:
        filters = [
            getattr(model, field) == row[field]
            for field in unique_fields
            if field in row
        ]
        if not db.session.query(model).filter(*filters).first():
            db.session.add(model(**row))


def seed_data():
    """Seed the database with initial data."""
    if not AppDefaults.query.get(1):
        default_data = {
            "servicedesk_phone": "0408012816",
            "servicedesk_email": "service.desk@myorg",
            "servicedesk_open_hour": "09:11",
            "servicedesk_close_hour": "17:00",
            "servicedesk_timezone": "+10",
            "change_default_risk": "CR4",
            "cmdb_default_icon": "alien.svg",
            "incident_default_impact": "Medium",
            "incident_default_priority": "P3",
            "incident_default_urgency": "Medium",
            "problem_default_priority": "P4",
            "support_team_default_id": 1
        }
        AppDefaults.set_app_defaults(default_data)

    # First pass: Seed tables without foreign key dependencies
    independent_tables = {
        BenefitsLookup: {
            "data": [
                {"benefit": "Cost Savings", "comment": "Reduction in operational expenses or resource usage"},
                {"benefit": "Efficiency Gains",
                 "comment": "Improvements in productivity or faster delivery of services"},
                {"benefit": "Improved Quality", "comment": "Enhancements to service reliability or performance"},
                {"benefit": "Customer Satisfaction",
                 "comment": "Better customer experience or higher satisfaction scores"},
                {"benefit": "Compliance", "comment": "Meeting legal, regulatory, or organizational requirements"},
                {"benefit": "Risk Reduction", "comment": "Mitigating risks or improving security"},
                {"benefit": "Process Improvement",
                 "comment": "Decrease process steps, time to perform, or improve value chain"},
                {"benefit": "Staff Wellbeing", "comment": "Makes life better for our staff"}
            ],
            "unique_fields": ["benefit"]
        },
        BudgetBucketsLookup: {
            "data": [
                {"budget_bucket": "Discretionary",
                 "comment": "Predefined pool of funds available without needing higher-level approval"},
                {"budget_bucket": "Operational", "comment": "Covers the day-to-day running of the organisation"},
                {"budget_bucket": "Capital", "comment": "Allocated for the purchase of long-term assets"},
                {"budget_bucket": "Project",
                 "comment": "This budget is created based on the scope, objectives, and estimated costs of the project"},
                {"budget_bucket": "Contingency",
                 "comment": "A reserve fund set aside for unexpected expenses or emergencies that arise during a budget period"}
            ],
            "unique_fields": ["budget_bucket"]
        },
        Category: {
            "data": [
                {"id": 1, "name": "Accounts and Access"},
                {"id": 2, "name": "Collaboration (Email, Messaging)"},
                {"id": 3, "name": "Telephony"},
                {"id": 4, "name": "Interactions and Requests"},
                {"id": 5, "name": "Licences"},
                {"id": 6, "name": "Documentation"},
                {"id": 7, "name": "Applications/Software"},
                {"id": 8, "name": "Cloud and Platform"},
                {"id": 9, "name": "End User Compute"},
                {"id": 10, "name": "Network and Connectivity"},
                {"id": 11, "name": "Security"},
                {"id": 12, "name": "Servers and VMs"},
                {"id": 13, "name": "Social or Cultural"},
                {"id": 14, "name": "General Suggestion"},
                {"id": 15, "name": "Process Improvement"},
                {"id": 16, "name": "New Process Suggestion"},
                {"id": 17, "name": "Data Management"}
            ],
            "unique_fields": ["id"]
        },
        ChangeFreezeReasonLookup: {
            "data": [
                {"reason": "Maintenance Window", "comment": "Scheduled maintenance or upgrades"},
                {"reason": "High Traffic Period", "comment": "Any anticipated high traffic periods"},
                {"reason": "Regulatory Compliance",
                 "comment": "Preventing changes due to audit or regulatory requirements"},
                {"reason": "Critical Event", "comment": "Product launch, system migration, or similar events"},
                {"reason": "Holiday Period", "comment": "Internal holiday season freezes to ensure system stability"},
                {"reason": "Customer Request", "comment": "Freeze requested by a key customer"}
            ],
            "unique_fields": ["reason"]
        },
        ChangeReasons: {
            "data": [
                {"reason": "Application - Patch/Bug Fix"},
                {"reason": "Application - Version Upgrade"},
                {"reason": "Application - Install New"},
                {"reason": "Security - Prevention"},
                {"reason": "Security - Policy Change"},
                {"reason": "Infrastructure - Improvements/Enhancements"},
                {"reason": "Infrastructure - Add New functionality"}
            ],
            "unique_fields": ["reason"]
        },
        ChangeTypeLookup: {
            "data": [
                {"change_type": "Standard", "comment": "Pre-approved change"},
                {"change_type": "Emergency", "comment": "Urgent change"},
                {"change_type": "Normal", "comment": "Changes needing planning and approval"}
            ],
            "unique_fields": ["change_type"]
        },
        ChangeWindowLookup: {
            "data": [
                {"day": "Saturday", "start_time": "14:00:00", "length": 12, "active": True},
                {"day": "Thursday", "start_time": "18:00:00", "length": 12, "active": True}
            ],
            "unique_fields": ["day"]
        },
        Compliance: {
            "data": [
                {"compliance_standard": "GDPR", "comment": "General Data Protection Regulation"},
                {"compliance_standard": "HIPAA", "comment": "Health Insurance Portability and Accountability Act"},
                {"compliance_standard": "PCI DSS", "comment": "Payment Card Industry Data Security Standard"},
                {"compliance_standard": "SOX", "comment": "Sarbanes-Oxley Act"},
                {"compliance_standard": "ISO 27001",
                 "comment": "Security Payment Card Industry Data Security Standard"},
                {"compliance_standard": "ISO 9001",
                 "comment": "Quality Security Payment Card Industry Data Security Standard"},
                {"compliance_standard": "ISO 20000",
                 "comment": "ITSM Security Payment Card Industry Data Security Standard"}
            ],
            "unique_fields": ["compliance_standard"]
        },
        DeliveryMethodLookup: {
            "data": [
                {"delivery_method": "Internal", "comment": "Internal hosted and supported"},
                {"delivery_method": "Hybrid", "comment": "Hybrid Internal & Cloud"},
                {"delivery_method": "PaaS", "comment": "Platform as a Service"},
                {"delivery_method": "SaaS", "comment": "Software as a Platform as a Service"}
            ],
            "unique_fields": ["delivery_method"]
        },
        Department: {
            "data": [
                {"description": "Information Technology", "name": "IT"},
                {"description": "Sales enablers", "name": "Marketing"},
                {"description": "Head Honcho", "name": "Office of the CEO"},
                {"description": "Bring in the bucks", "name": "Sales"},
                {"description": "Back office", "name": "Administration"},
                {"description": "Accounting", "name": "Finance"},
                {"description": "Employee related relations", "name": "People and Culture"}
            ],
            "unique_fields": ["name"]
        },
        HostingLookup: {
            "data": [
                {"hosting": "local", "comment": "Hosted internally"},
                {"hosting": "hybrid", "comment": "Hybrid local/cloud"},
                {"hosting": "Cloud SaaS", "comment": "Software as a Service"},
                {"hosting": "Cloud PaaS", "comment": "Platform as a Service"}
            ],
            "unique_fields": ["hosting"]
        },
        ImpactLookup: {
            "data": [
                {"impact": "Individuals", "comment": "Various individual contributors"},
                {"impact": "Group", "comment": "A group performing a specific task"},
                {"impact": "Team", "comment": "An Internal team"},
                {"impact": "Department", "comment": "Entire Department"},
                {"impact": "Organisation", "comment": "The entire company"},
                {"impact": "Suppliers", "comment": "Our suppliers"},
                {"impact": "Customers", "comment": "Our customers"},
                {"impact": "Public", "comment": "General public who interact with us in some way"}
            ],
            "unique_fields": ["impact"]
        },
        Importance: {
            "data": [
                {"rating": 3, "note": "Important but not essential", "importance": "Silver"},
                {"rating": 5, "note": "Crucial for business functions", "importance": "Platinum"},
                {"rating": 0, "note": "Low priority, detected shadow IT", "importance": "Rust"},
                {"rating": 2, "note": "Useful for business but not essential", "importance": "Bronze"},
                {"rating": 4, "note": "Highly Important for business function", "importance": "Gold"},
                {"rating": 1, "note": "Low volume use, assists with departmental or individual functions",
                 "importance": "Tin"}
            ],
            "unique_fields": ["importance"]
        },
        KBATypesLookup: {
            "data": [
                {"comment": "End User Instructions", "article_type": "Instructional"},
                {"comment": "Frequently Asked", "article_type": "FAQ"},
                {"comment": "Process procedure", "article_type": "Procedure"},
                {"comment": "High level Process", "article_type": "Process"},
                {"comment": "Policy", "article_type": "Policy"},
                {"comment": "IT run books", "article_type": "Work Instruction"}
            ],
            "unique_fields": ["article_type"]
        },
        LikelihoodLookup: {
            "data": [
                {"likelihood": "Likely", "comment": "It's likely that the idea will be acted upon"},
                {"likelihood": "Possible",
                 "comment": "Could go either way but will possibly be acted upon if resourcing is favourable"},
                {"likelihood": "Unlikely", "comment": "The idea is unlikely to proceed based on the low vote count."}
            ],
            "unique_fields": ["likelihood"]
        },
        LocationLookup: {
            "data": [
                {"location": "Head Office", "comment": "Main Office"}
            ],
            "unique_fields": ["location"]
        },
        ModelLookup: {
            "data": [
                {"name": "Change"},
                {"name": "Cmdb"},
                {"name": "Idea"},
                {"name": "Interaction"},
                {"name": "Knowledge"},
                {"name": "Problem"},
                {"name": "Release"}
            ],
            "unique_fields": ["name"]
        },
        OfficeHours: {
            "data": [
                {
                    "id": 1,
                    "open_hour": "08:00:00",
                    "close_hour": "17:00:00",
                    "state": "QLD",
                    "province": "Gold Coast",
                    "location": "HQ",
                    "address": None,
                    "timezone": "Australia/Brisbane",
                    "date_format": "%d/%b/%Y",
                    "country": "Australia",
                    "country_code": "AU",
                    "datetime_format": "%d/%b/%Y %H:%M"
                }
            ],
            "unique_fields": ["id"]
        },
        OperatingSystem: {
            "data": [
                {"os": "Windows"},
                {"os": "Mac"},
                {"os": "Linux"}
            ],
            "unique_fields": ["os"]
        },
        PauseReasons: {
            "data": [
                {"reason": "Vendor - awaiting resolution"},
                {"reason": "Support tech - travelling to site"},
                {"reason": "Support tech - waiting on parts"},
                {"reason": "Customer - awaiting feedback/information"}
            ],
            "unique_fields": ["reason"]
        },
        PlatformLookup: {
            "data": [
                {"platform": "Windows", "comment": "If you must"},
                {"platform": "Mac", "comment": "If you can afford it"},
                {"platform": "Linux", "comment": "If you are smart"}
            ],
            "unique_fields": ["platform"]
        },
        PriorityLookup: {
            "data": [
                {"priority": "P1", "image_url": "/static/images/priority/p1.png", "respond_by": 0.5, "resolve_by": 2,
                 "twentyfour_seven": True},
                {"priority": "P2", "image_url": "/static/images/priority/p2.png", "respond_by": 2, "resolve_by": 4,
                 "twentyfour_seven": True},
                {"priority": "P3", "image_url": "/static/images/priority/p3.png", "respond_by": 4, "resolve_by": 16,
                 "twentyfour_seven": False},
                {"priority": "P5", "image_url": "/static/images/priority/p5.png", "respond_by": 32, "resolve_by": 48,
                 "twentyfour_seven": False},
                {"priority": "P4", "image_url": "/static/images/priority/p4.png", "respond_by": 16, "resolve_by": 32,
                 "twentyfour_seven": False}
            ],
            "unique_fields": ["priority"]
        },
        ReleaseTypesLookup: {
            "data": [
                {"release_type": "Security Patch", "comment": "Software upgrade to resolve security issues"},
                {"release_type": "Incremental Upgrade", "comment": "Minor version increment"},
                {"release_type": "New Install", "comment": "New product release"},
                {"release_type": "Database Migration", "comment": "Database upgrade"},
                {"release_type": "Infrastructure Rollout", "comment": "Infrastructure upgrade"},
                {"release_type": "SaaS Implementation", "comment": "Software-as-a-Service implementation"}
            ],
            "unique_fields": ["release_type"]
        },
        ResolutionLookup: {
            "data": [
                {"resolution": "Rolled Back due to failed Change", "comment": "The Change failed", "model": "Change"},
                {"resolution": "Rolled Back due to time constraints",
                 "comment": "The Change was taking longer than expected or exceeding Change Window", "model": "Change"},
                {"resolution": "Change cancelled", "comment": "A decision was made not to proceed with the Change",
                 "model": "Change"},
                {"resolution": "Change completed Successfully", "comment": "The Change was implemented as planned",
                 "model": "Change"},
                {"resolution": "Idea Implemented via Change Enablement",
                 "comment": "The Idea was actioned operationally", "model": "Idea"},
                {"resolution": "Idea Implemented as BAU", "comment": "The Idea was a process or practice improvement",
                 "model": "Idea"},
                {"resolution": "Idea Rejected as impractical",
                 "comment": "The Idea was voted down due to lack of interest or other reason", "model": "Idea"},
                {"resolution": "Idea Rejected due to resource limitations",
                 "comment": "The Benefits did not outweigh the required resource allocation", "model": "Idea"},
                {"resolution": "Idea moved to Project", "comment": "The Idea is accepted and is now a Project",
                 "model": "Idea"},
                {"resolution": "Duplicate/Ticket created in Error",
                 "comment": "A duplicate incident for the customer already exists. Ticket was created in error",
                 "model": "Interaction"},
                {"resolution": "External Vendor / Party",
                 "comment": "Issue occurred external to the organisation that was caused by an external party or vendor",
                 "model": "Interaction"},
                {"resolution": "Hardware Error",
                 "comment": "Fault Cleared, Device replaced with existing or different unit", "model": "Interaction"},
                {"resolution": "Inaccurate or Incomplete Information - Unable to process",
                 "comment": "The information provided was not sufficient to resolve the incident or complete the request. Additional information could not be obtained",
                 "model": "Interaction"},
                {"resolution": "Infrastructure Error", "comment": "Network or Server error that impacted service",
                 "model": "Interaction"},
                {"resolution": "Platform Error", "comment": "Error caused from Platform bug or misconfiguration",
                 "model": "Interaction"},
                {"resolution": "Outage", "comment": "The issue was caused due to an outage of a service or application",
                 "model": "Interaction"},
                {"resolution": "Password / Permissions / Authentication",
                 "comment": "Issue related to user’s password or access permissions", "model": "Interaction"},
                {"resolution": "Incorrectly categorised", "comment": "Wrong categorisation. New ticket required",
                 "model": "Interaction"},
                {"resolution": "Self-Healed", "comment": "Could not detect an issue. The trouble cleared on its own",
                 "model": "Interaction"},
                {"resolution": "Software Error",
                 "comment": "Bug fix implemented or software error was cleared or software was re-installed",
                 "model": "Interaction"},
                {"resolution": "Training or Information Provided",
                 "comment": "The customer was given training or information on a topic", "model": "Interaction"},
                {"resolution": "WFH / Remote IT Issues",
                 "comment": "The issue was located within the customer’s remote environment", "model": "Interaction"},
                {"resolution": "Withdrawn/Resolved by Caller", "comment": "The incident was cancelled by the customer",
                 "model": "Interaction"},
                {"resolution": "Configuration Error",
                 "comment": "An incorrect configuration or setting change was made", "model": "Interaction"},
                {"resolution": "Workaround Developed", "comment": "Root Cause not found but a Workaround is in place",
                 "model": "Problem"},
                {"resolution": "Not viable", "comment": "The cost to resolve cannot be justified", "model": "Problem"},
                {"resolution": "Known Error - Root Cause Identified",
                 "comment": "The root cause of the Problem was identified", "model": "Problem"},
                {"resolution": "Denied at CAB", "comment": "The Change was denied by CAB", "model": "Change"},
                {"resolution": "Rolled Back due to failed Change", "comment": "The Change failed", "model": "Change"},
                {"resolution": "Release/Deploy Successful", "comment": "The Release and Deployment was successful",
                 "model": "Release"},
                {"resolution": "Release/Deploy Unsuccessful",
                 "comment": "The Release and/or Deployment was not successfully completed", "model": "Release"}
            ],
            "unique_fields": ["resolution"]
        },
        RiskLookup: {
            "data": [
                {"risk": "CR1", "comment": "High risk"},
                {"risk": "CR3", "comment": "Medium risk"},
                {"risk": "CR2", "comment": "Medium-High risk"},
                {"risk": "CR4", "comment": "Medium-Low risk"},
                {"risk": "CR5", "comment": "Low risk"}
            ],
            "unique_fields": ["risk"]
        },
        Role: {
            "data": [
                {"name": "admin", "description": "Admin users"},
                {"name": "team member", "description": "Normal end users"},
                {"name": "manager", "description": "Advanced skills users!!"},
                {"name": "approver", "description": "Change approver"},
                {"name": "CAB member", "description": "Change Approval Board member"},
                {"name": "Tester", "description": "Change Tester"},
                {"name": "Product Owner", "description": "Responsible for Product Delivery"},
                {"name": "Release/Deploy", "description": "Release/Deploy agents"}
            ],
            "unique_fields": ["name"]
        },
        Source: {
            "data": [
                {"source": "Web Form"},
                {"source": "Walk up"},
                {"source": "Floorwalker"},
                {"source": "Chat"},
                {"source": "Phone"},
                {"source": "Email"},
                {"source": "Fax"},
                {"source": "System or API"}
            ],
            "unique_fields": ["source"]
        },
        StatusLookup: {
            "data": [
                {"status": "new"},
                {"status": "disposed"},
                {"status": "review"},
                {"status": "published"},
                {"status": "archived"},
                {"status": "implement"},
                {"status": "voting"},
                {"status": "adopting"},
                {"status": "testing"},
                {"status": "in-progress"},
                {"status": "internal"},
                {"status": "retired"},
                {"status": "closed"},
                {"status": "approval"},
                {"status": "operational"},
                {"status": "resolved"},
                {"status": "cab"},
                {"status": "plan"},
                {"status": "build"},
                {"status": "reviewing"},
                {"status": "ideation"},
                {"status": "pdca"}
            ],
            "unique_fields": ["status"]
        },
        SupportTypeLookup: {
            "data": [
                {"support_type": "IT Internal", "comment": "Internal IT Support team"},
                {"support_type": "Business Unit Specialist", "comment": "Internal support within business unit"},
                {"support_type": "Sourced - Vendor", "comment": "The vendor provides support directly"},
                {"support_type": "Sourced - 3rd Party", "comment": "A 3rd party support organisation is contracted"}
            ],
            "unique_fields": ["support_type", "comment"]
        },
        Team: {
            "data": [
                {"name": "Service Desk", "description": "Central Service Desk"},
                {"name": "ITSM", "description": "Central Service Desk"},
                {"name": "Systems Support", "description": "Infrastructure"},
                {"name": "Database Admin", "description": "Database maintenance"},
                {"name": "Application Support", "description": "Business Applications support team"}
            ],
            "unique_fields": ["name", "description"]
        }
    }

    # Seed independent tables first
    for model, config in independent_tables.items():
        seed_lookup_table(model, config["unique_fields"], config["data"])

    # Commit after independent tables
    db.session.commit()
    print("✅ Seeded independent tables")

    # Second pass: Seed tables with foreign key dependencies
    dependent_tables = {
        Subcategory: {
            "data": [
                {"name": "Access Permissions", "category_id": 1, "ticket_type": "Request"},
                {"name": "Account Creation", "category_id": 1, "ticket_type": "Request"},
                {"name": "Account Deactivation", "category_id": 1, "ticket_type": "Request"},
                {"name": "Multi-Factor Authentication (MFA)", "category_id": 1, "ticket_type": "Request"},
                {"name": "Password Reset", "category_id": 1, "ticket_type": "Request"},
                {"name": "Installation/Configuration", "category_id": 2, "ticket_type": "Request"},
                {"name": "Errors/Crashes", "category_id": 2, "ticket_type": "Incident"},
                {"name": "Updates/Patching", "category_id": 2, "ticket_type": "Request"},
                {"name": "License Management", "category_id": 2, "ticket_type": "Request"},
                {"name": "Virtual Machine", "category_id": 3, "ticket_type": "Request"},
                {"name": "Cloud Server Configuration", "category_id": 3, "ticket_type": "Request"},
                {"name": "Cloud Resource Scaling", "category_id": 3, "ticket_type": "Request"},
                {"name": "Cloud Service Issues", "category_id": 3, "ticket_type": "Incident"},
                {"name": "Cloud Security Concerns", "category_id": 3, "ticket_type": "Incident"},
                {"name": "Cloud migration", "category_id": 3, "ticket_type": "Request"},
                {"name": "Platform configuration", "category_id": 3, "ticket_type": "Request"},
                {"name": "Performance issues", "category_id": 3, "ticket_type": "Incident"},
                {"name": "Email delivery issues", "category_id": 4, "ticket_type": "Incident"},
                {"name": "Email Setup/Configuration", "category_id": 4, "ticket_type": "Request"},
                {"name": "VoIP/Telephony Issues", "category_id": 4, "ticket_type": "Incident"},
                {"name": "Messaging Application Issues", "category_id": 4, "ticket_type": "Incident"},
                {"name": "Messaging Issues", "category_id": 4, "ticket_type": "Incident"},
                {"name": "Spam or phishing emails", "category_id": 4, "ticket_type": "Incident"},
                {"name": "Data Backup/Restoration", "category_id": 5, "ticket_type": "Request"},
                {"name": "Data Loss/Recovery", "category_id": 5, "ticket_type": "Incident"},
                {"name": "Data corruption", "category_id": 5, "ticket_type": "Incident"},
                {"name": "Database performance", "category_id": 5, "ticket_type": "Incident"},
                {"name": "Data Storage/Quota Increase", "category_id": 5, "ticket_type": "Request"},
                {"name": "Data Archiving", "category_id": 5, "ticket_type": "Request"},
                {"name": "Laptop/Computer Issues", "category_id": 6, "ticket_type": "Incident"},
                {"name": "Peripheral Device Issues", "category_id": 6, "ticket_type": "Incident"},
                {"name": "Operating System Issues", "category_id": 6, "ticket_type": "Incident"},
                {"name": "User Profile Issues", "category_id": 6, "ticket_type": "Incident"},
                {"name": "Hardware Upgrades/Replacements", "category_id": 6, "ticket_type": "Incident"},
                {"name": "Software installation", "category_id": 6, "ticket_type": "Request"},
                {"name": "General Inquiries", "category_id": 7, "ticket_type": "Request"},
                {"name": "Equipment Requests", "category_id": 7, "ticket_type": "Request"},
                {"name": "Training Needs", "category_id": 7, "ticket_type": "Request"},
                {"name": "Feedback and Suggestions", "category_id": 7, "ticket_type": "Request"},
                {"name": "Internet Connectivity Issues", "category_id": 8, "ticket_type": "Incident"},
                {"name": "Network Configuration", "category_id": 8, "ticket_type": "Request"},
                {"name": "Firewall/Security Settings", "category_id": 8, "ticket_type": "Request"},
                {"name": "Network Performance", "category_id": 8, "ticket_type": "Incident"},
                {"name": "VPN Setup", "category_id": 8, "ticket_type": "Request"},
                {"name": "VPN Issues", "category_id": 8, "ticket_type": "Incident"},
                {"name": "Malware/Virus Detection and Removal", "category_id": 9, "ticket_type": "Incident"},
                {"name": "Data Breach/Security Incident", "category_id": 9, "ticket_type": "Incident"},
                {"name": "Security Software Configuration", "category_id": 9, "ticket_type": "Request"},
                {"name": "Security Policy Violations", "category_id": 9, "ticket_type": "Incident"},
                {"name": "Unauthorized access attempts", "category_id": 9, "ticket_type": "Incident"},
                {"name": "Server Maintenance/Configuration", "category_id": 10, "ticket_type": "Request"},
                {"name": "Virtual Machine Provisioning", "category_id": 10, "ticket_type": "Incident"},
                {"name": "Server Outages", "category_id": 10, "ticket_type": "Incident"},
                {"name": "Server Security", "category_id": 10, "ticket_type": "Incident"},
                {"name": "Virtualization Issues", "category_id": 10, "ticket_type": "Incident"},
                {"name": "Server or VM crashes", "category_id": 10, "ticket_type": "Incident"},
                {"name": "Supply new phone", "category_id": 16, "ticket_type": "Request"},
                {"name": "Calls failing", "category_id": 16, "ticket_type": "Incident"}
            ],
            "unique_fields": ["name", "category_id"]
        },
        User: {
            "data": [
                {"username": "admin", "email_address:": "admin@yourorg.com", "password": "password", "roles": [
                    "admin", "team member", "manager", "approver", "CAB Member", "Tester", "Product Owner",
                    "Release/Deploy"]},
            ],
            "unique_fields": ["username"]
        }
    }

    # Final commit
    db.session.commit()
    print("✅ Seeded dependent tables")


if __name__ == '__main__':
    app = create_app('production')
    with app.app_context():
        seed_data()
