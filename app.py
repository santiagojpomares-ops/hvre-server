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
def buscar_estandar(datos):
    import anthropic
    IDIOMAS={"en":"English","fr":"Francais","de":"Deutsch","nl":"Nederlands","es":"Espanol"}
    lang=IDIOMAS.get(datos.get("idioma","es"),"Espanol")
    nom=datos.get("nombre","Cliente");prov=datos.get("provincia","Alicante")
    ent=datos.get("entorno","Costa");bud=datos.get("presupuesto","300k-500k")
    prompt=f"Eres experto inmobiliario Hero Valencia. Cliente:{nom} {prov} {ent} {bud}. Busca Idealista Fotocasa Kyero 15 propiedades reales. JSON: {{propiedades:[{{numero:1,titulo,ubicacion,precio,m2,dormitorios,descripcion,link,portal,puntuacion}}],resumen:'80 palabras {lang}'}}"
    client=anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=4000,tools=[{"type":"web_search_20250305","name":"web_search"}],messages=[{"role":"user","content":prompt}])
    texto="".join(b.text for b in resp.content if hasattr(b,"text")).strip()
    m=re.search(r'{[\s\S]*}',texto)
    if not m: raise ValueError("Sin JSON")
    return json.loads(m.group())
def buscar_premium(datos):
    import anthropic
    IDIOMAS={"en":"English","fr":"Francais","de":"Deutsch","nl":"Nederlands","es":"Espanol"}
    lang=IDIOMAS.get(datos.get("idioma","es"),"Espanol")
    nom=datos.get("nombre","Cliente");prov=datos.get("provincia","Alicante")
    ent=datos.get("entorno","Costa");bud=datos.get("presupuesto","300k-500k")
    prompt=f"Eres experto inmobiliario senior Hero Valencia. Servicio PREMIUM cliente:{nom} {prov} {ent} {bud}. Busca Idealista Fotocasa Kyero 10 propiedades reales para visita presencial. Scoring 0-10 por: precio_mercado,estado_conservacion,ubicacion_calidad,rentabilidad,extras,potencial_revalorizacion. JSON: {{propiedades:[{{numero:1,titulo,ubicacion,precio,m2,dormitorios,descripcion,link,portal,scoring:{{precio_mercado:8,estado_conservacion:7,ubicacion_calidad:9,rentabilidad:6,extras:5,potencial_revalorizacion:8,puntuacion_total:7.2}},recomendacion_visita:'30 palabras {lang}'}}],resumen:'100 palabras {lang}',conclusion_premium:'50 palabras {lang}'}}"
    client=anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=6000,tools=[{"type":"web_search_20250305","name":"web_search"}],messages=[{"role":"user","content":prompt}])
    texto="".join(b.text for b in resp.content if hasattr(b,"text")).strip()
    m=re.search(r'{[\s\S]*}',texto)
    if not m: raise ValueError("Sin JSON premium")
    return json.loads(m.group())
