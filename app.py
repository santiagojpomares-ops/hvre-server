import os,json,re,datetime,unicodedata,threading,smtplib,io
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask,request,jsonify
app=Flask(__name__)
ANTHROPIC_API_KEY=os.environ.get("ANTHROPIC_API_KEY","")
EMAIL_FROM=os.environ.get("EMAIL_FROM","santiago@herovalenciarealestate.com")
EMAIL_PASSWORD=os.environ.get("EMAIL_PASSWORD","")
EMAIL_TO=os.environ.get("EMAIL_TO","santiago@herovalenciarealestate.com")
EMAIL_SMTP=os.environ.get("EMAIL_SMTP","smtp.gmail.com")
EMAIL_PORT=int(os.environ.get("EMAIL_PORT","587"))
API_SECRET=os.environ.get("API_SECRET","hvre2025")
def log(m): print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}",flush=True)
def slug(t):
    t=unicodedata.normalize("NFKD",str(t)).encode("ascii","ignore").decode()
    return re.sub(r"\s+","_",re.sub(r"[^\w\s-]","",t).strip())[:50]

def buscar_propiedades(datos):
    import anthropic
    nom=datos.get("nombre","Cliente")
    prov=datos.get("provincia","Alicante")
    ent=datos.get("entorno","Costa")
    bud=datos.get("presupuesto","300k-500k")
    servicio=datos.get("servicio","estandar")
    prompt=f"""Eres un experto inmobiliario senior de Hero Valencia Real Estate.
Cliente: {nom}, busca en {prov}, entorno {ent}, presupuesto {bud}. Servicio: {servicio}.
Busca en TODOS estos portales inmobiliarios rastreando cada uno: Idealista, Fotocasa, Kyero, Yaencontre, ThinkSpain, Rightmove Spain, A Place in the Sun, Habitaclia, Pisos.com, Milanuncios, Spainhouses, Properstar, Resales Online, Green-acres, Viva Estates, Lucas Fox, Knight Frank Spain, y agencias inmobiliarias locales de la zona solicitada.
Encuentra exactamente 15 propiedades reales disponibles ahora mismo, variando los portales para dar la mayor cobertura posible del mercado.
Para cada propiedad necesito datos reales y detallados. Responde SOLO con JSON sin texto adicional:
{{
  "propiedades": [
    {{
      "numero": 1,
      "ref": "REF-001",
      "titulo": "titulo real de la propiedad",
      "ubicacion": "direccion o zona exacta",
      "precio": "precio en euros",
      "m2": "metros cuadrados construidos",
      "dormitorios": "numero de dormitorios",
      "banos": "numero de banos",
      "extras": ["piscina","terraza","parking","barbacoa","jardin","ascensor","aire acondicionado"],
      "distancia_aeropuerto": "nombre del aeropuerto mas cercano y distancia en km",
      "distancia_ave": "estacion AVE mas cercana y distancia en km, o N/A si no hay",
      "distancia_playa": "distancia a pie a la playa si zona costera (ej: 5 min a pie / 300m), si no N/A",
      "portal": "nombre del portal donde esta publicada",
      "link": "url real y completa de la propiedad",
      "analisis": "Analisis experto e independiente de 200 palabras sobre esta propiedad especifica y su zona. Incluye: puntos fuertes de la propiedad, calidad del barrio o zona, servicios cercanos, potencial de revalorizacion, perfil de comprador ideal, y por que representa una oportunidad destacada en el mercado actual. Tono profesional y comercial que atraiga al comprador.",
      "scoring": {{
        "precio_mercado": 8,
        "estado_conservacion": 7,
        "ubicacion_calidad": 9,
        "rentabilidad": 6,
        "extras": 5,
        "potencial_revalorizacion": 8,
        "puntuacion_total": 7.2
      }}
    }}
  ]
}}"""
    client=anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp=client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        tools=[{"type":"web_search_20250305","name":"web_search"}],
        messages=[{"role":"user","content":prompt}]
    )
    texto="".join(b.text for b in resp.content if hasattr(b,"text")).strip()
    m=re.search(r'{[\s\S]*}',texto)
    if not m: raise ValueError("Sin JSON")
    return json.loads(m.group())

