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
Busca en TODOS estos portales inmobiliarios: Idealista, Fotocasa, Kyero, Yaencontre, ThinkSpain, Rightmove Spain, A Place in the Sun, Habitaclia, Pisos.com, Milanuncios, Spainhouses, Properstar, Resales Online, Green-acres, Viva Estates, y agencias inmobiliarias locales de la zona solicitada. Busca exactamente 15 propiedades reales disponibles ahora mismo repartidas entre los distintos portales.
Para cada propiedad necesito datos reales y detallados. Responde SOLO con JSON sin texto adicional:
{{
  "propiedades": [
    {{
      "numero": 1,
      "ref": "REF-001",
      "titulo": "titulo real de la propiedad",
