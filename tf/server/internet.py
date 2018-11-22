import os
import datetime
import time
import pickle

import markdown

import bottle
from bottle import (post, get, route, template, request, static_file, run)

from tf.core.helpers import console
from tf.parameters import NAME, VERSION, DOI_TEXT, DOI_URL, COMPOSE_URL
from tf.applib.apphelpers import RESULT
from tf.applib.appmake import (
    findAppConfig,
)
from tf.server.kernel import makeTfConnection
from tf.server.common import (
    getParam,
    getModules,
    getDebug,
    getDocker,
    getLocalClones,
    getAppDir,
    getValues,
    setValues,
    pageLinks,
    passageLinks,
    shapeMessages,
    shapeOptions,
    shapeCondense,
    shapeFormats,
)

TIMEOUT = 180

COMPOSE = 'Compose results example'

BATCH = 20
DEFAULT_NAME = 'DefaulT'

myDir = os.path.dirname(os.path.abspath(__file__))
appDir = None
localDir = None
bottle.TEMPLATE_PATH = [f'{myDir}/views']

dataSource = None
config = None

wildQueries = set()


def getStuff(lgc):
  global TF
  global appDir
  global localDir

  config = findAppConfig(dataSource)
  if config is None:
    return None

  TF = makeTfConnection(config.host, config.port['kernel'], TIMEOUT)
  appDir = getAppDir(myDir, dataSource)
  cfg = config.configure(lgc, version=config.VERSION)
  localDir = cfg['localDir']
  return config


def getProvenance(form, provenance, setNames):
  utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
  utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
  now = datetime.datetime.now().replace(microsecond=0,
                                        tzinfo=datetime.timezone(offset=utc_offset)).isoformat()
  job = form['jobName']
  author = form['author']

  dataHtml = ''
  dataMd = ''
  sep = ''

  for d in provenance:
    corpus = d['corpus']
    version = d['version']
    release = d['release']
    (live, liveUrl) = d['live']
    liveHtml = f'<a href="{liveUrl}">{live}</a>'
    liveMd = f'[{live}]({liveUrl})'
    (doiText, doiUrl) = d['doi']
    doiHtml = f'<a href="{doiUrl}">{doiText}</a>'
    doiMd = f'[{doiText}]({doiUrl})'
    dataHtml += f'''
    <div class="pline">
      <div class="pname">Data:</div>
      <div class="pval">{corpus}</div>
    </div>
    <div class="p2line">
      <div class="pname">version</div>
      <div class="pval">{version}</div>
    </div>
    <div class="p2line">
      <div class="pname">release</div>
      <div class="pval">{release}</div>
    </div>
    <div class="p2line">
      <div class="pname">download</div>
      <div class="pval">{liveHtml}</div>
    </div>
    <div class="p2line">
      <div class="pname">DOI</div>
      <div class="pval">{doiHtml}</div>
    </div>
'''
    dataMd += f'''{sep}Data source | {corpus}
version | {version}
release | {release}
download   | {liveMd}
DOI | {doiMd}'''
    sep = '\n'

  setHtml = ''
  setMd = ''

  if setNames:
    setNamesRep = ', '.join(setNames)
    setHtml += f'''
    <div class="psline">
      <div class="pname">Sets:</div>
      <div class="pval">{setNamesRep} (<b>not exported</b>)</div>
    </div>
'''
    setMd += f'''Sets | {setNamesRep} (**not exported**)'''

  tool = f'{NAME} {VERSION}'
  toolDoiHtml = f'<a href="{DOI_URL}">{DOI_TEXT}</a>'
  toolDoiMd = f'[{DOI_TEXT}]({DOI_URL})'

  composeHtml = f'<a href="{COMPOSE_URL}">{COMPOSE}</a>'
  composeMd = f'[{COMPOSE}]({COMPOSE_URL})'

  html = f'''
    <div class="pline">
      <div class="pname">Job:</div><div class="pval">{job}</div>
    </div>
    <div class="pline">
      <div class="pname">Author:</div><div class="pval">{author}</div>
    </div>
    <div class="pline">
      <div class="pname">Created:</div><div class="pval">{now}</div>
    </div>
    {dataHtml}
    {setHtml}
    <div class="pline">
      <div class="pname">Tool:</div>
      <div class="pval">{tool} {toolDoiHtml}</div>
    </div>
    <div class="pline">
      <div class="pname">See also:</div>
      <div class="pval">{composeHtml}</div>
    </div>
  '''

  md = f'''
meta | data
--- | ---
Job | {job}
Author | {author}
Created | {now}
{dataMd}
{setMd}
Tool | {tool} {toolDoiMd}
See also | {composeMd}
'''

  return (html, md)