def generar_pdf_propiedad(prop, num_total, datos_cliente, es_premium=False):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,HRFlowable,Table,TableStyle
    from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
    buf=io.BytesIO()
    NAVY=colors.HexColor("#16243E")
    GOLD=colors.HexColor("#C9A55A")
    CLAY=colors.HexColor("#B8845A")
    GRAY=colors.HexColor("#5E5A56")
    def S(n,**k): return ParagraphStyle(n,**k)
    s_title=S("Ti",fontName="Helvetica-Bold",fontSize=18,textColor=NAVY,alignment=TA_CENTER,spaceAfter=2)
    s_sub=S("Su",fontName="Helvetica",fontSize=10,textColor=GOLD,alignment=TA_CENTER,spaceAfter=12)
    s_ref=S("Re",fontName="Helvetica",fontSize=8,textColor=GRAY,alignment=TA_CENTER,spaceAfter=10)
    s_sec=S("Se",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY,spaceBefore=12,spaceAfter=5)
    s_body=S("Bo",fontName="Helvetica",fontSize=9,textColor=GRAY,alignment=TA_JUSTIFY,leading=14,spaceAfter=4)
    s_link=S("Lk",fontName="Helvetica",fontSize=8,textColor=CLAY,spaceAfter=4)
    s_ft=S("Ft",fontName="Helvetica",fontSize=7,textColor=GRAY,alignment=TA_CENTER)
    s_prem=S("Pm",fontName="Helvetica-Bold",fontSize=8,textColor=GOLD,spaceAfter=2)
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2*cm,bottomMargin=1.8*cm)
    h=[]
    fecha=datetime.datetime.now().strftime("%d/%m/%Y")
    num=prop.get("numero",1)
    tipo_label="PREMIUM" if es_premium else "ESTANDAR"
    h.append(Paragraph("HERO VALENCIA REAL ESTATE",s_title))
    h.append(Paragraph(f"Ficha de Propiedad {tipo_label} — {num:02d} de {num_total:02d}",s_sub))
    h.append(HRFlowable(width="100%",thickness=1.5,color=GOLD,spaceAfter=8))
    h.append(Paragraph(f"Ref: {prop.get('ref','N/A')} | Cliente: {datos_cliente.get('nombre','')} | Fecha: {fecha}",s_ref))
    h.append(HRFlowable(width="100%",thickness=0.4,color=GOLD,spaceAfter=8))
    h.append(Paragraph("Datos de la Propiedad",s_sec))
    url=prop.get("link","")
    ficha=[
        ["Titulo",prop.get("titulo","")],
        ["Ubicacion",prop.get("ubicacion","")],
        ["PRECIO",prop.get("precio","")],
        ["Superficie",f"{prop.get('m2','')} m2"],
        ["Dormitorios",str(prop.get("dormitorios",""))],
        ["Banos",str(prop.get("banos",""))],
        ["Portal",prop.get("portal","")],
        ["Link",url if url else "N/A"],
    ]
    tf=Table(ficha,colWidths=[4*cm,13*cm])
    tf.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),
        ("TEXTCOLOR",(0,0),(0,-1),NAVY),("TEXTCOLOR",(1,0),(1,-1),GRAY),
        ("BACKGROUND",(0,2),(1,2),colors.HexColor("#16243E")),
        ("TEXTCOLOR",(0,2),(1,2),GOLD),
        ("FONTNAME",(0,2),(1,2),"Helvetica-Bold"),
        ("FONTSIZE",(0,2),(1,2),10),
        ("TEXTCOLOR",(1,7),(1,7),CLAY),
        ("FONTSIZE",(1,7),(1,7),7.5),
        ("BACKGROUND",(0,2),(1,2),colors.HexColor("#16243E")),
        ("TEXTCOLOR",(0,2),(1,2),GOLD),
        ("FONTNAME",(0,2),(1,2),"Helvetica-Bold"),
        ("FONTSIZE",(0,2),(1,2),10),
        ("TEXTCOLOR",(1,7),(1,7),CLAY),
        ("FONTSIZE",(1,7),(1,7),7.5),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f9f6f1"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e8e2d8")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    h.append(tf)
    extras=prop.get("extras",[])
    if extras:
        h.append(Spacer(1,4))
        h.append(Paragraph("Extras y equipamiento",s_sec))
        extras_txt=" · ".join(extras) if isinstance(extras,list) else str(extras)
        h.append(Paragraph(extras_txt,s_body))
    h.append(Paragraph("Distancias y accesos",s_sec))
    dist_data=[
        ["Aeropuerto mas cercano",prop.get("distancia_aeropuerto","N/A")],
        ["Estacion AVE",prop.get("distancia_ave","N/A")],
        ["Playa (a pie)",prop.get("distancia_playa","N/A")],
    ]
    td=Table(dist_data,colWidths=[5.5*cm,11.5*cm])
    td.setStyle(TableStyle([
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.5),
        ("TEXTCOLOR",(0,0),(0,-1),NAVY),("TEXTCOLOR",(1,0),(1,-1),GRAY),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.HexColor("#f9f6f1"),colors.white]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#e8e2d8")),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    h.append(td)
    h.append(Paragraph("Analisis experto Hero Valencia",s_sec))
    h.append(HRFlowable(width="100%",thickness=0.5,color=GOLD,spaceAfter=6))
    h.append(Paragraph(prop.get("analisis",""),s_body))
    # Link incluido en tabla de datos
    h.append(HRFlowable(width="100%",thickness=1,color=NAVY,spaceAfter=6,spaceBefore=14))
    h.append(Paragraph("SCORING INTERNO — CONFIDENCIAL HERO VALENCIA",s_prem))
    sc=prop.get("scoring",{})
    total=sc.get("puntuacion_total",0)
    score_data=[
        ["Precio/Mdo","Conserv.","Ubicacion","Rentabil.","Extras","Revalor.","TOTAL"],
        [str(sc.get("precio_mercado","?")),str(sc.get("estado_conservacion","?")),str(sc.get("ubicacion_calidad","?")),str(sc.get("rentabilidad","?")),str(sc.get("extras","?")),str(sc.get("potencial_revalorizacion","?")),f"{total}/10"]
    ]
    ts=Table(score_data,colWidths=[2.5*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm])
    ts.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
        ("BACKGROUND",(0,1),(-2,-1),colors.HexColor("#f5f0e8")),
        ("BACKGROUND",(-1,1),(-1,-1),GOLD),("FONTNAME",(-1,1),(-1,-1),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.3,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ]))
    h.append(ts)
    h.append(Spacer(1,12))
    h.append(HRFlowable(width="100%",thickness=0.8,color=NAVY,spaceAfter=5))
    h.append(Paragraph("Hero Valencia Real Estate | www.herovalenciarealestate.com | santiago@herovalenciarealestate.com | +34 666 980 970",s_ft))
    doc.build(h)
    buf.seek(0)
    return buf.read()

