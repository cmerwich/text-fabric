# Text-Fabric kernel

## About

??? abstract "TF kernel"
    Text-Fabric can be used as a service.
    The full API of Text-Fabric needs a lot of memory, which makes it unusably for
    rapid successions of loading and unloading, like when used in a web server context.

    However, you can start TF as a service process, after which many clients can connect to it,
    all looking at the same (read-only) data. We call this a **TF kernel**.

    The API that the TF kernel offers is limited, it is primarily template search that is offered.
    see *Kernel API* below.

    The code in
    [kernel]({{tfghb}}/{{c_kernel}})
    explains how it works.

### Start

??? abstract "Run"
    You can run the TF kernel as follows:

    ```sh
    python3 -m tf.server.kernel ddd
    ```

    where `ddd` is one of the [supported apps](../About/Corpora.md)

    ??? example
        See the
        [start-up script]({{tfghb}}/{{c_start}})
        of the text-fabric browser.

### Connect

??? abstract "Connect"
    The TF kernel can be connected by an other Python program as follows:

    ```python
    from tf.server.kernel import makeTfConnection
    TF = makeTfConnection(host, port)
    api = TF.connect()
    ```

    After this, `api` can be used to obtain information from the TF kernel.

    ??? example
        See the
        [web server]({{tfghb}}/{{c_web}})
        of the text-fabric browser.

## Kernel API

??? abstract "About"
    The API of the TF kernel is created
    by the function `makeTfKernel` in the 
    [kernel]({{tfghb}}/{{c_kernel}})
    module of the server subpackage.

    It returns a class `TfKernel` with a number
    of exposed methods that can be called by other programs.

    For the machinery of interprocess communication we rely on the
    [rpyc]({{rpyc}}) module.
    See especially the docs on
    [services]({{rpycdocservices}}).

    ??? caution "Shadow objects"
        The way rpyc works in the case of data transmission has a pitfall.
        When a service returns a Python object to the client, it
        does not return the object itself, but only a shadow object
        so called *netref* objects. This strategy is called
        [boxing]({{rpycdocboxing}}).
        To the client the shadow object looks like the real thing,
        but when the client needs to access members, they will be fetched
        on the fly.

        This is a performance problem when the service sends a big list or dict,
        and the client iterates over all its items. Each item will be fetched in
        a separate interprocess call, which causes an enormous overhead.

        Boxing only happens for mutable objects. And here lies the work-around:

        The service must send big chunks of data as immutable objects,
        such as tuples. They are sent within a single interprocess call,
        and fly swiftly through the connecting pipe. 

??? abstract "monitor()"
    A utility function that spits out some information from the kernel
    to the outside work. 
    At this moment it is only used for debugging, but later
    it can be useful to monitor the kernel or manage it
    while it remains running.

??? abstract "header()"
    Calls the `header()` method of the app,
    which fetches all the stuff to create a header
    on the page with links to data and documentation of the
    data source.

??? abstract "provenance()"
    Calls the `provenance()` method of the app,
    which fetches provenance metadata to be shown
    on exported pages.

??? abstract "setNames()"
    Returns the names of sets that have been provided
    as custom sets to the kernel by means of the
    [`--sets=`]() command line argument with which the kernel
    was started.

    A web server kan use this informatiomn to write out provernance
    info.

??? abstract "css()"
    Calls the `loadCSS()` method of the app,
    which delivers the CSS code to be inserted
    on the browser page.

??? abstract "condenseTypes()"
    Fetches several things from the app and the 
    generic TF api:

    * `condenseType`:
      the default node type that acts
      as a container for representing query results;
      for Bhsa it is `verse`, for Uruk it is `tablet`;
    * `exampleSection`: an example for the help text
      for this data source;
    * `levels`: information about the node types in this
      data source.

