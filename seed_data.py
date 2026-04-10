import os
os.environ['DATABASE_URL'] = 'sqlite:///instance/app.db'
os.environ.setdefault('SECRET_KEY', 'dev-seed-key')

from app import create_app
from app.extensions import db
from app.models.service import Service
from app.models.part import Part

app = create_app()

with app.app_context():
    services = [
        Service(service_name="Olajcsere", cost=8000, tenant_id=1),
        Service(service_name="Fekbetet csere", cost=15000, tenant_id=1),
        Service(service_name="Gumiszereles", cost=2500, tenant_id=1),
        Service(service_name="Diagnosztika", cost=5000, tenant_id=1),
        Service(service_name="Legkond toltes", cost=12000, tenant_id=1),
        Service(service_name="Vezerlosziij csere", cost=35000, tenant_id=1),
        Service(service_name="Fekfolyadek csere", cost=6000, tenant_id=1),
        Service(service_name="Gyujtogyertya csere", cost=8500, tenant_id=1),
        Service(service_name="Akkumulator csere", cost=5000, tenant_id=1),
        Service(service_name="Futomuu beallitas", cost=10000, tenant_id=1),
    ]
    parts = [
        Part(part_name="Motorolaj 5W-30 5L", cost=4500, tenant_id=1),
        Part(part_name="Olajszuro", cost=1200, tenant_id=1),
        Part(part_name="Levegoszuro", cost=2800, tenant_id=1),
        Part(part_name="Fekbetet keszlet elso", cost=8500, tenant_id=1),
        Part(part_name="Fekbetet keszlet hatso", cost=7200, tenant_id=1),
        Part(part_name="Gyujtogyertya db", cost=1800, tenant_id=1),
        Part(part_name="Uzemanyagszuro", cost=3200, tenant_id=1),
        Part(part_name="Vezerlosziij keszlet", cost=18000, tenant_id=1),
        Part(part_name="Hutofol 1L", cost=1500, tenant_id=1),
        Part(part_name="Fekfolyadek DOT4 500ml", cost=1800, tenant_id=1),
    ]
    for s in services:
        db.session.add(s)
    for p in parts:
        db.session.add(p)
    db.session.commit()
    print("Kesz! {} szolgaltatas es {} alkatresz feltoltve!".format(len(services), len(parts)))