def generar_pdf_estandar(datos,ia):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,HRFlowable,KeepTogether
    from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
    buf=io.BytesIO()
    NAVY=colors.HexColor("#16243E");GOLD=colors.HexColor("#C9A55A");CLAY=colors.HexColor("#B8845A");GRAY=colors.HexColor("#5E5A56")
    def S(n,**k): return ParagraphStyle(n,**k)
    s1=S("T",fontName="Helvetica-Bold",fontSize=20,textColor=NAVY,alignment=TA_CENTER,spaceAfter=4)
    s2=S("Su",fontName="Helvetica",fontSize=11,textColor=GOLD,alignment=TA_CENTER,spaceAfter=14)
    s3=S("Se",fontName="Helvetica-Bold",fontSize=11,textColor=NAVY,spaceBefore=10,spaceAfter=5)
    s4=S("Bo",fontName="Helvetica",fontSize=9.5,textColor=GRAY,alignment=TA_JUSTIFY,leading=14,spaceAfter=5)
    s5=S("Pt",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY,spaceAfter=2)
    s6=S("Pi",fontName="Helvetica",fontSize=8.5,textColor=GRAY,spaceAfter=2)
    s7=S("Pd",fontName="Helvetica-Oblique",fontSize=8.5,textColor=GRAY,alignment=TA_JUSTIFY,leading=12,spaceAfter=3)
    s8=S("Lk",fontName="Helvetica",fontSize=8,textColor=CLAY,spaceAfter=5)
    s9=S("Ft",fontName="Helvetica",fontSize=7.5,textColor=GRAY,alignment=TA_CENTER)
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2.5*cm,bottomMargin=2*cm)
    h=[]
    nombre=datos.get("nombre","Cliente");fecha=datetime.datetime.now().strftime("%d/%m/%Y")
    h.append(Paragraph("HERO VALENCIA REAL ESTATE",s1))
    h.append(Paragraph("Informe Personalizado de Propiedades",s2))
    h.append(HRFlowable(width="100%",thickness=1.5,color=GOLD,spaceAfter=10))
    h.append(Paragraph(f"Cliente: {nombre} | Fecha: {fecha} | Provincia: {datos.get('provincia','')} | Entorno: {datos.get('entorno','')} | Presupuesto: {datos.get('presupuesto','')}",s4))
    h.append(HRFlowable(width="100%",thickness=0.5,color=GOLD,spaceAfter=5))
    h.append(Paragraph("Resumen",s3))
    h.append(Paragraph(ia.get("resumen",""),s4));h.append(Spacer(1,6))
    h.append(HRFlowable(width="100%",thickness=0.5,color=GOLD,spaceAfter=5))
    h.append(Paragraph("15 propiedades seleccionadas",s3))
    for i,p in enumerate(ia.get("propiedades",[])[:15],1):
        b=[]
        b.append(Paragraph(f"{i:02d}. {p.get('titulo','')}",s5))
        b.append(Paragraph(f"{p.get('ubicacion','')} | {p.get('precio','')} | {p.get('m2','')} | {p.get('dormitorios','')} dorm | {p.get('puntuacion','')}/10 | {p.get('portal','')}",s6))
        b.append(Paragraph(p.get("descripcion",""),s7))
        url=p.get("link","")
        if url: b.append(Paragraph(f'<link href="{url}"><u>{url}</u></link>',s8))
        b.append(HRFlowable(width="100%",thickness=0.3,color=colors.HexColor("#e0d8cc"),spaceAfter=3))
        h.append(KeepTogether(b))
    h.append(Spacer(1,12))
    h.append(HRFlowable(width="100%",thickness=1,color=NAVY,spaceAfter=5))
    h.append(Paragraph("Hero Valencia Real Estate | www.herovalenciarealestate.com | santiago@herovalenciarealestate.com | +34 666 980 970",s9))
    doc.build(h);buf.seek(0);return buf.read()
