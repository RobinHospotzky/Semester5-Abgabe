import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from openpyxl import Workbook
from datetime import datetime, timedelta
import requests

@csrf_exempt

def vorstrafenLoeschung(request):
    vorstrafenPfad = "/var/www/django-project/se5project/templates/Vorstrafenregister.json"
    if request.method == "PUT":
        if not request.body:
            return HttpResponse("Empty request body")
        try:
            data = json.loads(request.body.decode('utf-8'))
            iban = data.get("iban", "keine IBAN vorhanden")
            with open(vorstrafenPfad, "r") as datei:
                vorstrafenRegister = json.load(datei)
            person_found = False
            for person in vorstrafenRegister:
                if person.get("iban") == iban:
                    person_found = True
                    for straftat in person.get("strafen", []):
                        if straftat["Status"] == "aktiv":
                            straftat["Status"] = "Kurs abgeschlossen"  # Change the status
                            break
                    break
            if not person_found:
                return HttpResponse(f"Person mit der IBAN {iban} hat keine Straftaten.")
            with open(vorstrafenPfad,"w") as datei:
                json.dump(vorstrafenRegister, datei,indent=4)
            
            return HttpResponse(f"PUT-Anfrage erhalten. Vorstrafe gelöscht")
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON data")

def vorstrafenBekommen(iban):
    vorstrafenPfad = "/var/www/django-project/se5project/templates/Vorstrafenregister.json"
    with open(vorstrafenPfad, "r") as datei:
        vorstrafenRegister = json.load(datei)
    records = []
    for eintrag in vorstrafenRegister:
        if eintrag["iban"] == iban:
            for strafe in eintrag["strafen"]:
                records.append(strafe)
    if records == []:
        return False
    return records

def vorstrafeAnPersonalamt(request):
    pass

@csrf_exempt

def vorstrafeErfassen(request):
    vorstrafenPfad = "/var/www/django-project/se5project/templates/Vorstrafenregister.json"
    if request.method == "POST":
        if not request.body:
            return HttpResponse("Empty request body")
        try:
            data = json.loads(request.body.decode('utf-8'))
            iban = data.get("iban", "keine IBAN vorhanden")
            vorstrafe = data.get("straf_id", "keine Straf ID vorhanden")
            with open(vorstrafenPfad, "r") as datei:
                vorstrafenRegister = json.load(datei)

            updated = False
            for eintrag in vorstrafenRegister:
                if eintrag["iban"] == iban:
                    eintrag["strafen"].append({"Vorstrafe": vorstrafe, "Status": "aktiv"})
                    updated = True
                    break

            if not updated:
                vorstrafenRegister.append({
                    "iban": iban,
                    "strafen": [{"Vorstrafe": vorstrafe, "Status": "aktiv"}]
                })
            with open(vorstrafenPfad, "w") as datei:
                json.dump(vorstrafenRegister, datei, indent=4)

 

            return HttpResponse("Vorstrafe erfolgreich erfasst", status=200)

        except:
            return HttpResponse("Invalid JSON ")
    return HttpResponse("Invalid JSON data")

@csrf_exempt
def vorstrafenAbfrage(request):
    if request.method == "GET":
        iban = request.GET.get("iban")
        if not iban:
            return HttpResponse("Keine IBAN vorhanden", status=400)
        einträge= vorstrafenBekommen(iban)
        if einträge == False:
            return HttpResponse(False)
        for strafe in einträge:
            if strafe["Status"] == "aktiv":
                return HttpResponse(True)
        return HttpResponse(False)

def videoabgabe(request):
    return render(request, 'abgabe1.html')

def vorstrafenAlsExcel(request):
    iban = request.COOKIES.get("iban")
    vorstrafenRegister =vorstrafenBekommen(iban)

    wb = Workbook()
    ws = wb.active
    ws.title = "Vorstrafen"
    ws.append(["IBAN", "Vorstrafe", "Status"])
    for straftat in vorstrafenRegister:
        vorstrafe = straftat["Vorstrafe"]
        status = straftat["Status"]
        ws.append([iban, vorstrafe, status])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename= "Vorstrafen.xlsx"'
    
    wb.save(response)
    return response

def get_favicon_status():
    faviconStatusPfad = "/var/www/django-project/se5project/templates/favicon_status.json"
    try:
        with open(faviconStatusPfad, "r") as datei:
            status = json.load(datei)
        return status.get("favicon", "standard")
    except FileNotFoundError:
        return "standard"

