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
API_GET_PROPOSITIONS = '/Proposicoes.asmx/ListarProposicoes'
API_GET_PROPOSITION_BY_ID = 'Proposicoes.asmx/ObterProposicaoPorID'
API_GET_SPEECHES = '/sessoesreunioes.asmx/ListarDiscursosPlenario'

logging.basicConfig(filename=LOG_FILE, level=logging.WARNING)

# Get all congressmen information
try:
    cm = requests.get('http://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados')
except Exception:
    logging.warning('Could not GET data')

deputados = dict()
try:
    obj = untangle.parse(cm.content)
    for dep in obj.deputados.deputado:
        deputados[dep.nomeParlamentar.cdata] = dict()
        deputados[dep.nomeParlamentar.cdata]['nome'] = dep.nome.cdata
        deputados[dep.nomeParlamentar.cdata]['urlFoto'] = dep.urlFoto.cdata
        deputados[dep.nomeParlamentar.cdata]['uf'] = dep.uf.cdata
        deputados[dep.nomeParlamentar.cdata]['partido'] = dep.partido.cdata
        deputados[dep.nomeParlamentar.cdata]['fone'] = dep.fone.cdata
        deputados[dep.nomeParlamentar.cdata]['email'] = dep.email.cdata
except IndexError as e:
    logging.warning(e)

# Get all proposals for each congressman
for dep in deputados:
    try:
        # set sigla=PL for projetos de lei
        propositions = requests.get('http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoes?sigla=&numero=&ano=&datApresentacaoIni=18/07/2015&datApresentacaoFim=12/07/2016&parteNomeAutor=%s&idTipoAutor=&siglaPartidoAutor=%s&siglaUFAutor=%s&generoAutor=&codEstado=&codOrgaoEstado=&emTramitacao=' % (dep, deputados[dep]['partido'], deputados[dep]['uf']))
    except Exception:
        logging.warning('Could not GET data')
    try:
        obj = untangle.parse(propositions.content)
        for prop in obj.proposicoes.proposicao:
            deputados[dep]['proposicoes'] = dict()
            deputados[dep]['proposicoes'][prop.id.cdata] = dict()

            # Get proposal keywords and text
            try:
                detailed_prop = requests.get('http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterProposicaoPorID?idProp=%s' % (prop.id.cdata))
            except Exception:
                logging.warning('Could not GET data')
            try:
                obj2 = untangle.parse(detailed_prop.content)
                deputados[dep]['proposicoes'][prop.id.cdata]['key words'] = obj2.proposicao.Indexacao.cdata

            except IndexError as e:
                logging.warning(e)

    except IndexError as e:
        logging.warning("'%s'\n\tin:\n%s\n\tfor: %s" % (e, propositions.content, dep))

# Get all speeches for each congressman
for dep in deputados:
    try:
        speeches = requests.get('http://www.camara.leg.br/sitcamaraws/sessoesreunioes.asmx/ListarDiscursosPlenario?dataIni=18/07/2015&dataFim=12/07/2016&codigoSessao=&parteNomeParlamentar=%s&siglaPartido=%s&siglaUF=%s' % (dep, deputados[dep]['partido'], deputados[dep]['uf']))
    except Exception:
        logging.warning('Could not GET data')
    try:
        obj = untangle.parse(speeches.content)
        for session in obj.sessoesDiscursos.sessao:
            for phase in session.fasesSessao.faseSessao:
                for speech in phase.discursos.discurso:
                    deputados[dep]['discursos'] = []
                    deputados[dep]['discursos'].append(speech.txtIndexacao.cdata)

    except IndexError as e:
        logging.warning(e)

with open('data.json', 'w') as outfile:
    json.dumps(deputados, outfile)
