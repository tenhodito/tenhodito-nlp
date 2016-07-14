obtem todos os deputados
  http://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados

hierarquia xml:

deputados
  deputado
    nome
    nomeParlamentar (fazer busca e apresentar com este nome)
    urlFoto
    uf
    partido
    fone (queremos isto nos dados do deputado?)
    email (queremos isto nos dados do deputado?)

==========

obter todas as proposições do deputado:
  http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoes?parteNomeAutor=string&siglaPartidoAutor=string&siglaUFAutor=string

hierarquia xml:

proposicoes
  proposicao
    id

===========
obtem uma proposição
  http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterProposicaoPorID?idProp=<ID_DA_PROPOSICAO>

hierarquia xml:

proposicao
  Indexacao (extrair termos separados por vírgulas, ignorar case)
  Ementa (texto da proposicao)

===========
===========

Alguns deputados não tem dados em dado periodo, o que fazer?

=====
calcular coerencia:
  obter bag-of-words para discursos
  obter bag-of-words para PLs
  transformar bag of words em vetores
  obter cosseno entre vetores
=====
discursos podem ser obtidos para cada 360 dias. Obter várias vezes para pegar um período maior? ex: 2015 até hoje.