??? abstract "passage()"
    Asks the kernel for passages (chunks of material corresponding
    to sections of level 1 (chapters).

    The material will be displayed as a sequence of plain
    representations of the sec2s, which can be expanded to pretty
    displays when the user chooses to do so.

    Parameters:

    ??? note "sec0"
        The level 0 section (book) in which the passage occurs

    ??? note "sec1"
        The level 1 section (chapter) to fetch

    ??? note "sec2=None"
        The level 2 section (verse) that should get focus

    ??? note "opened"
        The set of items that are currently expanded into pretty display

    ??? note "features"
        The features that should be displayed in pretty displays when expanding
        a plain representation of a sec2 into a pretty display

    ??? note "query"
        The query whose results should be highlighted in the passage display.

    ??? note "getx"
        If given, only a single sec2 (verse) will be fetched, but in pretty
        display.
        `getx` is the identifier (section label, verse number) of the item/

    ??? note "\*\*options"
        Additional, optional display options

??? abstract "table()"
    Fetches material corresponding to a list of sections or tuples of nodes.

    Parameters:

    ??? note "kind"
        Either `sections` or `tuples`: whether to find section material or tuple
        material;

    ??? note "task"
        The list of things (sections or tuples) to retrieve the material for;
        Typically coming from the *section pad* / *node pad* in the browser.

    ??? note "opened=set()"
        As in `passage()`

    ??? note "features"
        As in `passage()`

    ??? note "getx"
        As in `passage()`

    ??? note "\*\*options"
        As in `passage()`

??? abstract "search()"
    The work horse of this API.
    Executes a TF search template, retrieves
    formatted results, retrieves 
    formatted results for additional nodes and
    sections.

    Parameters:

    ??? note "query"
        Search template to be executed.
        Typically coming
        from the *search pad* in the browser.

    ??? note "batch"
        The number of table rows to show on one page
        in the browser.

    ??? note "position=1"
        The position that is central in the browser.
        The navigation links take this position
        as the focus point, and enable the user
        to navigate to neighbouring results, in ever bigger
        strides.

    ??? note "opened=set()"
        Which results have been expanded and need extended results.
        Normally, only the information to provide a *plain*
        representation of a result is being fetched,
        but for the opened ones information is gathered for
        pretty displays.

    ??? note "getx"
        If given, only a single result will be fetched, but in pretty
        display.
        `getx` is the sequence number of the result.

    ??? note "condensed"
        Whether or not the results should be *condensed*.
        Normally, results come as tuples of nodes, and each
        tuple is shown in a corresponding table row in
        plain or pretty display.

        But you can also *condense* results in container
        objects. All tuples will be inspected, and the nodes
        of each tuple will be gathered in containers,
        and these containers will be displayed in table rows.
        What is lost is the notion of an individual result,
        and what is gained is a better overview of where
        the parts of the results are.

    ??? note "condenseType"
        When condensing results, you can choose the node type
        that acts as container.

        ??? caution "Nodes get suppressed"
            Nodes in result tuples that have a type
            that is bigger than the condenseType, will
            be skipped.
            E.g. if you have chapter nodes in your results,
            but you condense to verses, the chapter nodes will 
            not show up.
            But if you condense to books, they will show up.

    ??? note "withNodes=False"
        Whether to include the node numbers into the formatted
        results.

    ??? note "linked=1"
        Which column in the results should be hyperlinked to
        online representations closest to the objects
        in that column.

        Counting columns starts at 1.

    ??? note "**options**"
        Additional keyword arguments are passed
        as options to the underlying API.

        For example, the Uruk API accepts `linenumbers`
        and `lineart`, which will ask to include line numbers
        and lineart in the formatted results.
        
??? abstract "csvs()"
    This is an other workhorse.
    It also asks for the things `search()` is asking
    for, but it does not want formatted results.
    It will get tabular data of result
    nodes, one for the *sections*, one for the *node tuples*,
    and one for the *search results*.

    For every node that occurs in this tabular data,
    features will be looked up.
    All loaded features will be looked up for those nodes.
    The result is a big table of nodes and feature values.

    The parameters are *query*, *tuples*, *sections*,
    *condensed*, *condenseType* and have the same meaning as
    in `search()` above.