def writeAbout(header, provenance, form):
  pass
  '''
  jobName = form['jobName']
  with open(f'about.md', 'w', encoding='utf8') as ph:
    ph.write(
  '''
  f'''
{header}

{provenance}

# {form["title"]}

## {form["author"]}

{form["description"]}

## Information requests:

### Sections

```
{form["sections"]}
```

### Nodes

```
{form["tuples"]}
```

### Search

```
{form["searchTemplate"]}
```
'''
  '''
    )
  '''


def writeCsvs(csvs, context, resultsX, form):
  pass
  '''
  jobName = form['jobName']
  if csvs is not None:
    for (csv, data) in csvs:
      with open(f'{csv}.tsv', 'w', encoding='utf8') as th:
        for tup in data:
          th.write('\t'.join(str(t) for t in tup) + '\n')
  for (name, data) in (
      ('CONTEXT', context),
      ('RESULTSX', resultsX),
  ):
    if data is not None:
      with open(f'{name}.tsv', 'w', encoding='utf_16_le') as th:
        th.write('﻿')  # utf8 bom mark, useful for opening file in Excel
        for tup in data:
          th.write('\t'.join('' if t is None else str(t) for t in tup) + '\n')
  '''


def getInt(x, default=1):
  if len(x) > 15:
    return default
  if not x.isdecimal():
    return default
  return int(x)


def getFormData():
  console(request.content_type)
  console(str(request.is_ajax))
  console(str(request.forms.get('sections')))
  console(repr(request.forms))
  console(str(request.body))
  form = {}
  form['searchTemplate'] = request.forms.searchTemplate.replace('\r', '')
  form['tuples'] = request.forms.tuples.replace('\r', '')
  form['sections'] = request.forms.sections.replace('\r', '')
  form['jobName'] = request.forms.jobName.strip()
  form['jobNameHidden'] = request.forms.jobNameHidden.strip()
  form['rename'] = request.forms.rename
  form['duplicate'] = request.forms.duplicate
  form['side'] = request.forms.side
  form['help'] = request.forms.help
  form['author'] = request.forms.author.strip()
  form['title'] = request.forms.title.strip()
  form['description'] = request.forms.description.replace('\r', '')
  form['withNodes'] = request.forms.withNodes
  form['condensed'] = request.forms.condensed
  form['condensetp'] = request.forms.condensetp
  form['textformat'] = request.forms.textformat
  form['export'] = request.forms.export
  form['expandAll'] = request.forms.expandAll
  form['linked'] = getInt(request.forms.linked, default=1)
  form['opened'] = request.forms.opened
  form['mode'] = request.forms.mode
  form['position'] = getInt(request.forms.position, default=1)
  form['batch'] = getInt(request.forms.batch, default=BATCH)
  form['sec0'] = request.forms.sec0
  form['sec1'] = request.forms.sec1
  form['sec2'] = request.forms.sec2
  setValues(config.options, request.forms, form)
  return form


@route('/server/static/<filepath:path>')
def serveStatic(filepath):
  return static_file(filepath, root=f'{myDir}/static')


