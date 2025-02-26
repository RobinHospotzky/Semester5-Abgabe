from django.urls import path

from se4project import views as app_views
from se5project import views as se5_views
from hello import views as hello_views
urlpatterns = [
    path("empfangen/", app_views.empfangen),
    path("email/", app_views.send_email),
    path('buchung_erstellen/', app_views.buchung_erstellen, name="buchung_erstellen"),
    path('buchungsseite', app_views.buchungsseite, name='buchungsseite' ),
    path('anmeldung', app_views.anmeldung, name="anmeldung"),
    path('abmeldung', app_views.logout, name="abmeldung"),
    path('registrierung', app_views.registrierung, name="registrierung"),
    path('vorstrafenLoeschung', se5_views.vorstrafenLoeschung, name="vorstrafenLoeschung"),
    path('vorstrafeErfassen', se5_views.vorstrafeErfassen, name="vorstrafeErfassen"),
    path('vorstrafenAbfrage', se5_views.vorstrafenAbfrage, name="vorstrafenAbfrage"),
    path('rechtUndOrdnung/schnittstellen', se5_views.videoabgabe, name="videoabgabe"),
    path('metadaten', hello_views.metadaten, name="metadaten"),
    path('helloWorld', hello_views.helloWorld, name="helloWorld"),
    path('vorstrafenAlsExcel',se5_views.vorstrafenAlsExcel, name="vorstrafenAlsExcel"),
    path('vorstrafen_anzeigen',se5_views.vorstrafen_anzeigen, name="vorstrafen_anzeigen"),
    path('reset_favicon_status', se5_views.reset_favicon_status, name="reset_favicon_status"),
    path('redirect_target_page', se5_views.redirect_target_page, name= "redirect_target_page"),
    path('einspruch_einlegen', se5_views.einspruch_einlegen, name="einspruch_einlegen"),
    path('bezahlen', se5_views.bezahlen, name="bezahlen")
]