def enviar_email_confirmacion_cliente(datos):
    ec=datos.get("email","")
    if not ec: return
    nombre=datos.get("nombre","Cliente")
    es_premium=datos.get("servicio","estandar")=="premium"
    msg=MIMEMultipart()
    msg["From"]=EMAIL_FROM
    msg["To"]=ec
    msg["Subject"]="Hero Valencia Real Estate — Hemos recibido tu solicitud"
    if es_premium:
        detalle="<p>Has contratado el <strong>Servicio Premium</strong>. Nuestro equipo seleccionara personalmente las mejores propiedades para ti y coordinara las visitas presenciales con un asesor de Hero Valencia.</p><p>En menos de 48 horas te contactaremos para confirmar los detalles.</p>"
    else:
        detalle="<p>Has contratado el <strong>Estudio Personalizado</strong>. Nuestro equipo analizara el mercado y te enviara una seleccion de propiedades adaptadas exactamente a tu perfil.</p><p>En menos de 48 horas recibiras tu informe personalizado.</p>"
    cuerpo=f"""<html><body style="font-family:Arial,sans-serif;color:#252220;max-width:580px;margin:auto">
<div style="background:#16243E;padding:28px 32px;border-radius:12px 12px 0 0">
<h1 style="color:#C9A55A;font-size:1.3rem;margin:0">HERO VALENCIA REAL ESTATE</h1>
<p style="color:rgba(255,255,255,.6);font-size:.8rem;margin:4px 0 0">Tu experto inmobiliario en la Comunitat Valenciana</p>
</div>
<div style="background:#f9f6f1;padding:28px 32px;border-radius:0 0 12px 12px;border:1px solid #e8e2d8">
<h2 style="color:#16243E">Hola {nombre},</h2>
<p>Hemos recibido tu solicitud correctamente. Gracias por confiar en Hero Valencia Real Estate.</p>
{detalle}
<p>Si tienes cualquier pregunta puedes contactarnos directamente:</p>
<p><strong>WhatsApp:</strong> <a href="https://wa.me/34666980970">+34 666 980 970</a><br>
<strong>Email:</strong> <a href="mailto:santiago@herovalenciarealestate.com">santiago@herovalenciarealestate.com</a></p>
<p style="margin-top:20px;color:#9A9590;font-size:.8rem">Hero Valencia Real Estate | www.herovalenciarealestate.com</p>
</div></body></html>"""
    msg.attach(MIMEText(cuerpo,"html","utf-8"))
    with smtplib.SMTP(EMAIL_SMTP,EMAIL_PORT) as s:
        s.starttls();s.login(EMAIL_FROM,EMAIL_PASSWORD);s.sendmail(EMAIL_FROM,[ec],msg.as_string())
    log(f"Confirmacion enviada a: {ec}")