def reset_favicon_status(request):
    if request.method == "POST":
        iban = request.COOKIES.get("iban")
        token = request.COOKIES.get("token")
        faviconStatusPfad = "/var/www/django-project/se5project/templates/favicon_status.json"
        try:
            # Setze den Status auf 'standard'
            with open(faviconStatusPfad, "w") as datei:
                json.dump({"favicon": "standard"}, datei, indent=4)

            # Nach dem Zurücksetzen auf die Hauptseite weiterleiten
            response= redirect(redirect_target_page)
            response.set_cookie(iban)
            response.set_cookie(token)
            return response
        except Exception as e:
            return HttpResponse(f"Fehler beim Zurücksetzen des Favicons: {e}", status=500)
    return HttpResponse("Invalid request method", status=405)

def laufendeVorstrafenBekommen(iban): 
    base_url = "http://193.196.55.232:8888/straftaten_abrufen"
    param = {"iban": iban}
    response = requests.get(base_url, params=param)

    if response.status_code == 200:
        data = response.json()

        if not data:
            return False
        
        records = []
        aktuellesDatum = datetime.now()

        for Fall_id, Fall_details in data.items():
            datum = datetime.strptime(Fall_details[2], "%d/%m/%Y")  # Datum parsen
            status = Fall_details[4]

            if status == "offen" or (aktuellesDatum - datum).days <= 90 and status != "bezahlt": #Falls der Fall nicht offen oder länger als 90 Tage alt ist, wird er nicht übernommen
                record = {
                    "FallID": Fall_id,
                    "Straftat": Fall_details[0],
                    "IBAN": Fall_details[1],
                    "Datum": Fall_details[2],
                    "Schwere": Fall_details[3],
                    "Status": Fall_details[4],
                    "Einspruch": Fall_details[5] if Fall_details[5] else [],
                }
                records.append(record)
        return records
    else:
        return f"Error: Server kann nicht erreicht werden (status code: {response.status_code})"

@csrf_exempt
def vorstrafen_anzeigen(request):
    verificationURL = "http://193.196.52.227:8000/SE5/verify/" 
    token = request.COOKIES.get("token")
    iban = request.COOKIES.get("iban")
    
    if not token or not iban:  # Wenn Cookies nicht vorhanden sind, auf Query-Parameter prüfen
        token = request.GET.get("token")
        iban = request.GET.get("iban")
        if not token or not iban:  # Prüfen, ob Token und IBAN übergeben wurden
            queryString = "Es wurde kein Token oder keine IBAN gefunden!"
            return redirect(f"http://193.196.52.227:8000/SE5/start/?queryString={queryString}")
    try:
        response = requests.get(verificationURL, params={"iban" : iban, "token" : token})
        if response.status_code == 200:
            data = response.json()
            if data.get("result", False) == True:
                
                #iban = ibanbekommen()
                vorstrafen_data = laufendeVorstrafenBekommen(iban)
                alleVorstrafen = vorstrafenBekommen(iban)
                aktuellesDatum = datetime.now()
                faviconStatusPfad = "/var/www/django-project/se5project/templates/favicon_status.json"

                if vorstrafen_data == False and alleVorstrafen == False:
                    with open(faviconStatusPfad, "r") as datei:
                        entladen = json.load(datei)
                    favicon_status = entladen["favicon"]
                    return render(request, "vorstrafenAnzeigen.html", {"error": "Keine laufenden Vorstrafen gefunden.","favicon_status": favicon_status,})
                
                if vorstrafen_data == False:
                    vorstrafen_data = []
                if alleVorstrafen == False:
                    alleVorstrafen = []

                for record in vorstrafen_data:
                    try:
                        record_datum = datetime.strptime(record["Datum"], "%d/%m/%Y")
                                
                        if aktuellesDatum - record_datum <= timedelta(days=90) and record["Status"] == "offen":
                            with open(faviconStatusPfad, "w") as datei:
                                json.dump({"favicon": "updated"}, datei, indent=4)
                            break
                    except:
                        continue
                
                with open(faviconStatusPfad, "r") as datei:
                    entladen = json.load(datei)
                    favicon_status = entladen["favicon"]

                content = {
                    "iban":iban, 
                    "token":token,
                    "vorstrafen_data": vorstrafen_data,
                    "favicon_status": favicon_status,
                    "vorstrafen": alleVorstrafen,
                    }
                response = render(request, "vorstrafenAnzeigen.html", content) # HIER MUSS EUER TEMPLATE REIN BZW DIESER SCHRITT RETURN EUER TEMPLATE WIE GEWOHNT
                response.set_cookie("iban",iban) # Zum setzen des Cookies "iban" für eure Domain
                response.set_cookie("token",token) # Zum setzten des Cookies "token" für eure Domain
                return response
            else:
                queryString="Der Token konnte nicht verifiziert werden!"
                return redirect(f"http://193.196.52.227:8000/SE5/start/?queryString={queryString}")
        else:
            return HttpResponse("Keine Antwort vom Verifizierungsserver.")  # Wenn das kommt, bitte bei mir melden :)
    except requests.RequestException as e: 	# Hier wird falls eine andere Exception geworfen wird diese als String mit der Fehlermeldung zurückgegeben. Dient v.a. mir zum Debugging, also auch hier bei mir melden :)
        print("Netzwerkfehler:", e)

