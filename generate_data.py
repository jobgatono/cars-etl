"""Generates the synthetic raw CSV data (seeded, reproducible) into data/raw/."""
import random, csv, datetime as dt, os
random.seed(42)
from pathlib import Path
OUT = Path(__file__).parent  # CSVs are written next to this script
OUT.mkdir(parents=True, exist_ok=True)
TODAY = dt.date(2026, 11, 4)
USD_KES = lambda d: round(random.uniform(127, 130) if d.year >= 2024 else random.uniform(135, 155), 2)

# ---------- car_models ----------
models = [
 # make, model, body, fuel, cc, trans, origin, base FOB usd
 ("Toyota","Land Cruiser Prado","SUV","Diesel",2800,"Automatic","Japan",21000),
 ("Toyota","Harrier","SUV","Petrol",2000,"Automatic","Japan",11500),
 ("Toyota","Axio","Sedan","Petrol",1500,"Automatic","Japan",5200),
 ("Toyota","Fielder","Station Wagon","Petrol",1500,"Automatic","Japan",5000),
 ("Toyota","Hilux Double Cab","Pickup","Diesel",2400,"Manual","Japan",14500),
 ("Toyota","Vitz","Hatchback","Petrol",1000,"Automatic","Japan",3300),
 ("Toyota","Passo","Hatchback","Petrol",1000,"Automatic","Japan",3100),
 ("Toyota","Noah","Minivan","Petrol",2000,"Automatic","Japan",7800),
 ("Nissan","X-Trail","SUV","Petrol",2000,"Automatic","Japan",7600),
 ("Nissan","Note","Hatchback","Petrol",1200,"Automatic","Japan",3900),
 ("Nissan","Juke","SUV","Petrol",1500,"Automatic","Japan",5600),
 ("Subaru","Forester","SUV","Petrol",2000,"Automatic","Japan",8200),
 ("Subaru","Impreza","Sedan","Petrol",1600,"Automatic","Japan",5800),
 ("Mazda","CX-5","SUV","Diesel",2200,"Automatic","Japan",12800),
 ("Mazda","Demio","Hatchback","Petrol",1300,"Automatic","Japan",3600),
 ("Honda","Fit","Hatchback","Hybrid",1300,"Automatic","Japan",4300),
 ("Honda","Vezel","SUV","Hybrid",1500,"Automatic","Japan",8900),
 ("Mitsubishi","Outlander","SUV","Petrol",2400,"Automatic","Japan",8400),
 ("Suzuki","Swift","Hatchback","Petrol",1200,"Automatic","Japan",4100),
 ("Land Rover","Range Rover Sport","SUV","Diesel",3000,"Automatic","United Kingdom",34000),
 ("Land Rover","Discovery 4","SUV","Diesel",3000,"Automatic","United Kingdom",19500),
 ("Mercedes-Benz","C200","Sedan","Petrol",1500,"Automatic","United Kingdom",14800),
 ("BMW","X5","SUV","Diesel",3000,"Automatic","United Kingdom",24500),
 ("Volkswagen","Golf","Hatchback","Petrol",1400,"Manual","United Kingdom",7900),
 ("Toyota","Land Cruiser V8","SUV","Diesel",4500,"Automatic","United Arab Emirates",42000),
 ("Lexus","RX 350","SUV","Petrol",3500,"Automatic","United Arab Emirates",26000),
 ("Nissan","Patrol","SUV","Petrol",4000,"Automatic","United Arab Emirates",29000),
 ("Isuzu","D-Max","Pickup","Diesel",3000,"Manual","Thailand",15500),
 ("Toyota","Fortuner","SUV","Diesel",2800,"Automatic","Thailand",23500),
 ("Ford","Ranger","Pickup","Diesel",3200,"Automatic","South Africa",24500),
]
mrows=[]
for i,m in enumerate(models,1):
    mrows.append([f"M{i:03d}",*m[:7],m[7]])
def w(name, header, rows):
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        cw = csv.writer(f); cw.writerow(header); cw.writerows(rows)
    print(name, len(rows))
w("car_models.csv",["model_id","make","model","body_type","fuel_type","engine_cc","transmission","origin_country","base_fob_price_usd"],mrows)