def enviar_pdfs_a_santiago(datos, propiedades, es_premium):
    nombre=datos.get("nombre","Cliente")
    servicio="PREMIUM" if es_premium else "ESTANDAR"
    fecha=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    num_total=len(propiedades)
    msg=MIMEMultipart()
    msg["From"]=EMAIL_FROM
    msg["To"]=EMAIL_TO
    msg["Subject"]=f"[HVRE {servicio}] {nombre} — {num_total} propiedades — {fecha}"
    resumen_props=""
    for p in propiedades:
        sc=p.get("scoring",{})
        resumen_props+=f"<tr><td style='padding:5px 8px'>{p.get('numero','')}</td><td style='padding:5px 8px'>{p.get('titulo','')[:50]}</td><td style='padding:5px 8px;font-weight:bold;color:#C9A55A;background:#16243E'>{p.get('precio','')}</td><td style='padding:5px 8px'>{p.get('portal','')}</td><td style='padding:5px 8px;text-align:center;font-weight:bold'>{sc.get('puntuacion_total','?')}/10</td><td style='padding:5px 8px'><a href='{p.get('link','')}' style='color:#B8845A'>Ver</a></td></tr>"
    cuerpo=f"""<html><body style="font-family:Arial,sans-serif;color:#252220;max-width:700px;margin:auto">
<div style="background:#16243E;padding:24px 28px;border-radius:10px 10px 0 0">
<h2 style="color:#C9A55A;margin:0">HVRE — Nuevo cliente {servicio}</h2>
<p style="color:rgba(255,255,255,.6);margin:4px 0 0;font-size:.85rem">{fecha}</p>
</div>
<div style="background:#f9f6f1;padding:24px 28px;border:1px solid #e8e2d8;border-radius:0 0 10px 10px">
<h3 style="color:#16243E">Datos del cliente</h3>
<p><strong>Nombre:</strong> {nombre}<br>
<strong>Email:</strong> {datos.get('email','')}<br>
<strong>Telefono:</strong> {datos.get('telefono','')}<br>
<strong>Provincia:</strong> {datos.get('provincia','')} — {datos.get('entorno','')}<br>
<strong>Presupuesto:</strong> {datos.get('presupuesto','')}<br>
<strong>Tipo compra:</strong> {datos.get('tipo_compra','')}<br>
<strong>Estilo de vida:</strong> {datos.get('estilo_vida','')}<br>
<strong>Idioma:</strong> {datos.get('idioma','')}<br>
<strong>Servicio:</strong> {servicio}</p>
<h3 style="color:#16243E;margin-top:18px">Resumen — {num_total} propiedades encontradas</h3>
<table style="width:100%;border-collapse:collapse;font-size:.82rem">
<tr style="background:#16243E;color:white">
<th style="padding:6px 8px;text-align:left">Num</th>
<th style="padding:6px 8px;text-align:left">Titulo</th>
<th style="padding:6px 8px;text-align:left">Precio</th>
<th style="padding:6px 8px;text-align:left">Portal</th>
<th style="padding:6px 8px">Score</th>
</tr>
{resumen_props}
</table>
<p style="margin-top:16px;color:#5E5A56;font-size:.8rem">Adjuntos: {num_total} PDFs individuales con ficha completa, analisis experto y scoring interno confidencial.</p>
</div></body></html>"""
    msg.attach(MIMEText(cuerpo,"html","utf-8"))
    for i,prop in enumerate(propiedades,1):
        try:
            pdf_bytes=generar_pdf_propiedad(prop,num_total,datos,es_premium)
            titulo_slug=slug(prop.get("titulo","propiedad"))
            fn=f"HVRE_{servicio}_{i:02d}_{titulo_slug}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
            part=MIMEBase("application","octet-stream")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition",f'attachment; filename="{fn}"')
            msg.attach(part)
            log(f"PDF {i}/{num_total}: {fn}")
        except Exception as e:
            log(f"Error PDF {i}: {e}")
    with smtplib.SMTP(EMAIL_SMTP,EMAIL_PORT) as s:
        s.starttls();s.login(EMAIL_FROM,EMAIL_PASSWORD);s.sendmail(EMAIL_FROM,[EMAIL_TO],msg.as_string())
    log(f"Email con {num_total} PDFs enviado a Santiago OK")