def redirect_target_page(request):
    verificationURL = "http://193.196.52.227:8000/SE5/verify/" 
    token = request.COOKIES.get("token")
    iban = request.COOKIES.get("iban")
    
    if not token or not iban:  # Wenn Cookies nicht vorhanden sind, auf Query-Parameter prüfen
        token = request.GET.get("token")
        iban = request.GET.get("iban")
        if not token or not iban:  # Prüfen, ob Token und IBAN übergeben wurden
            queryString = "Es wurde kein Token oder keine IBAN gefunden!"
            return redirect(f"http://193.196.52.227:8000/SE5/start/?queryString={queryString}")
    try:
        response = requests.get(verificationURL, params={"iban" : iban, "token" : token})
        if response.status_code == 200:
            data = response.json()
            if data.get("result", False) == True:
                
                vorstrafen_data = laufendeVorstrafenBekommen(iban)
                alleVorstrafen = vorstrafenBekommen(iban)
                faviconStatusPfad = "/var/www/django-project/se5project/templates/favicon_status.json"

                if vorstrafen_data == False and alleVorstrafen == False:
                    return render(request, "vorstrafenAnzeigen.html", {"error": "Keine Vorstrafen gefunden.","favicon_status": favicon_status,})
                if vorstrafen_data == False:
                    vorstrafen_data = None
                if alleVorstrafen == False:
                    alleVorstrafen = None
                with open(faviconStatusPfad, "r") as datei:
                    entladen = json.load(datei)
                    favicon_status = entladen["favicon"]

                content = {
                    "iban":iban, 
                    "token":token,
                    "vorstrafen_data": vorstrafen_data,
                    "favicon_status": favicon_status,
                    "vorstrafen": alleVorstrafen,
                    }
                response = render(request, "vorstrafenAnzeigen.html", content) # HIER MUSS EUER TEMPLATE REIN BZW DIESER SCHRITT RETURN EUER TEMPLATE WIE GEWOHNT
                response.set_cookie("iban",iban) # Zum setzen des Cookies "iban" für eure Domain
                response.set_cookie("token",token) # Zum setzten des Cookies "token" für eure Domain
                return response
            else:
                queryString="Der Token konnte nicht verifiziert werden!"
                return redirect(f"http://193.196.52.227:8000/SE5/start/?queryString={queryString}")
        else:
            return HttpResponse("Keine Antwort vom Verifizierungsserver.")  # Wenn das kommt, bitte bei mir melden :)
    except requests.RequestException as e: 	# Hier wird falls eine andere Exception geworfen wird diese als String mit der Fehlermeldung zurückgegeben. Dient v.a. mir zum Debugging, also auch hier bei mir melden :)
        print("Netzwerkfehler:", e)

def einspruch_einlegen(request):
    if request.method == "POST":
        vz = request.POST.get("strafe_id")
        grund = request.POST.get("reason")
        data={
            "vz": vz,
            "grund": grund
        }
        zielURL = "http://193.196.55.232:8888/einspruch_einlegen"

        response = requests.post(zielURL,params=data)
        return redirect(redirect_target_page)

def bezahlen(request):
    if request.method == "POST":
        zweck = request.POST.get("zweck")
        iban_sender = request.POST.get("iban")
        iban_empfaenger = "DE48123456780972733291"
        betrag = request.POST.get("betrag")
        url = "http://193.196.53.209/bank/transfer/"  # Bezahl-Schnittstellen-URL
        body = {
        "sender_iban": iban_sender,
        "receiver_iban": iban_empfaenger,
        "amount": float(betrag),
        "verwendungszweck": str(zweck)
        }
        headers = {'Content-Type':'application/json'}
        response = requests.post(url,json=body, headers=headers)
    return redirect(redirect_target_page)