def generar_pdf_premium(datos,ia):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,HRFlowable,KeepTogether,Table,TableStyle
    from reportlab.lib.enums import TA_CENTER,TA_JUSTIFY
    buf=io.BytesIO()
    NAVY=colors.HexColor("#16243E");GOLD=colors.HexColor("#C9A55A");CLAY=colors.HexColor("#B8845A");GRAY=colors.HexColor("#5E5A56");GREEN=colors.HexColor("#2E7D32")
    def S(n,**k): return ParagraphStyle(n,**k)
    s1=S("T",fontName="Helvetica-Bold",fontSize=22,textColor=NAVY,alignment=TA_CENTER,spaceAfter=2)
    s_prem=S("Pr",fontName="Helvetica-Bold",fontSize=13,textColor=GOLD,alignment=TA_CENTER,spaceAfter=14)
    s3=S("Se",fontName="Helvetica-Bold",fontSize=11,textColor=NAVY,spaceBefore=10,spaceAfter=5)
    s4=S("Bo",fontName="Helvetica",fontSize=9.5,textColor=GRAY,alignment=TA_JUSTIFY,leading=14,spaceAfter=5)
    s5=S("Pt",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY,spaceAfter=2)
    s6=S("Pi",fontName="Helvetica",fontSize=8.5,textColor=GRAY,spaceAfter=2)
    s7=S("Pd",fontName="Helvetica-Oblique",fontSize=8.5,textColor=GRAY,alignment=TA_JUSTIFY,leading=12,spaceAfter=3)
    s8=S("Lk",fontName="Helvetica",fontSize=8,textColor=CLAY,spaceAfter=5)
    s9=S("Ft",fontName="Helvetica",fontSize=7.5,textColor=GRAY,alignment=TA_CENTER)
    s_rec=S("Rc",fontName="Helvetica-Oblique",fontSize=9,textColor=GREEN,spaceAfter=5)
    s_concl=S("Co",fontName="Helvetica-Bold",fontSize=10,textColor=NAVY,alignment=TA_JUSTIFY,leading=15,spaceAfter=5)
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=2.5*cm,bottomMargin=2*cm)
    h=[]
    nombre=datos.get("nombre","Cliente");fecha=datetime.datetime.now().strftime("%d/%m/%Y")
    h.append(Paragraph("HERO VALENCIA REAL ESTATE",s1))
    h.append(Paragraph("INFORME PREMIUM - SERVICIO DE VISITAS",s_prem))
    h.append(HRFlowable(width="100%",thickness=2,color=GOLD,spaceAfter=10))
    h.append(Paragraph(f"Cliente: {nombre} | Fecha: {fecha} | Provincia: {datos.get('provincia','')} | Entorno: {datos.get('entorno','')} | Presupuesto: {datos.get('presupuesto','')}",s4))
    h.append(Paragraph("Servicio incluido: Visita presencial con asesor HVRE + Scoring por 6 variables",s6))
    h.append(HRFlowable(width="100%",thickness=0.5,color=GOLD,spaceAfter=5))
    h.append(Paragraph("Resumen del mercado",s3))
    h.append(Paragraph(ia.get("resumen",""),s4));h.append(Spacer(1,6))
    h.append(HRFlowable(width="100%",thickness=0.5,color=GOLD,spaceAfter=5))
    h.append(Paragraph("10 propiedades seleccionadas para visita",s3))
    for i,p in enumerate(ia.get("propiedades",[])[:10],1):
        b=[]
        sc=p.get("scoring",{})
        total=sc.get("puntuacion_total",0)
        b.append(Paragraph(f"{i:02d}. {p.get('titulo','')}",s5))
        b.append(Paragraph(f"{p.get('ubicacion','')} | {p.get('precio','')} | {p.get('m2','')} m2 | {p.get('dormitorios','')} dorm | {p.get('portal','')}",s6))
        b.append(Paragraph(p.get("descripcion",""),s7))
        score_data=[["SCORING","Precio/Mdo","Conserv.","Ubicacion","Rentabil.","Extras","Revalor.","TOTAL"],["Nota",str(sc.get("precio_mercado","?")),str(sc.get("estado_conservacion","?")),str(sc.get("ubicacion_calidad","?")),str(sc.get("rentabilidad","?")),str(sc.get("extras","?")),str(sc.get("potencial_revalorizacion","?")),f"{total}/10"]]
        t=Table(score_data,colWidths=[2.2*cm,2.2*cm,2.2*cm,2.2*cm,2.2*cm,2.2*cm,2.2*cm,2.2*cm])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7.5),("BACKGROUND",(0,1),(-2,-1),colors.HexColor("#f5f0e8")),("BACKGROUND",(-1,1),(-1,-1),GOLD),("FONTNAME",(-1,1),(-1,-1),"Helvetica-Bold"),("ALIGN",(0,0),(-1,-1),"CENTER"),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("GRID",(0,0),(-1,-1),0.3,GRAY)]))
        b.append(t);b.append(Spacer(1,4))
        rec=p.get("recomendacion_visita","")
        if rec: b.append(Paragraph(f"Recomendacion: {rec}",s_rec))
        url=p.get("link","")
        if url: b.append(Paragraph(f'<link href="{url}"><u>{url}</u></link>',s8))
        b.append(HRFlowable(width="100%",thickness=0.3,color=colors.HexColor("#e0d8cc"),spaceAfter=3))
        h.append(KeepTogether(b))
    h.append(Spacer(1,10))
    concl=ia.get("conclusion_premium","")
    if concl:
        h.append(HRFlowable(width="100%",thickness=1,color=GOLD,spaceAfter=8))
        h.append(Paragraph("Conclusion y Recomendacion Premium",s3))
        h.append(Paragraph(concl,s_concl))
    h.append(Spacer(1,10))
    h.append(HRFlowable(width="100%",thickness=1,color=NAVY,spaceAfter=5))
    h.append(Paragraph("Hero Valencia Real Estate | www.herovalenciarealestate.com | santiago@herovalenciarealestate.com | +34 666 980 970",s9))
    doc.build(h);buf.seek(0);return buf.read()