# ---------- suppliers ----------
sup = [
 ("USS Auction Tokyo","Japan","Auction",4.6,"Prepaid"),("HAA Kobe Auction","Japan","Auction",4.4,"Prepaid"),
 ("JU Nagoya","Japan","Auction",4.3,"Prepaid"),("Be Forward Exports","Japan","Exporter",4.1,"LC 30 days"),
 ("SBT Japan","Japan","Exporter",4.2,"Prepaid"),("Autorec Japan","Japan","Exporter",3.9,"Prepaid"),
 ("Manchester Prestige Cars","United Kingdom","Dealer",4.5,"Bank Transfer"),("Hartwell Motor Exports","United Kingdom","Exporter",4.0,"Bank Transfer"),
 ("Dubizzle Motors FZE","United Arab Emirates","Exporter",3.8,"LC 30 days"),("Al Futtaim Pre-Owned","United Arab Emirates","Dealer",4.4,"Bank Transfer"),
 ("Siam Auto Trading","Thailand","Exporter",4.0,"Prepaid"),("Cape Motor Group","South Africa","Dealer",4.1,"Bank Transfer"),
]
w("suppliers.csv",["supplier_id","supplier_name","country","supplier_type","rating","payment_terms"],
  [[f"S{i:03d}",*s] for i,s in enumerate(sup,1)])
sup_by_country={}
for i,s in enumerate(sup,1): sup_by_country.setdefault(s[1],[]).append(f"S{i:03d}")

# ---------- customers ----------
fn_m=["James","John","Peter","Samuel","David","Brian","Kevin","Daniel","Joseph","Collins","Dennis","Michael","Patrick","Felix","Victor","Moses","George","Eric","Hassan","Abdi","Omar","Otieno","Kiprop"]
fn_f=["Mary","Grace","Faith","Jane","Esther","Lucy","Mercy","Nancy","Joyce","Purity","Caroline","Wanjiru","Akinyi","Amina","Halima","Sharon","Winnie"]
ln=["Kamau","Mwangi","Otieno","Odhiambo","Njoroge","Wanyama","Kiptoo","Cheruiyot","Mutua","Muthoni","Omondi","Ochieng","Karanja","Maina","Ndungu","Hussein","Ali","Mohamed","Kariuki","Waweru","Barasa","Wafula","Kilonzo","Langat","Rotich"]
counties=[("Nairobi",30),("Kiambu",10),("Mombasa",9),("Nakuru",7),("Kisumu",5),("Uasin Gishu",5),("Machakos",4),("Kajiado",4),("Nyeri",3),("Meru",3),("Kisii",2),("Kakamega",2),("Nyandarua",2),("Kilifi",2),("Laikipia",2)]
corp=["Savannah Logistics Ltd","Kilimani Contractors","Rift Valley Tours & Safaris","Mt Kenya Agrovet","Lakeview Hospitality","Tembo Construction Co","Pwani Freight Services","Highland Dairy Co-op","Nairobi Medical Supplies","Jua Kali Enterprises","Eastlands Transporters","County Government of Kajiado","State Dept of Roads"]
cust=[]
for i in range(1,1201):
    r=random.random()
    if r<0.07:
        name=random.choice(corp); ctype="Corporate" if "County" not in name and "State" not in name else "Government"
    else:
        name=f"{random.choice(fn_m if random.random()<0.6 else fn_f)} {random.choice(ln)}"; ctype="Individual"
    county=random.choices([c for c,_ in counties],[wt for _,wt in counties])[0]
    email=name.lower().replace(" ","."). replace("&","and").replace(",","")[:24]+str(random.randint(1,99))+"@"+random.choice(["gmail.com","yahoo.com","outlook.com","gmail.com","company.co.ke"])
    phone=random.choice(["07","01"])+str(random.randint(10000000,99999999))
    reg=dt.date(2022,6,1)+dt.timedelta(days=random.randint(0,1280))
    cust.append([f"C{i:05d}",name,email,phone,county,ctype,reg.isoformat()])
# dirty: whitespace/case/missing
for c in random.sample(cust,40): c[1]=c[1].upper()
for c in random.sample(cust,35): c[2]=""
for c in random.sample(cust,25): c[3]="+254"+c[3][1:]
for c in random.sample(cust,20): c[4]=c[4].lower()+" "
for c in random.sample(cust,15): c[6]=dt.date.fromisoformat(c[6]).strftime("%d/%m/%Y")
cust += [random.choice(cust)[:] for _ in range(12)]  # duplicate rows
w("customers.csv",["customer_id","full_name","email","phone","county","customer_type","registration_date"],cust)
cust_ids=[c[0] for c in cust[:1200]]
cust_w=[random.random()**3+0.05 for _ in cust_ids]  # repeat buyers

