"""
Transaction type mappings for bank-specific transaction preprocessing.

This file contains mappings from bank-specific transaction identifiers
to standardized transaction type labels.

For Intesa: Maps operazione.lower() to transaction type label
For Allianz: Maps transaction_type.lower() (first part before dash) to transaction type label
For FinecoBank: Maps transaction_type.lower() (first part before dash) to transaction type label
"""

# Transaction type label constants
ALTRO = "Altro"
ADDEBITO_DIRETTO = "Addebito diretto"
ASSEGNO = "Assegno"
BANCOMAT_PAY = "BANCOMAT Pay"
BONIFICO_EFFETTUATO = "Bonifico effettuato"
BONIFICO_RICEVUTO = "Bonifico ricevuto"
CANONE_CC = "Canone CC"
CANONE_INVESTIMENTO = "Canone investimento"
CARTA_DI_CREDITO = "Carta di credito"
CARTA_PREPAGATA = "Carta prepagata"
COMMISSIONE_SU_BONIFICO_ADDEBITO_DIRETTO = "Commissione su bonifico/addebito diretto"
GIROCONTO = "Giroconto"
IMPORTO_INIZIALE_SU_CONTO = "Importo iniziale su conto"
IMPOSTA_DI_BOLLO = "Imposta di bollo"
TASSE_INVESTIMENTI = "Tasse investimenti"
INVESTIMENTO = "Investimento"
PAGAMENTO_CON_CARTA = "Pagamento con carta"
PAGAMENTO_F24 = "Pagamento F24"
PAGAMENTO_MAV = "Pagamento Mav"
PRELIEVO_CONTANTI = "Prelievo contanti"
PREMIO_POLIZZA_ASSICURATIVA = "Premio polizza assicurativa"
RICARICA_CARTA_PREPAGATA = "Ricarica Carta Prepagata"
STIPENDIO = "Stipendio"

# Intesa transaction type mappings
# Maps operazione.lower() to standardized transaction type
TRANSACTION_MAP_INTESA = {
    # Exact or substring matches
    "pagamento adue": ADDEBITO_DIRETTO,
    "addebito diretto": ADDEBITO_DIRETTO,
    "assegni": ASSEGNO,
    "assegni circolari emessi": ASSEGNO,
    "bancomat pay": BANCOMAT_PAY,
    "fast pay": BANCOMAT_PAY,
    "beu tramite internet banking": BONIFICO_EFFETTUATO,
    "bonifico disposto a favore di": BONIFICO_EFFETTUATO,
    "bonifico istantaneo da voi disposto a favore di": BONIFICO_EFFETTUATO,
    "disposizione di bonifico": BONIFICO_EFFETTUATO,    
    "accredito beu con contabile": BONIFICO_RICEVUTO,
    "accredito bonifico istantaneo": BONIFICO_RICEVUTO,
    "bonifico disposto da": BONIFICO_RICEVUTO,
    "bonifico istantaneo disposto da": BONIFICO_RICEVUTO,
    "canone": CANONE_INVESTIMENTO,
    "ritenute su titoli esteri": TASSE_INVESTIMENTI,
    "commiss": COMMISSIONE_SU_BONIFICO_ADDEBITO_DIRETTO,
    "costo bonifico istantaneo": COMMISSIONE_SU_BONIFICO_ADDEBITO_DIRETTO,
    "maggiorazione bonifico istantaneo": COMMISSIONE_SU_BONIFICO_ADDEBITO_DIRETTO,
    "giroconto": GIROCONTO,
    "saldo contabile iniziale": IMPORTO_INIZIALE_SU_CONTO,
    "imposta di bollo": IMPOSTA_DI_BOLLO,
    "investimento": INVESTIMENTO,
    "pagamento premio assicurativo": INVESTIMENTO,
    "carta n.": PAGAMENTO_CON_CARTA,  # This is checked in dettagli, but included here for reference
    "deleghe fisco": PAGAMENTO_F24,
    "pagamento": PAGAMENTO_F24,
    "pagamento delega f24": PAGAMENTO_F24,
    "pagamento mav": PAGAMENTO_MAV,
    "premio polizza": PREMIO_POLIZZA_ASSICURATIVA,
    "ricarica carta prepagata": RICARICA_CARTA_PREPAGATA,
    "stipendio": STIPENDIO,
}

# Allianz transaction type mappings
# Maps transaction_type.lower() (first part before dash in operazione) to standardized transaction type
TRANSACTION_MAP_ALLIANZ = {
    "addeb. diretto": ADDEBITO_DIRETTO,
    "pagam. diversi": ADDEBITO_DIRETTO,
    "ass. circolare": ASSEGNO,
    "disposizione": BONIFICO_EFFETTUATO,
    "bonif. v/fav.": BONIFICO_RICEVUTO,
    "st. add. generi": BONIFICO_RICEVUTO,
    "addebito canone": CANONE_CC,
    "addebito nexi": CARTA_DI_CREDITO,
    "cartasi": CARTA_DI_CREDITO,
    "imposta bollo": IMPOSTA_DI_BOLLO,
    "imposte/tasse": TASSE_INVESTIMENTI,
    "pagam. pos": PAGAMENTO_CON_CARTA,
    "delega unica": PAGAMENTO_F24,
    "bancomat": PRELIEVO_CONTANTI,
    "emolumenti": STIPENDIO,
}

# FinecoBank transaction type mappings
TRANSACTION_MAP_FINECO = {
    "pagamento visa debit": PAGAMENTO_CON_CARTA,
    "bancomat": PAGAMENTO_CON_CARTA,
    "visa debit": PAGAMENTO_CON_CARTA,
    "pagamento bancomat": PAGAMENTO_CON_CARTA,
    "giroconto": GIROCONTO,
    "sepa direct debit": ADDEBITO_DIRETTO,
    "stipendio": STIPENDIO,
    "bonifico ricevuto": BONIFICO_RICEVUTO,
    "bonifico effettuato": BONIFICO_EFFETTUATO
}

# Default transaction types
DEFAULT_TRANSACTION_TYPE_INTESA = ALTRO
DEFAULT_TRANSACTION_TYPE_ALLIANZ = ALTRO
DEFAULT_TRANSACTION_TYPE_FINECO = ALTRO