@route('/data/static/<filepath:path>')
def serveData(filepath):
  return static_file(filepath, root=f'{appDir}/static')


@route('/local/<filepath:path>')
def serveLocal(filepath):
  return static_file(filepath, root=f'{localDir}')


def serveTable(kind):
  form = getFormData()
  textFormat = form['textformat'] or None
  task = form[kind]
  openedSet = {int(n) for n in form['opened'].split(',')} if form['opened'] else set()

  options = config.options
  values = getValues(options, form)

  kernelApi = TF.connect()

  messages = ''
  table = None
  if task:
    (
        table,
        messages,
    ) = kernelApi.table(
        kind,
        task,
        textFormat,
        opened=openedSet,
        withNodes=form['withNodes'],
        **values,
    )

    if messages:
      messages = shapeMessages(messages)
  return dict(
      table=table,
      messages=messages,
  )


@post('/sections')
@get('/sections')
def serveSections():
  return serveTable('sections')


@post('/tuples')
@get('/tuples')
def serveTuples():
  return serveTable('tuples')


@post('/query')
@get('/query')
def serveQuery():
  form = getFormData()
  query = form['searchTemplate']
  condenseType = form['condensetp'] or None
  resultKind = condenseType if form['condensed'] else RESULT
  textFormat = form['textformat'] or None
  openedSet = {int(n) for n in form['opened'].split(',')} if form['opened'] else set()

  options = config.options
  values = getValues(options, form)

  pages = ''

  kernelApi = TF.connect()

  if query:
    messages = ''
    table = None
    if query in wildQueries:
      messages = (
          f'Aborted because query is known to take longer than {TIMEOUT} second'
          + ('' if TIMEOUT == 1 else 's')
      )
    else:
      try:
        (
            table,
            messages,
            start,
            total,
        ) = kernelApi.search(
            query,
            form['condensed'],
            condenseType,
            textFormat,
            form['batch'],
            position=form['position'],
            opened=openedSet,
            withNodes=form['withNodes'],
            linked=form['linked'],
            **values,
        )
      except TimeoutError:
        messages = (
            f'Aborted because query takes longer than {TIMEOUT} second'
            + ('' if TIMEOUT == 1 else 's')
        )
        console(f'{query}\n{messages}', error=True)
        wildQueries.add(query)

    if table is not None:
      pages = pageLinks(total, form['position'])
    if messages:
      messages = shapeMessages(messages)
  else:
    table = f'no {resultKind}s'
    messages = ''
  return dict(
      pages=pages,
      table=table,
      messages=messages,
  )


@post('/passage')
@get('/passage')
def servePassage():
  form = getFormData()
  textFormat = form['textformat'] or None

  options = config.options
  values = getValues(options, form)

  passages = ''

  kernelApi = TF.connect()

  openedSet = set(form['opened'].split(',')) if form['opened'] else set()
  sec0 = form['sec0']
  sec1 = form['sec1']
  sec2 = form['sec2']
  (
      table,
      passages,
  ) = kernelApi.passage(
      sec0,
      sec1,
      textFormat,
      sec2=sec2,
      opened=openedSet,
      withNodes=form['withNodes'],
      **values,
  )
  passages = passageLinks(passages, sec0, sec1)
  return passages


