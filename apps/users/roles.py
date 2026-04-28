from rolepermissions.roles import AbstractUserRole


class Admin(AbstractUserRole):
    available_permissions = {
        'manage_users': True,
        'manage_jobs': True,
        'approve_jobs': True,
        'view_reports': True,
    }


class Employer(AbstractUserRole):
    available_permissions = {
        'post_job': True,
        'edit_own_job': True,
        'delete_own_job': True,
        'view_applicants': True,
        'download_cv': True,
    }


class JobSeeker(AbstractUserRole):
    available_permissions = {
        'apply_job': True,
        'save_job': True,
        'upload_cv': True,
        'view_application_status': True,
    }
