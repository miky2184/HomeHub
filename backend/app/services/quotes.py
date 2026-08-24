"""Frase del giorno per la Home. Verificato: non esiste una API italiana
gratuita e affidabile per questo (a differenza del santo del giorno) — lista
curata di proverbi italiani (dominio pubblico, nessun problema di diritti),
con rotazione deterministica per giorno dell'anno: stessa frase tutto il
giorno, cambia da sola a mezzanotte, nessuna dipendenza da servizi esterni."""

from datetime import date

QUOTES_IT = [
    "Chi va piano va sano e va lontano.",
    "Chi trova un amico trova un tesoro.",
    "Roma non fu fatta in un giorno.",
    "Non è tutto oro quel che luccica.",
    "Chi dorme non piglia pesci.",
    "L'unione fa la forza.",
    "Chi la dura la vince.",
    "Meglio tardi che mai.",
    "Chi semina raccoglie.",
    "Il tempo è galantuomo.",
    "Volere è potere.",
    "Chi ben comincia è a metà dell'opera.",
    "Non tutti i mali vengono per nuocere.",
    "L'appetito vien mangiando.",
    "Chi cerca trova.",
    "A caval donato non si guarda in bocca.",
    "Batti il ferro finché è caldo.",
    "Chi fa da sé fa per tre.",
    "Il buongiorno si vede dal mattino.",
    "Ogni promessa è debito.",
    "Impara l'arte e mettila da parte.",
    "Non si finisce mai di imparare.",
    "Un passo alla volta si va lontano.",
    "Le buone azioni non sono mai sprecate.",
    "Chi ha tempo non aspetti tempo.",
    "Sbagliando si impara.",
    "Non c'è due senza tre.",
    "Chi ama crede.",
    "La pratica vale più della grammatica.",
    "Anno nuovo, vita nuova.",
    "Chi si loda si imbroda.",
    "Fatti maschi, parole femmine.",
    "Ride bene chi ride ultimo.",
    "Tra il dire e il fare c'è di mezzo il mare.",
    "Chi si accontenta gode.",
    "Il mondo è fatto a scale, chi le scende e chi le sale.",
]


def quote_of_day(day: date) -> str:
    return QUOTES_IT[day.timetuple().tm_yday % len(QUOTES_IT)]