@post('/export')
@get('/export')
def serveExport():
  sectionsData = serveSections()
  tuplesData = serveTuples()
  queryData = serveQuery()

  form = getFormData()
  query = form['searchTemplate']
  condenseType = form['condensetp'] or None
  textFormat = form['textformat'] or None

  kernelApi = TF.connect()
  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = getProvenance(form, provenance, setNames)

  descriptionMd = markdown.markdown(
      form['description'], extensions=[
          'markdown.extensions.tables',
          'markdown.extensions.fenced_code',
      ]
  )

  sectionsMessages = sectionsData['messages']
  sectionsTable = sectionsData['table']
  tuplesMessages = tuplesData['messages']
  tuplesTable = tuplesData['table']
  queryMessages = queryData['messages']
  queryTable = queryData['table']
  csvs = None
  context = None
  resultsX = None
  if not queryMessages and query not in wildQueries:
    try:
      (csvs, context, resultsX) = kernelApi.csvs(
          query,
          form['tuples'],
          form['sections'],
          form['condensed'],
          condenseType,
          textFormat,
      )
      csvs = pickle.loads(csvs)
      context = pickle.loads(context)
      resultsX = pickle.loads(resultsX)
    except TimeoutError:
      console(f'{query}\n{queryMessages} (in: export)', error=True)
      wildQueries.add(query)
  writeCsvs(csvs, context, resultsX, form)
  writeAbout(
      header,
      provenanceMd,
      form,
  )

  return template(
      'exportx',
      dataSource=dataSource,
      css=css,
      descriptionMd=descriptionMd,
      sectionsTable=(
          sectionsMessages if sectionsMessages or sectionsTable is None else sectionsTable
      ),
      tuplesTable=(
          tuplesMessages if tuplesMessages or tuplesTable is None else tuplesTable
      ),
      queryTable=(
          queryMessages if queryMessages or queryTable is None else queryTable
      ),
      colofon=f'{appLogo}{header}{tfLogo}',
      provenance=provenanceHtml,
      setNames=setNameHtml,
      **form,
  )


@post('/<anything:re:.*>')
@get('/<anything:re:.*>')
def serveAll(anything):
  form = getFormData()
  condensedAtt = ' checked ' if form['condensed'] else ''
  withNodesAtt = ' checked ' if form['withNodes'] else ''

  options = config.options
  values = getValues(options, form)

  pages = ''
  passages = ''

  kernelApi = TF.connect()

  (header, appLogo, tfLogo) = kernelApi.header()
  css = kernelApi.css()
  provenance = kernelApi.provenance()
  setNames = kernelApi.setNames()
  setNamesRep = ', '.join(setNames)
  setNameHtml = f'''
<p class="setnames">Sets:
<span class="setnames">{setNamesRep}</span>
</p>''' if setNames else ''
  (provenanceHtml, provenanceMd) = getProvenance(form, provenance, setNames)

  (
      defaultCondenseType,
      exampleSection,
      exampleSectionText,
      condenseTypes,
      defaultTextFormat,
      textFormats,
  ) = kernelApi.condenseTypes()
  condenseType = form['condensetp'] or defaultCondenseType
  condenseOpts = shapeCondense(condenseTypes, condenseType)
  textFormat = form['textformat'] or defaultTextFormat
  textFormatOpts = shapeFormats(textFormats, textFormat)

  return template(
      'indexx',
      dataSource=dataSource,
      css=css,
      header=f'{appLogo}{header}{tfLogo}',
      setNames=setNameHtml,
      options=shapeOptions(options, values),
      condensedAtt=condensedAtt,
      condenseOpts=condenseOpts,
      defaultCondenseType=defaultCondenseType,
      textFormatOpts=textFormatOpts,
      defaultTextFormat=defaultTextFormat,
      exampleSection=exampleSection,
      exampleSectionText=exampleSectionText,
      withNodesAtt=withNodesAtt,
      pages=pages,
      passages=passages,
      **form,
  )


if __name__ == "__main__":
  dataSource = getParam(interactive=True)
  modules = getModules()

  if dataSource is not None:
    modules = tuple(modules[6:].split(',')) if modules else ()
    lgc = getLocalClones()
    debug = getDebug()
    config = getStuff(lgc)
    onDocker = getDocker()
    console(f'onDocker={onDocker}')
    if config is not None:
      run(
          debug=debug,
          reloader=debug,
          host='0.0.0.0' if onDocker else config.host,
          port=config.port['internet'],
      )
