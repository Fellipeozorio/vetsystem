from django.contrib import admin


class VetSystemAdminSite(admin.AdminSite):
    site_header = "VetSystem - Administração"
    site_title = "VetSystem"
    index_title = "Painel Administrativo"


admin_site = VetSystemAdminSite(name="vetsystem_admin")
