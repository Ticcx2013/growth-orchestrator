"""Synthetic data: accounts and contacts in the states the scenario describes.

Nothing here is real. Names, domains and people are invented.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .db import Database, iso, utcnow
from .integrations.crm import MockCRM

ACCOUNTS = [
    # id, name, domain, country, segment, employees, is_customer, has_open_opp, owner_ae, csm
    ("acc_andino", "Grupo Andino Logística", "grupoandino.mx", "MX", "mid-market", 320, 0, 0, "ae_sofia", None),
    ("acc_verde", "Verde Foods S.A.", "verdefoods.com.br", "BR", "mid-market", 540, 0, 0, "ae_rafael", None),
    ("acc_cafeto", "Cafeto Tech", "cafeto.co", "CO", "smb", 40, 0, 0, None, None),               # out of ICP (size)
    ("acc_norte", "Constructora del Norte", "cnorte.mx", "MX", "enterprise", 1800, 1, 0, None, "csm_lucia"),  # existing customer
    ("acc_pampa", "Pampa Retail", "pamparetail.com.ar", "AR", "mid-market", 600, 0, 0, None, None),  # out of ICP (country)
    ("acc_marea", "Marea Seguros", "marea.mx", "MX", "mid-market", 410, 0, 1, "ae_diego", None),  # active opportunity with an AE
    ("acc_sol", "Sol Energía", "solenergia.co", "CO", "mid-market", 220, 0, 0, "ae_camila", None),
    ("acc_bruma", "Bruma Farmacéutica", "bruma.com.br", "BR", "enterprise", 2300, 0, 0, "ae_rafael", None),
    ("acc_lima", "Lima & Asociados", "limaasociados.mx", "MX", "smb", 75, 0, 0, "ae_sofia", None),
    ("acc_delta", "Delta Manufactura", "deltamfg.mx", "MX", "mid-market", 380, 0, 0, "ae_sofia", "csm_lucia"),  # will become a customer mid-demo
]

CONTACTS = [
    # id, account_id, email, name, title, status, sequence_status, last_outreach_days_ago, enriched
    ("c_lucia", "acc_andino", "lucia.fernandez@grupoandino.mx", "Lucía Fernández", "CFO", "active", "enrolled", 3, 1),
    ("c_pedro", "acc_andino", "pedro.ruiz@grupoandino.mx", "Pedro Ruiz", "Controller", "active", "none", None, 0),
    ("c_ana", "acc_verde", "ana.souza@verdefoods.com.br", "Ana Souza", "Diretora Financeira", "active", "enrolled", 5, 1),
    ("c_joao", "acc_verde", "joao.lima@verdefoods.com.br", "João Lima", "Gerente de Contas a Pagar", "active", "enrolled", 6, 1),
    ("c_mateo", "acc_cafeto", "mateo@cafeto.co", "Mateo Gómez", "Founder", "active", "enrolled", 2, 1),
    ("c_rosa", "acc_norte", "rosa.perez@cnorte.mx", "Rosa Pérez", "Tesorería", "active", "enrolled", 20, 1),
    ("c_martin", "acc_pampa", "martin@pamparetail.com.ar", "Martín Pereyra", "CFO", "active", "none", None, 1),
    ("c_valeria", "acc_marea", "valeria@marea.mx", "Valeria Ortiz", "Directora de Finanzas", "active", "enrolled", 4, 1),
    ("c_camilo", "acc_sol", "camilo.rojas@solenergia.co", "Camilo Rojas", "Gerente Financiero", "active", "enrolled", 7, 1),
    ("c_fernanda", "acc_bruma", "fernanda.costa@bruma.com.br", "Fernanda Costa", "CFO", "active", "enrolled", 1, 1),
    ("c_hugo", "acc_lima", "hugo@limaasociados.mx", "Hugo Lima", "Socio", "active", "enrolled", 9, 1),
    ("c_sara", "acc_delta", "sara.mendez@deltamfg.mx", "Sara Méndez", "CFO", "active", "enrolled", 2, 1),
    ("c_recent", "acc_sol", "andrea@solenergia.co", "Andrea Vélez", "Contadora", "active", "none", 3, 1),  # inside cooldown
    ("c_optout", "acc_bruma", "marcos@bruma.com.br", "Marcos Silva", "Compras", "suppressed", "completed", 40, 1),
]

SUPPRESSIONS = [
    ("domain", "gov.mx", "public sector excluded by policy"),
    ("contact_email", "marcos@bruma.com.br", "opted out 2026-08-15"),
]


def seed(db: Database, crm: MockCRM | None = None, now: datetime | None = None) -> None:
    now = now or utcnow()
    db.reset()
    if crm is not None:
        crm.reset()
    with db.tx():
        for (aid, name, domain, country, segment, emp, cust, opp, ae, csm) in ACCOUNTS:
            db.exec(
                "INSERT INTO accounts(id,name,domain,country,segment,employee_count,is_customer,has_open_opportunity,owner_ae_id,csm_id,state_version,state_updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,1,?)",
                (aid, name, domain, country, segment, emp, cust, opp, ae, csm, iso(now - timedelta(days=30))),
            )
        for (cid, aid, email, name, title, status, seq, days_ago, enriched) in CONTACTS:
            last = iso(now - timedelta(days=days_ago)) if days_ago is not None else None
            db.exec(
                "INSERT INTO contacts(id,account_id,email,name,title,status,sequence_status,last_outreach_at,wait_until,enriched,updated_at)"
                " VALUES (?,?,?,?,?,?,?,?,NULL,?,?)",
                (cid, aid, email, name, title, status, seq, last, enriched, iso(now)),
            )
        for scope, key, reason in SUPPRESSIONS:
            db.exec("INSERT OR IGNORE INTO suppressions(scope,key,reason,created_at) VALUES (?,?,?,?)", (scope, key, reason, iso(now)))
    if crm is not None:
        for acc in db.all("SELECT * FROM accounts"):
            crm.sync_account(acc)
