import frappe


def remove_departments_spaces():
    departments = frappe.get_all('Department', {}, ['name', 'parent_department'])
    for d in departments:
        if d.name.endswith(' '):
            frappe.rename_doc('Department', d.name, d.name.strip(), 0, 0)
        if d.parent_department.endswith(' '):
            if frappe.db.exists('Department', {"parent_department": d.parent_department}):
                parent_dept = frappe.get_all('Department', {"parent_department": d.parent_department}, ['parent_department'])
                for parent_dep in parent_dept:
                    parent_dep.parent_department = d.parent_department.strip()
                    parent_dep.save()