# ---------- routes ----------
routes={"Japan":[("Yokohama",(26,38)),("Osaka",(28,40)),("Nagoya",(27,39))],
 "United Kingdom":[("Southampton",(30,45))],
 "United Arab Emirates":[("Jebel Ali",(14,24))],
 "Thailand":[("Laem Chabang",(24,34))],
 "South Africa":[("Durban",(10,18))]}
vessels={"Japan":["Morning Cosmos","Ocean Aurora","Sakura Highway","Glovis Courage","Hoegh Trapper"],
 "United Kingdom":["Grande Francia","MV Atlantic Express","Torm Mathilde"],
 "United Arab Emirates":["Al Mirqab","Gulf Navigator","Emirates Star"],
 "Thailand":["Siam Carrier","Pacific Dragon","Bangkok Express"],
 "South Africa":["Cape Harmony","Natal Spirit"]}
delays=["Port congestion","Bad weather","Vessel rescheduled","Customs inspection","Documentation error","KRA system downtime","Transshipment delay","Strike action",None]
colors=["White","Pearl White","Black","Silver","Grey","Blue","Red","Dark Green","Beige","Gold"]
pay=["M-Pesa Paybill","Bank Transfer","Bank Transfer","Cash Deposit","Asset Finance","Cheque"]
reps=["Alice Wambui","Brian Kimani","Cynthia Atieno","Dan Mutiso","Evelyn Chebet"]
fmt=lambda d,f:d.strftime(f)