def enviar_email(datos,pdf):
    nombre=datos.get("nombre","Cliente");ec=datos.get("email","")
    servicio=datos.get("servicio","estandar")
    fecha=datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    tipo_label="PREMIUM" if servicio=="premium" else "Estandar"
    fn=f"HVRE_{tipo_label}_{slug(nombre)}_{datetime.datetime.now().strftime('%Y%m%d')}.pdf"
    msg=MIMEMultipart();msg["From"]=EMAIL_FROM;msg["Subject"]=f"[HVRE] Informe {tipo_label} - {nombre} {fecha}"
    props_num="10" if servicio=="premium" else "15"
    extras_premium="<p><strong>Servicio Premium incluye:</strong> Visita presencial con asesor HVRE + Scoring por 6 variables.</p>" if servicio=="premium" else ""
    cuerpo=f"<html><body><h2>HVRE - Informe {tipo_label}: {nombre}</h2><p>Cliente: {nombre}<br>Email: {ec}<br>Provincia: {datos.get('provincia','')}<br>Entorno: {datos.get('entorno','')}<br>Presupuesto: {datos.get('presupuesto','')}<br>Servicio: {tipo_label}<br>Generado: {fecha}</p>{extras_premium}<p>PDF adjunto con {props_num} propiedades seleccionadas.</p></body></html>"
    msg.attach(MIMEText(cuerpo,"html","utf-8"))
    part=MIMEBase("application","octet-stream");part.set_payload(pdf)
    encoders.encode_base64(part);part.add_header("Content-Disposition",f'attachment; filename="{fn}"')
    msg.attach(part)
    dest=[EMAIL_TO]
    if ec and ec!=EMAIL_TO: dest.append(ec)
    msg["To"]=", ".join(dest)
    with smtplib.SMTP(EMAIL_SMTP,EMAIL_PORT) as s:
        s.starttls();s.login(EMAIL_FROM,EMAIL_PASSWORD);s.sendmail(EMAIL_FROM,dest,msg.as_string())
    log(f"Email {tipo_label}: {', '.join(dest)}")
def pipeline(datos):
    try:
        servicio=datos.get("servicio","estandar").lower()
        log(f"Inicio {servicio}: {datos.get('nombre')}")
        if servicio=="premium":
            ia=buscar_premium(datos)
            pdf=generar_pdf_premium(datos,ia)
        else:
            ia=buscar_estandar(datos)
            pdf=generar_pdf_estandar(datos,ia)
        enviar_email(datos,pdf);log("OK")
    except Exception as e:
        log(f"ERROR: {e}");import traceback;traceback.print_exc()
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