def pipeline(datos):
    try:
        servicio=datos.get("servicio","estandar").lower()
        es_premium=servicio=="premium"
        nombre=datos.get("nombre","?")
        log(f"Pipeline START {servicio}: {nombre}")
        enviar_email_confirmacion_cliente(datos)
        resultado=buscar_propiedades(datos)
        propiedades=resultado.get("propiedades",[])
        log(f"Propiedades encontradas: {len(propiedades)}")
        enviar_pdfs_a_santiago(datos,propiedades,es_premium)
        log(f"Pipeline OK: {nombre}")
    except Exception as e:
        log(f"ERROR pipeline: {e}")
        import traceback;traceback.print_exc()

@app.route("/")
def home(): return jsonify({"estado":"activo"})

@app.route("/estado")
def estado(): return jsonify({"estado":"activo","anthropic":"OK" if ANTHROPIC_API_KEY else "FALTA","email":"OK" if EMAIL_PASSWORD else "FALTA"})

@app.route("/nuevo-cliente",methods=["POST","OPTIONS"])
def nuevo_cliente():
    if request.method=="OPTIONS":
        r=app.make_default_options_response()
        r.headers.update({"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"Content-Type,X-API-Secret"})
        return r
    if request.headers.get("X-API-Secret","")!=API_SECRET:
        return jsonify({"error":"Unauthorized"}),401
    datos=request.get_json(force=True,silent=True) or {}
    threading.Thread(target=pipeline,args=(datos,),daemon=True).start()
    r=jsonify({"ok":True});r.headers["Access-Control-Allow-Origin"]="*";return r,200

@app.route("/webhook-stripe",methods=["POST"])
def webhook_stripe():
    try:
        import stripe
        event=stripe.Webhook.construct_event(request.data,request.headers.get("Stripe-Signature",""),os.environ.get("STRIPE_WEBHOOK_SECRET",""))
    except Exception as e:
        return jsonify({"error":str(e)}),400
    if event.get("type") in ("checkout.session.completed","payment_intent.succeeded"):
        obj=event["data"]["object"];meta=obj.get("metadata",{})
        amount=obj.get("amount_total",0)
        servicio="premium" if amount>=40000 else "estandar"
        datos={"nombre":meta.get("nombre",obj.get("customer_details",{}).get("name","Cliente")),"email":meta.get("email",obj.get("customer_details",{}).get("email","")),"provincia":meta.get("provincia","Alicante"),"entorno":meta.get("entorno","Costa"),"presupuesto":meta.get("presupuesto","300k-500k"),"tipo_compra":meta.get("tipo_compra",""),"estilo_vida":meta.get("estilo_vida",""),"idioma":meta.get("idioma","es"),"servicio":meta.get("servicio",servicio)}
        threading.Thread(target=pipeline,args=(datos,),daemon=True).start()
    return jsonify({"ok":True}),200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