orders=[];ships=[];reviews=[]
N=3200
start=dt.date(2023,1,2); span=(TODAY-start).days
rid=0
for oi in range(1,N+1):
    od=start+dt.timedelta(days=int(span*random.random()**0.85))
    m=random.choices(mrows,[1/(1+ (r[8]/9000)**1.3) for r in mrows])[0]
    mid,make,model,body,fuel,cc,trans,origin,base=m
    sid=random.choice(sup_by_country[origin]); cid=random.choices(cust_ids,cust_w)[0]
    year=random.randint(2012,2022) if origin!="Thailand" else random.randint(2019,2024)
    price=round(base*random.uniform(0.8,1.25)*(1-0.03*(2022-year)),0)
    mileage=random.randint(15000,140000) if year<2023 else random.randint(0,60000)
    freight={"Japan":random.randint(1100,1600),"United Kingdom":random.randint(1500,2200),"United Arab Emirates":random.randint(800,1300),"Thailand":random.randint(1100,1500),"South Africa":random.randint(900,1400)}[origin]
    ins=round(price*0.015)
    rate=USD_KES(od)
    cif=(price+freight+ins)*rate
    duty=round(cif*0.25); excise=round((cif+duty)*(0.25 if cc<=3000 and fuel!="Hybrid" else 0.20)*0.0+ (cif+duty)*0.2*(1 if cc>2500 else 0.0)) 
    vat=round((cif+duty+excise)*0.16); idf=round(cif*0.035); rdl=round(cif*0.02)
    landed=cif+duty+excise+vat+idf+rdl
    margin=random.uniform(0.07,0.18)
    total=round(landed*(1+margin),-2)
    # status
    port,(dmin,dmax)=random.choice(routes[origin])
    dep=od+dt.timedelta(days=random.randint(10,28))
    transit=random.randint(dmin,dmax)
    delay=None
    if random.random()<0.28:
        delay=random.choice([d for d in delays if d]); transit+=random.randint(3,16)
    arr=dep+dt.timedelta(days=transit)
    clr=arr+dt.timedelta(days=random.randint(3,14)+(random.randint(5,12) if delay in("Customs inspection","KRA system downtime","Documentation error") else 0))
    dlv=clr+dt.timedelta(days=random.randint(2,6))
    r=random.random()
    if r<0.04: status="Cancelled"
    elif dlv<=TODAY: status="Delivered"
    elif clr<=TODAY: status="Cleared"
    elif arr<=TODAY: status="At Port - Mombasa"
    elif dep<=TODAY: status="In Transit"
    else: status="Pending Shipment"
    if status=="Cancelled": pass
    orders.append([f"ORD{oi:05d}",cid,mid,sid,od.isoformat(),year,mileage,random.choice(colors),price,freight,ins,rate,duty,excise,vat,total,random.choice(pay),status,random.choice(reps)])
    if status!="Cancelled":
        ships.append([f"SHP{oi:05d}",f"ORD{oi:05d}",random.choice(vessels[origin]),port,"Mombasa",dep.isoformat(),
            arr.isoformat() if arr<=TODAY else "", clr.isoformat() if clr<=TODAY else "", dlv.isoformat() if dlv<=TODAY else "",
            random.choices(["RoRo","Container 40ft"],[85,15])[0] if body!="Pickup" else "RoRo", delay or "", f"BL{random.randint(10**8,10**9-1)}"])
    # reviews
    if status=="Delivered" and random.random()<0.55:
        late=(dlv-od).days
        base_r=random.choices([5,4,3,2,1],[40,30,15,9,6])[0]
        if delay: base_r=max(1,base_r-random.choice([0,1,1,2]))
        pos=["Car arrived in great condition, exactly as described.","Smooth process from order to delivery.","Very happy with the {mk} {md}, runs perfectly.","Good communication throughout the shipping.","Fair price compared to other importers.","Mileage matched the auction sheet. Honest dealer."]
        neu=["Car is okay but delivery took longer than quoted.","Decent car, paperwork took a while at KRA.","Fine overall, would have liked more updates.","Price was fair but a few scratches not mentioned."]
        neg=["Shipping delayed by weeks, no updates from the sales team.","Mileage seems higher than on the auction sheet.","Had to pay extra at port, was not told upfront.","AC faulty on delivery, still waiting for a fix.","Waited too long for registration, very frustrating."]
        txt=random.choice(pos if base_r>=4 else neu if base_r==3 else neg).format(mk=make,md=model)
        if delay and base_r<=3 and random.random()<0.5: txt+=f" Cause given: {delay.lower()}."
        if random.random()<0.08: txt=txt+" "+random.choice(["Asante sana!","Poa kabisa.","Ni gari safi sana.","Sio mbaya."])
        rd=dlv+dt.timedelta(days=random.randint(1,45))
        if rd>TODAY: rd=TODAY
        rid+=1
        rv=[f"REV{rid:05d}",f"ORD{oi:05d}",cid,rd.isoformat(),base_r,txt,random.choices(["Website","Google","Facebook","WhatsApp","Email Survey"],[30,25,15,15,15])[0]]
        reviews.append(rv)

# dirty data injections
for o in random.sample(orders,60): o[4]=dt.date.fromisoformat(o[4]).strftime("%d/%m/%Y")
for o in random.sample(orders,45): o[17]=o[17].upper()
for o in random.sample(orders,40): o[6]=""
for o in random.sample(orders,30): o[7]=o[7].lower()
for o in random.sample(orders,25): o[15]=f"KES {o[15]:,.0f}"
for o in random.sample(orders,20): o[16]=""
orders += [random.choice(orders)[:] for _ in range(25)]
for s in random.sample(ships,50): s[10]=s[10].lower()
for s in random.sample(ships,30): s[5]=dt.date.fromisoformat(s[5]).strftime("%m-%d-%Y")
ships += [random.choice(ships)[:] for _ in range(15)]
for r in random.sample(reviews,40): r[4]=f"{r[4]}/5"
for r in random.sample(reviews,25): r[5]=""
for r in random.sample(reviews,15): r[5]="  "+r[5]+"  "
reviews += [random.choice(reviews)[:] for _ in range(10)]
random.shuffle(orders)

w("orders.csv",["order_id","customer_id","model_id","supplier_id","order_date","manufacture_year","mileage_km","color","fob_price_usd","freight_usd","insurance_usd","usd_kes_rate","import_duty_kes","excise_duty_kes","vat_kes","total_price_kes","payment_method","order_status","salesperson"],orders)
w("shipments.csv",["shipment_id","order_id","vessel_name","origin_port","destination_port","departure_date","arrival_date","customs_clearance_date","delivery_date","shipping_method","delay_reason","bill_of_lading_no"],ships)
w("customer_reviews.csv",["review_id","order_id","customer_id","review_date","rating","review_text","source"],reviews)
