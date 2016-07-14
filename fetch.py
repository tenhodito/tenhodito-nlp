# -*- coding: utf-8 -*-

import requests
import untangle
import logging
import json

# fix untangle encoding problems
import sys
reload(sys)  # just to be sure
sys.setdefaultencoding('utf-8')

LOG_FILE = 'retrieve.log'

# API URI variables
CAMARA_BASE_URL = 'http://www.camara.leg.br'
API_ENTRY_POINT = '/SitCamaraWS'
API_GET_CONGRESSMEN = '/Deputados.asmx/ObterDeputados'
API_GET_PROPOSALS = '/Proposicoes.asmx/ListarProposicoes'
API_GET_PROPOSAL_BY_ID = '/Proposicoes.asmx/ObterProposicaoPorID'
API_GET_SPEECHES = '/sessoesreunioes.asmx/ListarDiscursosPlenario'

logging.basicConfig(filename=LOG_FILE, level=logging.WARNING)


def fetch_all_congressmen():
    """
    returns a XML with all congressmen data
    """
    try:
        response = requests.get(CAMARA_BASE_URL + API_ENTRY_POINT +
                                API_GET_CONGRESSMEN)
    except Exception:
        logging.warning('Could not GET data')
    return response.content


# set sigla=PL for projetos de lei
def fetch_cm_proposals(cm_name, cm_party, cm_state, start_date, end_date):
    payload = {'sigla': 'PL',
               'numero': '',
               'ano': '',
               'datApresentacaoIni': start_date,
               'datApresentacaoFim': end_date,
               'parteNomeAutor': cm_name,
               'idTipoAutor': '',
               'siglaPartidoAutor': cm_party,
               'siglaUFAutor': cm_state,
               'generoAutor': '',
               'codEstado': '',
               'codOrgaoEstado': '',
               'emTramitacao': ''}
    try:
        response = requests.get(CAMARA_BASE_URL + API_ENTRY_POINT +
                                API_GET_PROPOSALS, params=payload)
    except Exception:
        logging.warning('Could not GET data')
    return response.content


def fetch_proposal_by_id(proposal_id):
    payload = {'idProp': proposal_id}
    try:
        response = requests.get(CAMARA_BASE_URL + API_ENTRY_POINT +
                                API_GET_PROPOSAL_BY_ID, params=payload)
    except Exception:
        logging.warning('Could not GET data')
    return response.content


def fetch_cm_speeches(cm_name, cm_party, cm_state, start_date, end_date):
    payload = {'dataIni': start_date,
               'dataFim': end_date,
               'codigoSessao': '',
               'parteNomeParlamentar': cm_name,
               'siglaPartido': cm_party,
               'siglaUF': cm_state}
    try:
        response = requests.get(CAMARA_BASE_URL + API_ENTRY_POINT +
                                API_GET_SPEECHES, params=payload)
    except Exception:
        logging.warning('Could not GET data')
    return response.content

# Get all congressmen information

deputados = dict()
try:
    obj = untangle.parse(fetch_all_congressmen())
    for dep in obj.deputados.deputado:
        deputados[dep.nomeParlamentar.cdata] = dict()
        deputados[dep.nomeParlamentar.cdata]['nome'] = dep.nome.cdata
        deputados[dep.nomeParlamentar.cdata]['urlFoto'] = dep.urlFoto.cdata
        deputados[dep.nomeParlamentar.cdata]['uf'] = dep.uf.cdata
        deputados[dep.nomeParlamentar.cdata]['partido'] = dep.partido.cdata
        deputados[dep.nomeParlamentar.cdata]['fone'] = dep.fone.cdata
        deputados[dep.nomeParlamentar.cdata]['email'] = dep.email.cdata
        # FIXME: DEBUG
        #print dep.nomeParlamentar.cdata
except IndexError as e:
    logging.warning(e)

# Get all proposals for each congressman
for dep in deputados:
    try:
        # set sigla=PL for projetos de lei
        obj = untangle.parse(fetch_cm_proposals(dep, deputados[dep]['partido'], deputados[dep]['uf'], '05/07/2016', '12/07/2016'))
        for prop in obj.proposicoes.proposicao:
            deputados[dep]['proposicoes'] = dict()
            deputados[dep]['proposicoes'][prop.id.cdata] = dict()

            # Get proposal keywords and text
            try:
                obj2 = untangle.parse(fetch_proposal_by_id(prop.id.cdata))
                deputados[dep]['proposicoes'][prop.id.cdata]['key words'] = obj2.proposicao.Indexacao.cdata
                # FIXME: DEBUG 2
                # print obj2.proposicao.Indexacao.cdata

            except IndexError as e:
                logging.warning(e)

    except Exception as e:
        logging.warning("'%s'\n\tfor: %s" % (e, dep))

# Get all speeches for each congressman
for dep in deputados:
    try:
        obj = untangle.parse(fetch_cm_speeches(dep, deputados[dep]['partido'], deputados[dep]['uf'], '05/07/2016', '12/07/2016'))
        for session in obj.sessoesDiscursos.sessao:
            for phase in session.fasesSessao.faseSessao:
                for speech in phase.discursos.discurso:
                    deputados[dep]['discursos'] = []
                    deputados[dep]['discursos'].append(speech.txtIndexacao.cdata)

    except Exception as e:
        logging.warning(e)

with open('data.json', 'w') as outfile:
    json.dump(deputados, outfile, ensure_ascii=False)
