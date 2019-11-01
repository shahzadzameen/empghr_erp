from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.data_migration.doctype.data_migration_connector.connectors.base import BaseConnection
import mysql.connector as mariadb


class EmployeePenaltyConnection(BaseConnection):
    def __init__(self, connector):
        self.connector = connector

        try:
            password = self.get_password()
        except frappe.AuthenticationError:
            password = None

        try:
            self.connection = mariadb.connect(
                host=self.connector.hostname,
                user=self.connector.username,
                password=password,
                database=self.connector.database_name
            )

        except mariadb.Error as error:
            print("Error: {}".format(error))
            frappe.throw(("Error: {}".format(error)))

        self.name_field = 'id'

    def insert(self, doctype, doc):
        pass

    def update(self, doctype, doc, migration_id):
        pass

    def delete(self, doctype, migration_id):
        pass

    def get(self, remote_objectname, fields=None, filters=None, start=0, page_length=10):
        self.create_penalties()
        rule_id_mappings = self.get_rule_id_mappings()
        if len(rule_id_mappings) == 0:
            frappe.throw("Failed to find policy rules")
        query = ("""
                SELECT 
                    eap.id,
                    u.employeeId AS employee,
                    eap.year,
                    eap.month,
                    eap.value,
                    eap.instance,
                    eap.penalty,
                    eap.policy_rule_id as attendance_policy_rules,
                    eap.type,
                    eap.comments
                FROM
                    main_empattendance_penalties eap
                INNER JOIN
                    main_users u ON u.id = eap.user_id;""")
        cursor = self.connection.cursor(dictionary=True)

        cursor.execute(query)
        records = []
        for data in cursor:
            data["employee"] = data['employee'].replace('EMPG', '')
            data["attendance_policy_rules"] = rule_id_mappings[data["attendance_policy_rules"]]
            records.append(data)
        cursor.close()
        return list(records)


    def __del__(self):
        self.connection.close()

    def create_penalties(self):
        query = ("""
                SELECT 
                    policy_name, policy_type, is_default
                FROM
                    main_attendance_policies;""")
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)

        _ap_dt = "Attendance Policy"

        for data in cursor:
            if frappe.db.exists(_ap_dt, data['policy_name']) is None:
                _args = data
                _args["doctype"] = _ap_dt
                _ap = frappe.get_doc(_args)
                _ap.insert()
        cursor.close()
        self.create_penalty_rules()

    def create_penalty_rules(self):
        query = ("""SELECT 
                    ap.policy_name AS attendance_policy,
                    apr.policy_unit,
                    apr.unit_value_to,
                    apr.unit_value_from,
                    apr.policy_multiplier,
                    apr.penalty_unit,
                    apr.comments
                FROM
                    main_attendance_policy_rules apr
                        INNER JOIN
                    main_attendance_policies ap ON ap.id = apr.policy_id;""")
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)
        _apr_dt = "Attendance Policy Rules"
        for data in cursor:
            _filters = data
            del(_filters["comments"])
            if frappe.db.exists(_apr_dt, _filters) is None:
                _args = data
                _args["doctype"] = _apr_dt
                _apr = frappe.get_doc(_args)
                _apr.insert()
        cursor.close()
        self.create_attendance_policy_association()

    def create_attendance_policy_association(self):
        query = ("""
                SELECT 
                    ap.policy_name AS attendance_policy,
                    CASE
                        WHEN apa.object_type = 'businessunit' THEN bu.unitname
                        WHEN apa.object_type = 'department' THEN dpt.deptname
                        WHEN apa.object_type = 'jobtitle' THEN jbt.jobtitlename
                        WHEN apa.object_type = 'position' THEN pos.positionname
                        WHEN apa.object_type = 'employee' THEN u.employeeId
                    END as object_id,
                    CASE
                        WHEN apa.object_type = 'businessunit' THEN 'Department'
                        WHEN apa.object_type = 'department' THEN 'Department'
                        WHEN apa.object_type = 'jobtitle' THEN 'Job Title'
                        WHEN apa.object_type = 'position' THEN 'Job Title'
                        WHEN apa.object_type = 'employee' THEN 'Employee'
                    END as object_type
                FROM main_attendance_policy_association apa
                INNER JOIN
                    main_attendance_policies ap ON ap.id = apa.policy_id
                LEFT JOIN
                    main_departments dpt ON dpt.id = apa.object_id
                LEFT JOIN
                    main_businessunits bu ON bu.id = apa.object_id
                LEFT JOIN
                    main_jobtitles jbt ON jbt.id = apa.object_id
                LEFT JOIN
                    main_positions pos ON pos.id = apa.object_id
                LEFT JOIN
                    main_users u ON u.id = apa.object_id;""")
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)

        _apa_dt = "Attendance Policy Associations"
        for data in cursor:
            if frappe.db.exists(_apa_dt, data) is None:
                _args = data
                _args["doctype"] = _apa_dt
                _apa = frappe.get_doc(_args)
                _apa.insert()
        cursor.close()

    def get_rule_id_mappings(self):
        query = ("""
                SELECT 
                    apr.id as id,
                    ap.policy_name AS attendance_policy,
                    apr.policy_unit,
                    apr.unit_value_to,
                    apr.unit_value_from,
                    apr.policy_multiplier,
                    apr.penalty_unit
                FROM
                    main_attendance_policy_rules apr
                        INNER JOIN
                    main_attendance_policies ap ON ap.id = apr.policy_id;""")
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query)

        _apr_dt = "Attendance Policy Rules"
        rule_id_mappings = {}
        for data in cursor:
            rule_id = data["id"]
            _filters = data
            del(_filters["id"])
            if frappe.db.exists(_apr_dt, _filters) is not None:
                rule_id_mappings[rule_id] = frappe.db.exists(_apr_dt, _filters)
        cursor.close()
        return rule_id_mappings